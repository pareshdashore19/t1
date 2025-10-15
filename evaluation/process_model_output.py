import csv
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from t1.tools.adjust_date import adjust_date
from t1.tools.cache import (
    dump_cache_query,
    dump_entire_cache,
    get_cache,
    get_cache_for_current_turn,
    reset_cache,
    retrieve_ground_truth_cache,
)
from t1.tools.filter_attractions import filter_attractions
from t1.tools.filter_flights import filter_flights
from t1.tools.filter_hotels import filter_hotels
from t1.tools.filter_restaurants import filter_restaurants
from t1.tools.find_nearest import search_nearest
from t1.tools.search_attractions import search_attractions
from t1.tools.search_flights import search_flights
from t1.tools.search_hotels import search_hotels
from t1.tools.search_restaurants import search_restaurants
from t1.tools.find_nearest import search_nearest
from t1.tools.seek_information import seek_information
from t1.tools.adjust_date import adjust_date
from t1.tools.sort_results import sort_results
from t1.tools.cache import get_results_from_cache, save_to_cache
from t1.tools.utils.get_tool_configurations import configure_tools_definitions


def extract_code_from_generated_plan(plan: str) -> str:
    """Extract all code from a generated plan and return it as a single string."""
    if pd.isna(plan):
        return ""
    matches = re.findall(r"<CODE>(.*?)</CODE>", plan, re.DOTALL)
    return "\n".join([match.strip() for match in matches]) if matches else ""


def process_first_pass(data: pd.DataFrame) -> pd.DataFrame:
    """Adds chat history, cache history, and error columns by executing ground truth plans."""
    new_column_values = []
    for event_id, group in data.groupby("ID"):
        print(f"Processing Ground Truth for Conversation ID: {event_id}")
        chat_history = []
        reset_cache()
        for _, row in group.iterrows():
            current_cache_full_obj = dump_entire_cache().copy()
            if pd.isna(row["Filled_Template"]):
                continue
            role, utterance = row["Filled_Template"].split(":", 1)
            chat_history.append({role.strip(): utterance.strip()})
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
            row_dict["cache_query_history"] = dump_cache_query()
            row_dict["error"] = error
            row_dict["role"] = role.strip()
            new_column_values.append(row_dict)
        reset_cache()
    return pd.DataFrame(new_column_values)


def process_second_pass(new_data: pd.DataFrame) -> pd.DataFrame:
    """Executes the generated plans and records any errors."""
    new_col = []
    for event_id, group in new_data.groupby("ID"):
        print(f"Processing Generated Plan for Conversation ID: {event_id}")
        reset_cache()
        for _, row in group.iterrows():
            planner_cache_history = retrieve_ground_truth_cache(row).copy()
            code = ""
            if row["role"] == "user":
                plan = row.get("generated_plan", "")
                code = extract_code_from_generated_plan(plan)
            error = "success"
            if code:
                try:
                    exec(code)
                except Exception as e:
                    error = str(e)
            row_dict = row.to_dict()
            row_dict["entire_planner_cache_history"] = get_cache(dump_entire_cache())
            row_dict["code_error"] = error
            row_dict["generated_code"] = code
            new_col.append(row_dict)
    return pd.DataFrame(new_col)


def main():
    """Main function to process all CSV files in a directory."""
    input_dir = os.getenv("INPUT_DIR")
    output_dir_root = os.getenv("OUTPUT_DIR")
    for domain_folder in os.listdir(input_dir):
        domain_path = os.path.join(input_dir, domain_folder)
        if not os.path.isdir(domain_path):
            continue
        test_folder = os.path.join(domain_path, "test")
        if not os.path.isdir(test_folder):
            continue
        csv_files = [f for f in os.listdir(test_folder) if f.endswith(".csv")]
        if not csv_files:
            print(f"No CSV files found in {test_folder}")
            continue
        output_dir = os.path.join(output_dir_root, domain_folder, "test")
        os.makedirs(output_dir, exist_ok=True)
        for csv_file in csv_files:
            full_path = os.path.join(test_folder, csv_file)
            print(f"\nProcessing file: {full_path}")
            base_filename = os.path.splitext(csv_file)[0]
            data = pd.read_csv(full_path, sep=",", quoting=csv.QUOTE_MINIMAL, dtype=str)
            new_data = process_first_pass(data)
            new_data2 = process_second_pass(new_data)
            output_file = os.path.join(output_dir, f"{base_filename}_planning.csv")
            new_data2.to_csv(output_file, index=False)
            print(f"Saved processed data to: {output_file}")
    print("All files processed successfully.")


if __name__ == "__main__":
    main()
