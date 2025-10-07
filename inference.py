import os
import pandas as pd
import csv
import numpy as np
import re
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# from eiffel import EiffelClient
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.models.auto import tokenization_auto
from tqdm.contrib.concurrent import thread_map

from t1.tools.cache import (
    get_results_from_cache,
    save_to_cache,
    reset_cache,
    dump_entire_cache,
    dump_cache_query,
    get_cache_for_current_turn,
    get_cache,
    retrieve_ground_truth_cache,
)

# from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

# model = LLM(
#     "/home/jovyan/llm-experiments-no-cache/model_zoo/simplescaling_s1.1-32B",
#     tensor_parallel_size=8,
# )
# tok = AutoTokenizer.from_pretrained("/home/jovyan/llm-experiments-no-cache/model_zoo/simplescaling_s1.1-32B")

stop_token_ids = [0]


from t1.tools.filter_attractions import filter_attractions
from t1.tools.seek_information import seek_information
from t1.tools.filter_flights import filter_flights
from t1.tools.filter_hotels import filter_hotels
from t1.tools.filter_restaurants import filter_restaurants
from t1.tools.find_nearest import search_nearest
from t1.tools.search_attractions import search_attractions
from t1.tools.search_flights import search_flights
from t1.tools.adjust_date import adjust_date
from t1.tools.search_hotels import search_hotels
from t1.tools.search_restaurants import search_restaurants
from t1.tools.sort_results import sort_results
from t1.tools.utils.get_tool_configurations import configure_tools_definitions
from t1.planner.planner_code import (
    plan_generation,
    make_reasoning_prompt,
    get_batch_results,
)
from t1.evaluation.eval_metrics import (
    extract_tool_calls,
    count_tool_usage,
    calculate_tool_calling_metrics,
    calculate_tool_param_metrics,
)
import sacrebleu
from collections import Counter
from torchmetrics.text.bert import BERTScore


def get_eiffel_client(url="localhost:9002"):
    """Initialize and return an EiffelClient instance."""
    return EiffelClient(url=url)


