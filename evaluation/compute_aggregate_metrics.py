import argparse
import ast
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def parse_metrics(val: Any) -> Dict:
    if pd.isna(val):
        return {}
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return {}


def compute_avg(numbers: List[float]) -> float:
    numbers = [n for n in numbers if n is not None]
    return sum(numbers) / len(numbers) if numbers else 0.0


def compute_precision(tp: int, fp: int) -> float:
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def compute_recall(tp: int, fn: int) -> float:
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def compute_accuracy(tp: int, fp: int, fn: int) -> float:
    return tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0


def f1_score(tp: int, fp: int, fn: int) -> float:
    prec = compute_precision(tp, fp)
    rec = compute_recall(tp, fn)
    return 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0


def calculate_success_rate(df: pd.DataFrame) -> float:
    if "non_executable_code" not in df.columns:
        return None
    df["non_executable_code"] = pd.to_numeric(
        df["non_executable_code"], errors="coerce"
    )
    user_rows = df[df["role"] == "user"]["non_executable_code"].fillna(0)
    if user_rows.empty:
        return None
    non_exec_count = sum(user_rows)
    total = len(user_rows)
    return 1.0 - (non_exec_count / total)


def accumulate_metrics(df: pd.DataFrame, prefix: str = "") -> Dict[str, Any]:
    tp_calling, fp_calling, fn_calling = 0, 0, 0
    tp_param, fp_param, fn_param = 0, 0, 0
    seek_bleu = []

    cache_vals = df[df["role"] == "user"]["cache_summary_exact_match"].dropna().tolist()

    for val in df["tool_calling_metrics"].dropna():
        d = parse_metrics(val)
        tp_calling += d.get("tp", 0)
        fp_calling += d.get("fp", 0)
        fn_calling += d.get("fn", 0)
    for val in df["tool_param_metrics"].dropna():
        d = parse_metrics(val)
        tp_param += d.get("tp", 0)
        fp_param += d.get("fp", 0)
        fn_param += d.get("fn", 0)
    for val in df["seek_info_metrics"].dropna():
        d = parse_metrics(val)
        seek_bleu.append(d.get("SacreBLEU"))

    return {
        f"{prefix}cache_summary_exact_match_avg": compute_avg(cache_vals),
        f"{prefix}tool_calling_micro_precision": compute_precision(
            tp_calling, fp_calling
        ),
        f"{prefix}tool_calling_micro_recall": compute_recall(tp_calling, fn_calling),
        f"{prefix}tool_calling_micro_accuracy": compute_accuracy(
            tp_calling, fp_calling, fn_calling
        ),
        f"{prefix}tool_calling_micro_f1": f1_score(tp_calling, fp_calling, fn_calling),
        f"{prefix}tool_param_micro_precision": compute_precision(tp_param, fp_param),
        f"{prefix}tool_param_micro_recall": compute_recall(tp_param, fn_param),
        f"{prefix}tool_param_micro_accuracy": compute_accuracy(
            tp_param, fp_param, fn_param
        ),
        f"{prefix}tool_param_micro_f1": f1_score(tp_param, fp_param, fn_param),
        f"{prefix}seek_SacreBLEU_avg": compute_avg(seek_bleu),
    }


def aggregate_metrics(files: List[Path]) -> Dict[str, float]:
    success_rates = []
    all_dfs = [pd.read_csv(file) for file in files]
    for df in all_dfs:
        success_rate = calculate_success_rate(df)
        if success_rate is not None:
            success_rates.append(success_rate)
    full_df = pd.concat(all_dfs, ignore_index=True)
    exec_df = (
        full_df[full_df["non_executable_code"] != 1.0]
        if "non_executable_code" in full_df.columns
        else full_df
    ).fillna({"non_executable_code": 0})
    results = {"code_success_rate": compute_avg(success_rates)}
    results.update(accumulate_metrics(full_df))
    results.update(accumulate_metrics(exec_df, prefix="exec_only_"))
    return results


def process_domains(input_dir: Path) -> List[Dict[str, Any]]:
    results = []
    for domain_dir in sorted(input_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        test_dir = domain_dir / "test"
        if not test_dir.is_dir():
            continue
        files = list(test_dir.glob("*_eval.csv"))
        if not files:
            print(f"No '*_eval.csv' files found in {test_dir}. Skipping.")
            continue
        print(f"[+] Processing domain: {domain_dir.name}")
        metrics = aggregate_metrics(files)
        metrics["model"] = input_dir.name
        metrics["domain"] = domain_dir.name
        results.append(metrics)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate planning_eval metrics per domain."
    )
    parser.add_argument(
        "--input_dir", type=str, required=True, help="Path to model directory."
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default="domain_metrics_summary.csv",
        help="Output CSV filename.",
    )
    args = parser.parse_args()
    input_path = Path(args.input_dir)
    if not input_path.is_dir():
        raise ValueError(
            f"Input directory does not exist or is not a directory: {args.input_dir}"
        )
    domain_metrics = process_domains(input_path)
    if not domain_metrics:
        print("No valid domain data found.")
        return
    df = pd.DataFrame(domain_metrics)
    cols = ["model", "domain"] + [c for c in df.columns if c not in ["model", "domain"]]
    df = df[cols]
    df.to_csv(args.output_csv, index=False)
    print(f"\nMetrics saved to {args.output_csv}")


if __name__ == "__main__":
    main()
