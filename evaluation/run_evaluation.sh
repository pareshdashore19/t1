#!/bin/bash

# A script to automate the tool-driven-agents evaluation pipeline.
#
# This script orchestrates the execution of three Python scripts in sequence:
# 1. process_model_output.py: Processes raw model outputs.
# 2. generate_evaluation_metrics.py: Generates evaluation metrics from the processed outputs.
# 3. compute_aggregate_metrics.py: Computes and summarizes the final domain metrics.
#
# Usage:
#   ./run_evaluation.sh <path_to_input_directory>
#
# Example:
#   ./run_evaluation.sh /path/to/your/model/output

# --- Configuration and Argument Handling ---

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if an input directory is provided.
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <input_directory>"
  echo "Example: $0 /path/to/your/model/output"
  exit 1
fi

# --- Variable Definitions ---

MODEL_INPUT_DIR="$1"
MODEL_BASENAME=$(basename "$MODEL_INPUT_DIR")

# --- Directory Paths ---
# Intermediate and final directories for evaluation outputs.
PROCESSED_OUTPUT_DIR="processed_output/${MODEL_BASENAME}"
EVAL_OUTPUT_DIR="eval_output/${MODEL_BASENAME}"
FINAL_METRICS_DIR="metrics"
FINAL_METRICS_FILE="${FINAL_METRICS_DIR}/${MODEL_BASENAME}_metrics.csv"

# Create the necessary directories for the script's output.
mkdir -p "$PROCESSED_OUTPUT_DIR"
mkdir -p "$EVAL_OUTPUT_DIR"
mkdir -p "$FINAL_METRICS_DIR"


# --- Execution Pipeline ---

echo ""
echo "--- Step 1: Processing Raw Model Outputs ---"
export INPUT_DIR="$MODEL_INPUT_DIR"
export OUTPUT_DIR="$PROCESSED_OUTPUT_DIR"
python3 evaluation/process_model_output.py
echo "--- Step 1 complete. ---"
echo ""

echo "--- Step 2: Generating Evaluation Files ---"
export INPUT_DIR="$PROCESSED_OUTPUT_DIR"
export OUTPUT_DIR="$EVAL_OUTPUT_DIR"
python3 evaluation/generate_evaluation_metrics.py
echo "--- Step 2 complete. ---"
echo ""

echo "--- Step 3: Computing Final Metrics ---"
python3 evaluation/compute_aggregate_metrics.py --input_dir "$EVAL_OUTPUT_DIR" --output_csv "$FINAL_METRICS_FILE"
echo "--- Step 3 complete. ---"
echo ""

# --- Final Output ---
echo "✅ Evaluation pipeline finished successfully!"
echo "Final metrics summary is available at: ${FINAL_METRICS_FILE}"
