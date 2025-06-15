#!/usr/bin/env python3
"""
Command-line interface for tensor operations and advanced token manipulations
"""
import os
import sys
import json
import argparse
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from token_utils import TokenProcessor, CustomLogitsProcessor, custom_token_generation
from token_visualization import TokenVisualizer
from tensor_manager import TokenTensorManager
import numpy as np
import matplotlib.pyplot as plt

def save_tensor_info(tensor, filename):
    """Save tensor information to a file"""
    info = {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
        "min": float(tensor.min()),
        "max": float(tensor.max()),
        "mean": float(tensor.mean()),
        "std": float(tensor.std()),
    }
    
    # If small enough, include the actual tensor values
    if tensor.numel() <= 100:
        info["values"] = tensor.tolist()
        
    with open(filename, 'w') as f:
        json.dump(info, f, indent=2)
    
    return info

def process_code_with_tensor_ops(args):
    """Process code with tensor operations"""
    print(f"Loading model: {args.model}")
    
    # Initialize tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.float16 if torch.cuda.is_available() and not args.cpu else torch.float32,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    
    # Move model to device
    device = "cuda" if torch.cuda.is_available() and not args.cpu else "cpu"
    model = model.to(device)
    
    # Create managers
    token_processor = TokenProcessor(tokenizer)
    tensor_manager = TokenTensorManager(tokenizer, device=torch.device(device))
    
    # Load code from file or use input
    if args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        code = args.code
    
    # Process based on operation
    if args.op == "visualize":
        visualizer = TokenVisualizer(tokenizer, model)
        
        if args.attention:
            print("Generating attention visualization...")
            output = visualizer.plot_attention_heads(
                code, 
                layer_idx=args.layer, 
                head_indices=args.heads,
                output_filename=args.output
            )
            if output:
                print(f"Visualization generated. Base64 string available.")
            else:
                print(f"Visualization saved to {args.output}")
            
        elif args.importance:
            print("Calculating token importance...")
            output = visualizer.get_token_importance(code, output_filename=args.output)
            
            if isinstance(output, dict):
                # Print top important tokens
                sorted_tokens = sorted(output.items(), key=lambda x: x[1], reverse=True)
                print("\nTop important tokens:")
                for token, score in sorted_tokens[:10]:
                    print(f"{token}: {score:.4f}")
                
                if args.output:
                    print(f"Visualization saved to {args.output}")
            
        elif args.embeddings:
            # Tokenize and split into words for embedding visualization
            words = code.split()
            if len(words) > 30:  # Limit to avoid cluttered visualization
                print("Warning: Input has many words. Using first 30 for visualization.")
                words = words[:30]
                
            print("Generating embedding visualization...")
            output = visualizer.visualize_token_embeddings(
                words, 
                method=args.method or 'pca',
                output_filename=args.output
            )
            if args.output:
                print(f"Visualization saved to {args.output}")
            
    elif args.op == "analyze":
        # Tokenize input
        tokens = tokenizer.tokenize(code)
        token_ids = tokenizer.encode(code, add_special_tokens=False)
        
        # Print token analysis
        print(f"Total tokens: {len(tokens)}")
        print(f"Unique tokens: {len(set(token_ids))}")
        
        # Print token information
        if len(tokens) <= 30 or args.verbose:
            print("\nToken breakdown:")
            for i, (token, id_) in enumerate(zip(tokens, token_ids)):
                print(f"{i}: {token} (ID: {id_})")
        else:
            print("\nFirst 15 tokens:")
            for i, (token, id_) in enumerate(zip(tokens[:15], token_ids[:15])):
                print(f"{i}: {token} (ID: {id_})")
            print("...")
            print("\nLast 15 tokens:")
            for i, (token, id_) in enumerate(zip(tokens[-15:], token_ids[-15:]), len(tokens)-15):
                print(f"{i}: {token} (ID: {id_})")
                
        # Get subword groups
        if args.subwords:
            print("\nSubword grouping:")
            groups = tensor_manager.get_subword_groups(code)
            for i, group in enumerate(groups):
                tokens_str = " + ".join([token for token, _ in group])
                positions = [pos for _, pos in group]
                print(f"Word {i}: {tokens_str} (positions: {positions})")
                
        # Token statistics
        print("\nToken ID statistics:")
        id_array = np.array(token_ids)
        print(f"Min ID: {id_array.min()}")
        print(f"Max ID: {id_array.max()}")
        print(f"Mean ID: {id_array.mean():.2f}")
        print(f"Median ID: {np.median(id_array):.2f}")
        
        # Save tensors if requested
        if args.output:
            # Tokenize with return tensors
            inputs = tokenizer(code, return_tensors="pt")
            
            # Save input_ids tensor info
            input_ids_info = save_tensor_info(inputs.input_ids, f"{args.output}_input_ids.json")
            print(f"\nInput IDs tensor info saved to {args.output}_input_ids.json")
            
    elif args.op == "manipulate":
        # Tokenize input
        inputs = tokenizer(code, return_tensors="pt").to(device)
        input_ids = inputs.input_ids
        attention_mask = inputs.attention_mask if 'attention_mask' in inputs else torch.ones_like(input_ids)
        
        if args.mask:
            # Parse tokens to mask (comma-separated)
            tokens_to_mask = args.mask.split(',')
            mask_ids = []
            for t in tokens_to_mask:
                t = t.strip()
                if t.isdigit():
                    # If number, treat as token ID
                    mask_ids.append(int(t))
                else:
                    # Otherwise encode as token(s)
                    ids = tokenizer.encode(t, add_special_tokens=False)
                    mask_ids.extend(ids)
            
            # Create and apply mask
            mask = tensor_manager.create_token_mask(input_ids, mask_ids)
            masked_ids = tensor_manager.apply_token_mask(input_ids, mask)
            
            # Decode and show result
            original_text = tokenizer.decode(input_ids[0])
            masked_text = tokenizer.decode(masked_ids[0])
            
            print("Original text:")
            print(original_text)
            print("\nMasked text:")
            print(masked_text)
            
        elif args.boost:
            # Parse tokens to boost (format: token:weight,token:weight)
            token_weights = {}
            for item in args.boost.split(','):
                if ':' in item:
                    token, weight = item.split(':')
                    token = token.strip()
                    weight = float(weight.strip())
                    
                    # Get token ID(s)
                    if token.isdigit():
                        token_id = int(token)
                        token_weights[token_id] = weight
                    else:
                        ids = tokenizer.encode(token, add_special_tokens=False)
                        for id_ in ids:
                            token_weights[id_] = weight
            
            # Create logits processor
            logits_processor = CustomLogitsProcessor(tokenizer)
            
            # Generate with boosted tokens
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                logits_processor=[
                    lambda input_ids, scores: logits_processor.enforce_token_constraints(
                        scores,
                        allowed_tokens=None,
                        disallowed_tokens=None,
                    )
                ]
            )
            
            result = tokenizer.decode(outputs[0])
            print("Generated with token boosting:")
            print(result)
    
    elif args.op == "generate":
        # Define a logical constraint function if specified
        constraint_fn = None
        
        if args.style == "python":
            def python_style_constraint(input_ids, scores):
                """Enforce Python coding style"""
                # Clone scores to avoid modifying the original
                modified_scores = scores.clone()
                
                # Get the last few tokens to determine context
                last_tokens = input_ids[0, -10:].tolist() if input_ids.size(1) >= 10 else input_ids[0, :].tolist()
                last_text = tokenizer.decode(last_tokens)
                
                # After colon and newline, encourage indentation
                if ":\n" in last_text:
                    space_id = tokenizer.encode(" ", add_special_tokens=False)[0]
                    modified_scores[0, space_id] += 2.0  # Boost spaces for indentation
                
                # Boost docstring tokens after function def
                if "def " in last_text and ":" in last_text:
                    triple_quote_ids = tokenizer.encode('"""', add_special_tokens=False)
                    for id_ in triple_quote_ids:
                        modified_scores[0, id_] += 1.5
                
                return modified_scores
                
            constraint_fn = python_style_constraint
            print("Using Python style constraint for generation")
        
        # Generate using custom token generation
        result = custom_token_generation(
            model,
            tokenizer,
            code,
            max_new_tokens=args.max_tokens or 100,
            logical_constraints=constraint_fn,
            temperature=args.temp or 0.7,
            top_k=args.top_k or 50,
            top_p=args.top_p or 0.95
        )
        
        print("\nGenerated result:")
        print(result)
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"\nResult saved to {args.output}")

