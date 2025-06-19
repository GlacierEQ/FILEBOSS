# Granite Model Integration

This directory contains the integration of the IBM Granite Code model for code generation tasks.

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the download script:
   ```bash
   python download_model.py
   ```

## Model Information

- **Model Name**: IBM Granite 7B Code
- **Model Type**: Causal Language Model for Code Generation
- **Repository**: [Hugging Face Model Hub](https://huggingface.co/ibm-granite/granite-7b-code)

## Usage

After downloading, you can use the model with the following code:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_path = "models/granite-7b-code"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True
)

def generate_code(prompt, max_length=100, temperature=0.7):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_length,
        temperature=temperature,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## Notes

- The model requires significant GPU memory. Make sure you have at least 16GB of GPU RAM available.
- The first run will download the model weights, which may take time depending on your internet connection.
- The model is designed for code generation and understanding tasks.