def extract_code_from_generated_plan(plan: str) -> str:
    """Extract code from a generated plan."""
    if pd.isna(plan):
        return ""
    match = re.search(r"<CODE>(.*?)</CODE>", plan, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_reasoning_from_generated_plan(plan: str) -> str:
    """Extract reasoning from a generated plan."""
    if pd.isna(plan):
        return ""
    match = re.search(r"<REASONING>(.*?)</REASONING>", plan, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_actual_tool_calls(row: pd.Series) -> Tuple[Optional[List], Optional[Dict]]:
    """Extract actual tool calls from a row."""
    role, utterance = row["Filled_Template"].split(":", 1)
    if "assistant" in role:
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
    role, utterance = row["Filled_Template"].split(":", 1)
    if "assistant" in role:
        return None, None

    code = row["generated_code"]

    if code is None:
        return None, None
    else:
        extracted_tool_calls = extract_tool_calls(code)

    # planner generates print statement when no plans needed
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
    role, utterance = row["Filled_Template"].split(":", 1)
    if "assistant" in role:
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
    else:
        return None, None


def extract_seek_information_texts(tool_calls):
    result = []
    if tool_calls:
        for item in tool_calls:
            if "seek_information" in item and "no_key" in item["seek_information"]:
                value = item["seek_information"]
                entry = value["no_key"][0]
                if isinstance(entry, list) and len(entry) == 1:
                    entry = entry[0]
                result.append(entry)
        return result
    else:
        return None


def seek_info_evaluation_metrics(row):
    role, utterance = row["Filled_Template"].split(":", 1)
    if "assistant" in role:
        return None

    actual = extract_seek_information_texts(row["actual_tool_calls"])
    gen = extract_seek_information_texts(row["generated_tool_calls"])

    if actual and gen:
        scores = {}
        bleu = sacrebleu.corpus_bleu(gen, [actual])
        scores["SacreBLEU"] = round(bleu.score, 4)

        # metric = BERTScore(
        #     model_name_or_path="/home/jovyan/fsx-claim-p/tool-driven-development/roberta-large",
        #     verbose=False,
        #     return_hash=False,
        # )
        # bertscore_roberta = metric(gen, actual)
        # bertscore_roberta = {
        #     k: round(v.item(), 4) for k, v in bertscore_roberta.items()
        # }
        # scores["BERTScore_roberta"] = bertscore_roberta

        metric = BERTScore(
            model_name_or_path="/home/jovyan/fsx-claim-p/tool-driven-development/deberta-xlarge-mnli",
            verbose=False,
            return_hash=False,
        )
        bertscore_deberta = metric(gen, actual)
        bertscore_deberta = {
            k: round(v.item(), 4) for k, v in bertscore_deberta.items()
        }
        scores["BERTScore_deberta"] = bertscore_deberta
        return scores
    else:
        return None


def cache_summary_exact_match(row):
    role, utterance = row["Filled_Template"].split(":", 1)
    if "assistant" in role:
        return None
    actual = row["cache_query_history"]
    gen = row["entire_planner_cache_history"]

    if not actual and not gen:
        return 1
    if actual and gen and Counter(actual.values()) == Counter(gen.values()):
        return 1
    else:
        return 0


def get_evaluation_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add evaluation columns to a dataframe."""
    df[["actual_tool_calls", "actual_tool_counts"]] = df.apply(
        extract_actual_tool_calls, axis=1, result_type="expand"
    )
    # df[["generated_tool_calls", "generated_tool_counts"]] = df.apply(
    #     extract_generated_tool_calls, axis=1, result_type="expand"
    # )
    # df[["tool_calling_metrics", "tool_param_metrics"]] = df.apply(
    #     tool_call_evaluation_metrics, axis=1, result_type="expand"
    # )
    # #df["seek_info_metrics"] = df.apply(seek_info_evaluation_metrics, axis=1)
    # df["cache_summary_exact_match"] = df.apply(cache_summary_exact_match, axis=1)

    return df


def process_first_pass(data: pd.DataFrame) -> pd.DataFrame:
    """
    Process the first pass: add chat_history, cache history, and error columns.
    """
    new_column_values = []

    # Group by the 'ID' column
    for event_id, group in data.groupby("ID"):
        print(f"Processing conversation ID: {event_id}")

        chat_history = []
        reset_cache()

        for index, row in group.iterrows():
            current_turn_cache = get_cache_for_current_turn()
            current_cache_full_obj = (
                dump_entire_cache().copy()
            )  # Get the full cache object, make a copy

            # Append chat history
            if pd.isna(row["Filled_Template"]):
                continue

            role, utterance = row["Filled_Template"].split(":", 1)
            if "user" in role:
                role = "user"
            elif "assistant" in role:
                role = "assistant"
            chat_history.append({role: utterance})

            # Append cache history
            plan = row["Filled_Plan"]
            error = ""

            if not pd.isna(plan):
                error = "success"
                try:
                    exec(plan)
                except Exception as e:
                    error = str(e)

            row_dict = row.to_dict()
            row_dict["entire_cache_before_current_turn"] = current_cache_full_obj
            row_dict["chat_history"] = f"{chat_history}"
            row_dict["cache_query_history"] = (
                dump_cache_query()
            )  # After ground truth code execution, updated cache
            row_dict["error"] = f"{error}"
            row_dict["cache_query_history_current_turn"] = (
                current_turn_cache  # Cache just before execution of ground truth code
            )
            row_dict["cache_check"] = get_cache(current_cache_full_obj)
            row_dict["role"] = role

            new_column_values.append(row_dict)

        reset_cache()  # Reset cache after processing each conversation

    return pd.DataFrame(new_column_values)


def wrapper(kwargs):

    return get_batch_results(**kwargs)


def generate_planner_reasoning(df: pd.DataFrame, tokeniser_path):
    # sampling_params = SamplingParams(
    # max_tokens=32000,
    # min_tokens=0,
    # stop_token_ids=stop_token_ids,
    # skip_special_tokens=False,
    # temperature=0.0,
    # )
    user_rows = df["role"] == "user"
    user_contents = df.loc[
        user_rows, ["chat_history", "cache_query_history_current_turn"]
    ]
    user_indices = df[df["role"] == "user"].index.tolist()
    df["generated_plan"] = np.nan

    # Step 3: Define the prompt creation function
    def create_prompt(df2):
        prompts = []
        for index, row in df2.iterrows():
            prompts.append(
                make_reasoning_prompt(
                    row["chat_history"],
                    row["cache_query_history_current_turn"],
                    tokeniser_path=tokeniser_path,
                )
            )

        return prompts

    # Step 4: Generate prompts only for user rows
    prompts = create_prompt(user_contents)
    batch_size = 1
    all_params = []
    all_batch_indices = []
    for i in range(0, len(prompts), batch_size):
        generated_code = []
        batch_prompts = prompts[i : i + batch_size]
        batch_indices = user_indices[i : i + batch_size]
        all_params.append({"prompts": batch_prompts, "tokeniser_path": tokeniser_path})
        all_batch_indices.append(batch_indices)
        # code = get_batch_results(batch_prompts,tokeniser_path)
        # generated_code=[]
        # for i in code:
        #     generated_code.append(i['text_output'])
        # df.loc[batch_indices,"generated_plan"] = generated_code
    responses = thread_map(wrapper, all_params, max_workers=1)
    for i in range(len(responses)):
        code = []
        code_str = responses[i].output_text
        code.append(code_str)
        index = all_batch_indices[i]
        for idx, val in zip(index, code):
            df.loc[idx, "generated_plan"] = val

    return df


def process_second_pass(new_data: pd.DataFrame, tokeniser_path: str) -> pd.DataFrame:
    """
    Process the second pass: generate plans based on chat history and cache.
    """
    new_col = []

    # Group by the 'ID' column
    for event_id, group in new_data.groupby("ID"):
        print(f"Processing conversation ID: {event_id}")

        chat_history = []

        for index, row in group.iterrows():
            planner_cache_history = retrieve_ground_truth_cache(row).copy()
            planner_cache_curr_turn = get_cache(planner_cache_history)

            # Append chat history
            if pd.isna(row["Filled_Template"]):
                continue

            role, utterance = row["Filled_Template"].split(":", 1)
            chat_history.append({role: utterance})

            # Generate plan based on role
            if "assistant" in role:
                plan = ""
                code = ""
                reasoning = ""
            elif "user" in role:
                plan = plan_generation(
                    row["chat_history"],
                    planner_cache_curr_turn,
                    tokeniser_path=tokeniser_path,
                )
                code = extract_code_from_generated_plan(plan)
                reasoning = extract_reasoning_from_generated_plan(plan)
            else:
                print(f"Unknown role: {role}")
                plan = ""
                code = ""
                reasoning = ""

            # Execute the code if it exists
            error = "success"
            if code:
                try:
                    if "input" in code:
                        error = "generated code had input"
                        pass
                    else:
                        exec(code)
                except Exception as e:
                    error = str(e)

            row_dict = row.to_dict()
            row_dict["planner_cache_curr_turn"] = planner_cache_curr_turn
            row_dict["entire_planner_cache_history"] = get_cache(dump_entire_cache())
            row_dict["code_error"] = error
            row_dict["generated_code"] = code
            row_dict["generated_reasoning"] = reasoning

            new_col.append(row_dict)

    return pd.DataFrame(new_col)


def process_and_save_file(
    input_file: str, output_dir: str, planning_dir: str, tokeniser_path: str
) -> None:
    """
    Process a single CSV file and save the results.

    Args:
        input_file: Path to the input CSV file
        output_dir: Directory to save processed data
        planning_dir: Directory to save planning data
    """
    print(f"\nProcessing file: {input_file}")

    # Extract filename without extension
    filename = os.path.basename(input_file)
    base_filename = os.path.splitext(filename)[0]

    # Read the CSV file
    data = pd.read_csv(input_file, sep=",", quoting=csv.QUOTE_MINIMAL, dtype=str)

    # Process first pass
    new_data = process_first_pass(data)

    # # Process second pass
    # new_data2 = process_second_pass(new_data, tokeniser_path)

    # # Extract planning data
    # plan_data = new_data2[
    #     [
    #         "ID",
    #         "Filled_Template",
    #         "Filled_Plan",
    #         "generated_code",
    #         "generated_reasoning",
    #         "entire_planner_cache_history",
    #         "cache_query_history",
    #         "code_error",
    #     ]
    # ]

    # # Get evaluation columns
    # plan_data_new = get_evaluation_columns(plan_data)

    # new_data = new_data[
    #     [
    #         "ID",
    #         "Filled_Template",
    #         "Filled_Plan",
    #         "cache_query_history_current_turn",
    #     ]
    # ]
    # # Save processed data

    new_data2 = generate_planner_reasoning(new_data, tokeniser_path)
    output_file = os.path.join(output_dir, f"{base_filename}_original.csv")
    new_data2.to_csv(output_file, index=False)
    print(f"Saved reasoning prompt to: {output_file}")

    # output_file = os.path.join(output_dir, f"{base_filename}_original.csv")
    # new_data.to_csv(output_file, index=False)
    # print(f"Saved original data to: {output_file}")

    # output_file = os.path.join(output_dir, f"{base_filename}_processed.csv")
    # new_data2.to_csv(output_file, index=False)
    # print(f"Saved processed data to: {output_file}")

    # # Save planning data
    # planning_file = os.path.join(planning_dir, f"{base_filename}_planning.csv")
    # plan_data_new.to_csv(planning_file, index=False)
    # print(f"Saved planning data to: {planning_file}")


def main():
    """Main function to process all CSV files in a directory."""
    input_dir = os.getenv("INPUT_DIR")
    output_dir_root = "/workspace/outputs_geimini"
    planning_dir_root = output_dir_root
    tokeniser_path = (
        "/home/jovyan/llm-experiments-no-cache/model_zoo/simplescaling_s1.1-32B"
    )

    for domain_folder in os.listdir(input_dir):
        domain_path = os.path.join(input_dir, domain_folder)
        if not os.path.isdir(domain_path):
            print("No path")
            continue

        test_folder = os.path.join(domain_path, "test")
        if not os.path.isdir(test_folder):
            print("No test folder")
            continue

        # Get all CSV files in the input directory
        csv_files = [
            os.path.join(test_folder, f)
            for f in os.listdir(test_folder)
            if f.endswith(".csv") and os.path.isfile(os.path.join(test_folder, f))
        ]

        if not csv_files:
            print(f"No CSV files found in {input_dir}")
            return

        # Create output directories for this domain
        output_dir = os.path.join(output_dir_root, domain_folder, "test")
        planning_dir = os.path.join(planning_dir_root, domain_folder, "test")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(planning_dir, exist_ok=True)

        # Process each CSV file
        for csv_file in csv_files:
            process_and_save_file(csv_file, output_dir, planning_dir, tokeniser_path)

        print(f"All files in test folder processed successfully for {domain_path}.")


if __name__ == "__main__":
    main()