def main():
    parser = argparse.ArgumentParser(description="DeepSeek-Coder Token Tensor Operations")
    
    # Model parameters
    parser.add_argument("--model", type=str, 
                       default="deepseek-ai/deepseek-coder-1.3b-instruct",
                       help="Model name or path")
    parser.add_argument("--cpu", action="store_true",
                       help="Force CPU usage even if GPU is available")
    
    # Input source
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--code", type=str,
                           help="Code or text to process")
    input_group.add_argument("--file", type=str,
                           help="File containing code to process")
    
    # Operation to perform
    parser.add_argument("--op", type=str, required=True,
                       choices=["visualize", "analyze", "manipulate", "generate"],
                       help="Operation to perform on tokens")
    
    # Visualization options
    parser.add_argument("--attention", action="store_true",
                      help="Visualize attention patterns")
    parser.add_argument("--layer", type=int, default=-1,
                      help="Layer index for attention visualization")
    parser.add_argument("--heads", type=int, nargs="+",
                      help="Attention head indices to visualize")
    parser.add_argument("--importance", action="store_true",
                      help="Calculate and visualize token importance")
    parser.add_argument("--embeddings", action="store_true",
                      help="Visualize token embeddings")
    parser.add_argument("--method", type=str, choices=["pca", "tsne"],
                      help="Dimensionality reduction method for embeddings")
    
    # Analysis options
    parser.add_argument("--verbose", action="store_true",
                      help="Show detailed token information")
    parser.add_argument("--subwords", action="store_true",
                      help="Group tokens into subwords")
    
    # Manipulation options
    parser.add_argument("--mask", type=str,
                      help="Tokens to mask (comma-separated IDs or text)")
    parser.add_argument("--boost", type=str,
                      help="Boost token probabilities (format: token:weight,token:weight)")
    
    # Generation options
    parser.add_argument("--style", type=str, choices=["python", "general"],
                      help="Style constraint for generation")
    parser.add_argument("--max-tokens", type=int,
                      help="Maximum number of tokens to generate")
    parser.add_argument("--temp", type=float,
                      help="Temperature for generation")
    parser.add_argument("--top-k", type=int,
                      help="Top-k for generation")
    parser.add_argument("--top-p", type=float,
                      help="Top-p (nucleus) for generation")
    
    # Output options
    parser.add_argument("--output", type=str,
                      help="Output file for results or visualizations")
    
    args = parser.parse_args()
    
    try:
        process_code_with_tensor_ops(args)
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
