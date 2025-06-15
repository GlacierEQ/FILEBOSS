"""
Example of using token tensors for complex logical decisions in DeepSeek-Coder
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from token_utils import TokenProcessor, CustomLogitsProcessor, custom_token_generation

# Example of a complex logical constraint function
def enforce_programming_style(input_ids, scores):
    """
    Example constraint function that enforces a Python coding style:
    - Encourages proper indentation (4 spaces)
    - Promotes docstrings after function definitions
    - Prefers list comprehensions over for loops where appropriate
    - Favors descriptive variable names
    """
    # Clone scores to avoid modifying the original
    modified_scores = scores.clone()
    
    # Get the last few tokens to determine context
    last_tokens = input_ids[0, -10:].tolist() if input_ids.size(1) >= 10 else input_ids[0, :].tolist()
    last_text = tokenizer.decode(last_tokens)
    
    # Check for function definition (def keyword)
    if "def " in last_text and ":" in last_text and "\n" in last_text.split(":")[-1]:
        # After function definition, encourage docstring
        quote_token_ids = [tokenizer.encode('"""', add_special_tokens=False)[0]]
        # Boost triple quote tokens
        modified_scores[0, quote_token_ids] += 3.0
    
    # Check for indentation after a colon followed by newline
    if ":\n" in last_text or ":\r\n" in last_text:
        # Encourage 4 spaces indentation
        space_token_id = tokenizer.encode(" ", add_special_tokens=False)[0]
        # Boost space tokens
        modified_scores[0, space_token_id] += 2.0
    
    # Check for 'for ' pattern and potentially encourage list comprehension
    if " for " in last_text and " in " in last_text and "[" not in last_text:
        # Encourage opening bracket for list comprehension
        open_bracket_id = tokenizer.encode("[", add_special_tokens=False)[0]
        modified_scores[0, open_bracket_id] += 1.5
    
    # Discourage single-letter variable names except i,j,k in loops
    if "=" in last_text and not any(x in last_text for x in ["for ", "while ", "def "]):
        # Get potential single-letter variable tokens
        single_letters = [tokenizer.encode(f" {c}", add_special_tokens=False)[0] 
                         for c in 'abcdefghijklmnopqrstuvwxyz'
                         if c not in 'ijk']
        
        # Reduce scores for single letter variables
        modified_scores[0, single_letters] -= 1.0
    
    return modified_scores

# Function to demonstrate tensor-based logic for code completion
def complete_code_with_tensor_logic(prompt, model_name="deepseek-ai/deepseek-coder-1.3b-instruct"):
    """Complete code using tensor-based logical decisions"""
    global tokenizer  # Make tokenizer accessible to the constraint function
    
    # Load model and tokenizer
    print(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True
    )
    
    # Move model to GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    
    # Create token processor
    token_processor = TokenProcessor(tokenizer)
    logits_processor = CustomLogitsProcessor(tokenizer)
    
    print("\n=== Standard Generation ===")
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    attention_mask = torch.ones_like(input_ids).to(device)
    outputs = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.7,
        top_p=0.95
    )
    standard_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(standard_output)
    
    print("\n=== Tensor-based Logical Constraints Generation ===")
    # Generate with custom logical constraints
    logical_output = custom_token_generation(
        model,
        tokenizer,
        prompt,
        max_new_tokens=150,
        logical_constraints=enforce_programming_style,
        temperature=0.7,
        top_k=50,
        top_p=0.95
    )
    print(logical_output)
    
    print("\n=== Token-by-Token Analysis ===")
    # Analyze tokens from both generations
    standard_tokens = tokenizer.encode(standard_output)
    logical_tokens = tokenizer.encode(logical_output)
    
    # Compare the two generations in terms of tokens
    print(f"Standard generation: {len(standard_tokens)} tokens")
    print(f"Logical generation: {len(logical_tokens)} tokens")
    
    # Count common tokens
    common_count = sum(1 for i in range(min(len(standard_tokens), len(logical_tokens))) 
                      if standard_tokens[i] == logical_tokens[i])
    
    print(f"Common tokens: {common_count}")
    print(f"Percentage similarity: {common_count / min(len(standard_tokens), len(logical_tokens)) * 100:.2f}%")
    
    return standard_output, logical_output

if __name__ == "__main__":
    # Example prompt for code completion
    prompt = """
def calculate_statistics(numbers):
    """
    
    # Run the example
    complete_code_with_tensor_logic(prompt)
