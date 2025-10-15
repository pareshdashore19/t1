from huggingface_hub import snapshot_download

# ---- CONFIG ----
DATASET_PATH = "capitalone/T1"  # e.g., "databricks/databricks-dolly-15k"
SAVE_DIR = "./dataset"

# ---- DOWNLOAD ----
snapshot_download(
    repo_id=DATASET_PATH,
    repo_type="dataset",
    local_dir=SAVE_DIR,
    local_dir_use_symlinks=False,  # ensures actual files are copied, not symlinks
)

print(f"✅ Dataset downloaded to: {SAVE_DIR}")
