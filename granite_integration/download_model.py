import os
from huggingface_hub import login, snapshot_download
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def setup_huggingface():
    # Use the provided API key
    api_key = "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"
    login(token=api_key)

def download_model():
    # Granite Coder model ID from Hugging Face
    model_id = "ibm-granite/granite-7b-code"
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    print(f"Downloading {model_id}...")
    
    # Download model and tokenizer
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True
    )
    
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    
    # Save model and tokenizer locally
    model_save_path = os.path.join("models", "granite-7b-code")
    model.save_pretrained(model_save_path)
    tokenizer.save_pretrained(model_save_path)
    
    print(f"Model and tokenizer saved to {model_save_path}")
    return model, tokenizer

def test_model(model, tokenizer):
    print("\nTesting the model...")
    
    # Test prompt
    prompt = "def hello_world():"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Generate text
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("\nGenerated code:")
    print(generated_text)

if __name__ == "__main__":
    print("Setting up Hugging Face...")
    setup_huggingface()
    
    print("\nDownloading Granite model...")
    model, tokenizer = download_model()
    
    print("\nModel downloaded successfully!")
    test_model(model, tokenizer)
