import ast
import csv
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import sacrebleu
from tqdm.auto import tqdm

from t1.evaluation.eval_metrics import (
    calculate_tool_calling_metrics,
    calculate_tool_param_metrics,
    count_tool_usage,
    extract_tool_calls,
)


def extract_actual_tool_calls(row: pd.Series) -> Tuple[Optional[List], Optional[Dict]]:
    """Extract actual tool calls from a row."""
    if row["role"] != "user":
        return None, None
    code = row["Filled_Plan"]
    if pd.isna(code):
        return None, None
    extracted_tool_calls = extract_tool_calls(code)
    count_tool_calls = count_tool_usage(extracted_tool_calls)
    return extracted_tool_calls, count_tool_calls


def extract_generated_tool_calls(
    row: pd.Series,
) -> Tuple[Optional[List], Optional[Dict]]:
    """Extract generated tool calls from a row."""
    if row["role"] != "user":
        return None, None
    code = row["generated_code"]
    if not code or pd.isna(code):
        return None, None
    try:
        extracted_tool_calls = extract_tool_calls(code)
    except SyntaxError:
        print(f"SyntaxError: Could not parse generated code for ID {row.get('ID')}")
        return None, None
    if len(extracted_tool_calls) == 1 and "print" in extracted_tool_calls[0]:
        return None, None
    if len(extracted_tool_calls) > 1:
        extracted_tool_calls = [
            item for item in extracted_tool_calls if "print" not in item
        ]
    count_tool_calls = count_tool_usage(extracted_tool_calls)
    return extracted_tool_calls, count_tool_calls


def tool_call_evaluation_metrics(
    row: pd.Series,
) -> Tuple[Optional[Dict], Optional[Dict]]:
    if row["role"] != "user":
        return None, None
    actual_tool_calls = row["actual_tool_calls"]
    generated_tool_calls = row["generated_tool_calls"]
    if actual_tool_calls is not None and generated_tool_calls is not None:
        tool_calling_metrics = calculate_tool_calling_metrics(
            actual_tool_calls, generated_tool_calls
        )
        tool_param_metrics = calculate_tool_param_metrics(
            actual_tool_calls, generated_tool_calls
        )
        return tool_calling_metrics, tool_param_metrics
    return None, None


def find_non_executable_code(row: pd.Series) -> Optional[int]:
    if row["role"] != "user":
        return None
    actual_tool_calls = row["actual_tool_calls"]
    generated_tool_calls = row["generated_tool_calls"]
    if (
        actual_tool_calls
        and not generated_tool_calls
        and row["code_error"] == "success"
    ):
        return 1
    elif actual_tool_calls and row["code_error"] != "success":
        return 1
    return 0


def extract_seek_information_texts(tool_calls: Optional[List]) -> Optional[List[str]]:
    if not tool_calls:
        return None
    result = []
    for item in tool_calls:
        if "seek_information" in item and "no_key" in item["seek_information"]:
            entry = item["seek_information"]["no_key"][0]
            result.append(str(entry[0]) if isinstance(entry, list) else str(entry))
    return [" ".join(result)] if result else None


def seek_info_evaluation_metrics(row: pd.Series) -> Optional[Dict]:
    if row["role"] != "user":
        return None
    actual = extract_seek_information_texts(row["actual_tool_calls"])
    gen = extract_seek_information_texts(row["generated_tool_calls"])
    if actual and not gen:
        return {"SacreBLEU": 0.0}
    if actual and gen:
        bleu = sacrebleu.corpus_bleu(gen, [actual])
        return {"SacreBLEU": round(bleu.score, 4)}
    return None


def cache_summary_exact_match(row: pd.Series) -> Optional[int]:
    if row["role"] != "user":
        return None
    actual = row["cache_query_history"]
    gen = row["entire_planner_cache_history"]
    if not actual and not gen:
        return 1
    if actual and gen and Counter(actual.values()) == Counter(gen.values()):
        return 1
    return 0


def get_evaluation_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add evaluation columns to a dataframe."""
    df[["actual_tool_calls", "actual_tool_counts"]] = df.apply(
        extract_actual_tool_calls, axis=1, result_type="expand"
    )
    df[["generated_tool_calls", "generated_tool_counts"]] = df.apply(
        extract_generated_tool_calls, axis=1, result_type="expand"
    )
    df[["tool_calling_metrics", "tool_param_metrics"]] = df.apply(
        tool_call_evaluation_metrics, axis=1, result_type="expand"
    )
    df["seek_info_metrics"] = df.apply(seek_info_evaluation_metrics, axis=1)
    df["cache_summary_exact_match"] = df.apply(cache_summary_exact_match, axis=1)
    df["non_executable_code"] = df.apply(find_non_executable_code, axis=1)
    return df


def main():
    """Main function to process all CSV files in a directory."""
    input_dir_env = os.getenv("INPUT_DIR")
    output_dir_env = os.getenv("OUTPUT_DIR")
    input_dir = Path(input_dir_env)
    output_dir = Path(output_dir_env)
    output_dir.mkdir(parents=True, exist_ok=True)
    files_to_process = list(input_dir.rglob("*_planning.csv"))
    for file in tqdm(files_to_process, desc="Generating evaluation metrics"):
        print(f"Processing: {file}")
        df = pd.read_csv(file)
        dict_cols = ["cache_query_history", "entire_planner_cache_history"]
        for col in dict_cols:
            df[col] = df[col].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
        new_df = get_evaluation_columns(df)
        relative_path = file.relative_to(input_dir)
        output_subdir = output_dir / relative_path.parent
        output_subdir.mkdir(parents=True, exist_ok=True)
        output_file = output_subdir / (file.stem + "_eval.csv")
        new_df.to_csv(output_file, index=False)
    print(f"Evaluation metrics generated for all files in {input_dir}.")


if __name__ == "__main__":
    main()
