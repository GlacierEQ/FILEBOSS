import os
from huggingface_hub import snapshot_download

def download_model():
    # Hugging Face model ID for Granite Code
    model_id = "ibm-granite/granite-8b-code-instruct-4k"
    
    # Local directory to save the model
    local_dir = "./models/granite-7b-code"
    os.makedirs(local_dir, exist_ok=True)
    
    print(f"Downloading {model_id} to {local_dir}...")
    
    # Download the model
    snapshot_download(
        repo_id=model_id,
        local_dir=local_dir,
        local_dir_use_symlinks=False,
        token="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",
        ignore_patterns=["*.h5", "*.ot", "*.msgpack"],
    )
    
    print(f"\nModel downloaded successfully to {local_dir}")

if __name__ == "__main__":
    download_model()
