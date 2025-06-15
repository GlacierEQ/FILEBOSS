"""
Advanced tensor operations for complex logical decisions with DeepSeek-Coder
"""
import torch
import numpy as np
from typing import List, Dict, Optional, Union, Callable, Tuple, Any
from dataclasses import dataclass
from transformers import PreTrainedTokenizer, LogitsProcessor, PreTrainedModel

@dataclass
class TokenConstraintRule:
    """Rule for token generation constraints"""
    name: str
    description: str
    condition: Callable[[List[int], str], bool]
    action: Callable[[torch.Tensor], torch.Tensor]
    priority: int = 1

class AdvancedLogitsProcessor(LogitsProcessor):
    """Advanced logits processor with rule-based approach"""
    
    def __init__(self, tokenizer: PreTrainedTokenizer, rules: List[TokenConstraintRule] = None):
        self.tokenizer = tokenizer
        self.rules = rules or []
        self.activation_history = []  # Track which rules were activated
    
    def add_rule(self, rule: TokenConstraintRule):
        """Add a constraint rule"""
        self.rules.append(rule)
        # Sort rules by priority (higher first)
        self.rules.sort(key=lambda x: x.priority, reverse=True)
    
    def clear_history(self):
        """Clear rule activation history"""
        self.activation_history = []
    
    def get_activation_stats(self):
        """Get statistics on rule activations"""
        if not self.activation_history:
            return {}
        
        stats = {}
        for rule_name in self.activation_history:
            stats[rule_name] = stats.get(rule_name, 0) + 1
        
        return stats
    
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        """Apply all constraint rules based on the current context"""
        modified_scores = scores.clone()
        
        # Get the context from the input
        last_tokens = input_ids[0, -20:].tolist() if input_ids.size(1) > 20 else input_ids[0].tolist()
        context_str = self.tokenizer.decode(last_tokens)
        
        # Apply each rule if its condition is met
        for rule in self.rules:
            if rule.condition(last_tokens, context_str):
                modified_scores = rule.action(modified_scores)
                self.activation_history.append(rule.name)
        
        return modified_scores


class TensorDecisionTree:
    """Decision tree for complex tensor operations"""
    
    def __init__(self, tokenizer: PreTrainedTokenizer):
        self.tokenizer = tokenizer
        self.nodes = {}
        self.next_id = 0
    
    def add_node(self, 
                condition_fn: Callable[[torch.Tensor], bool], 
                true_action: Optional[Callable[[torch.Tensor], torch.Tensor]] = None,
                false_action: Optional[Callable[[torch.Tensor], torch.Tensor]] = None,
                true_node: Optional[int] = None,
                false_node: Optional[int] = None) -> int:
        """
        Add a node to the decision tree
        
        Args:
            condition_fn: Function that takes input_ids and returns boolean
            true_action: Action to take if condition is true
            false_action: Action to take if condition is false
            true_node: Node ID to go to if condition is true
            false_node: Node ID to go to if condition is false
            
        Returns:
            ID of the added node
        """
        node_id = self.next_id
        self.next_id += 1
        
        self.nodes[node_id] = {
            "condition": condition_fn,
            "true_action": true_action,
            "false_action": false_action,
            "true_node": true_node,
            "false_node": false_node
        }
        
        return node_id
    
    def process(self, input_ids: torch.Tensor, scores: torch.Tensor, start_node: int = 0) -> torch.Tensor:
        """
        Process scores through the decision tree
        
        Args:
            input_ids: Input token IDs
            scores: Scores to modify
            start_node: Node ID to start from
            
        Returns:
            Modified scores
        """
        current_node_id = start_node
        modified_scores = scores.clone()
        
        # Set a maximum depth to prevent infinite loops
        max_depth = 100
        depth = 0
        
        while current_node_id is not None and depth < max_depth:
            if current_node_id not in self.nodes:
                break
                
            node = self.nodes[current_node_id]
            condition_result = node["condition"](input_ids)
            
            if condition_result:
                # Follow true branch
                if node["true_action"] is not None:
                    modified_scores = node["true_action"](modified_scores)
                current_node_id = node["true_node"]
            else:
                # Follow false branch
                if node["false_action"] is not None:
                    modified_scores = node["false_action"](modified_scores)
                current_node_id = node["false_node"]
                
            depth += 1
            
        return modified_scores


class RollingWindowTensorProcessor:
    """Process tokens in a rolling window for long contexts"""
    
    def __init__(self, 
                tokenizer: PreTrainedTokenizer, 
                window_size: int = 1024,
                overlap: int = 128):
        """
        Initialize with tokenizer and window parameters
        
        Args:
            tokenizer: The tokenizer to use
            window_size: Number of tokens in each window
            overlap: Number of tokens to overlap between windows
        """
        self.tokenizer = tokenizer
        self.window_size = window_size
        self.overlap = overlap
    
    def process_long_text(self, 
                         model: PreTrainedModel, 
                         text: str,
                         processor_fn: Callable[[torch.Tensor, torch.Tensor], torch.Tensor]) -> List[torch.Tensor]:
        """
        Process long text by breaking it into windows
        
        Args:
            model: The model to use
            text: Text to process
            processor_fn: Function to apply to each window (takes input_ids and scores)
            
        Returns:
            List of processed tensor results
        """
        # Tokenize the text
        tokens = self.tokenizer.encode(text)
        
        # Process in windows
        results = []
        start_idx = 0
        
        while start_idx < len(tokens):
            # Get the current window
            end_idx = min(start_idx + self.window_size, len(tokens))
            window_tokens = tokens[start_idx:end_idx]
            
            # Convert to tensor
            window_input_ids = torch.tensor([window_tokens], device=model.device)
            
            # Process the window
            with torch.no_grad():
                outputs = model(window_input_ids)
                scores = outputs.logits[:, -1, :]  # Get scores for next token prediction
                
                # Apply the processor function
                processed_scores = processor_fn(window_input_ids, scores)
                results.append(processed_scores)
            
            # Move to next window with overlap
            start_idx += (self.window_size - self.overlap)
        
        return results


class TensorAttentionAnalyzer:
    """Analyze attention patterns for token relationships"""
    
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer):
        self.model = model
        self.tokenizer = tokenizer
    
    def get_attention_weights(self, input_ids: torch.Tensor) -> List[torch.Tensor]:
        """
        Get attention weights for each layer
        
        Args:
            input_ids: Input token IDs
            
        Returns:
            List of attention weight tensors [layer, batch, heads, seq_len, seq_len]
        """
        # Create attention mask
        attention_mask = torch.ones_like(input_ids)
        
        # Get attention weights
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_attentions=True
            )
            
        return outputs.attentions
    
    def find_token_relationships(self, 
                                text: str, 
                                target_token: str,
                                layer_idx: int = -1,
                                threshold: float = 0.1) -> Dict[str, float]:
        """
        Find tokens that have strong attention relationships with target token
        
        Args:
            text: Input text
            target_token: Token to analyze relationships for
            layer_idx: Layer to analyze
            threshold: Minimum attention score to consider a relationship
            
        Returns:
            Dictionary mapping related tokens to attention scores
        """
        # Tokenize input
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        input_ids = inputs.input_ids
        
        # Get attention weights
        attentions = self.get_attention_weights(input_ids)
        
        # Get the specified layer
        if layer_idx < 0:
            layer_idx = len(attentions) + layer_idx
        layer_attention = attentions[layer_idx]
        
        # Get token indices
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        target_indices = [i for i, t in enumerate(tokens) if target_token in t]
        
        if not target_indices:
            return {}
        
        # Average attention across heads for each target position
        relationships = {}
        
        for target_idx in target_indices:
            # Get average attention from the target to all other tokens
            avg_attention = layer_attention[0, :, target_idx, :].mean(dim=0)
            
            # Find tokens with attention above threshold
            for i, score in enumerate(avg_attention):
                if i != target_idx and score >= threshold:
                    token = tokens[i]
                    if token in relationships:
                        relationships[token] = max(relationships[token], score.item())
                    else:
                        relationships[token] = score.item()
        
        return {k: v for k, v in sorted(relationships.items(), key=lambda x: x[1], reverse=True)}


# Create common constraint rules for code generation
def create_python_constraint_rules(tokenizer: PreTrainedTokenizer) -> List[TokenConstraintRule]:
    """Create constraint rules for Python code generation"""
    rules = []
    
    # Encourage proper indentation after colon and newline
    def indent_condition(tokens, context):
        return ":\n" in context or ":\r\n" in context
    
    def indent_action(scores):
        space_id = tokenizer.encode(" ", add_special_tokens=False)[0]
        scores[0, space_id] += 2.0
        return scores
    
    rules.append(TokenConstraintRule(
        name="python_indent",
        description="Encourage indentation after colon and newline",
        condition=indent_condition,
        action=indent_action,
        priority=3
    ))
    
    # Encourage docstrings after function definitions
    def docstring_condition(tokens, context):
        return "def " in context and ":" in context and "(" in context and ")" in context
    
    def docstring_action(scores):
        quote_tokens = tokenizer.encode('"""', add_special_tokens=False)
        for qt in quote_tokens:
            scores[0, qt] += 2.5
        return scores
    
    rules.append(TokenConstraintRule(
        name="python_docstring",
        description="Encourage docstrings after function definitions",
        condition=docstring_condition,
        action=docstring_action,
        priority=2
    ))
    
    # Discourage single-letter variable names (except loop variables)
    def var_name_condition(tokens, context):
        last_line = context.split("\n")[-1] if "\n" in context else context
        return "=" in last_line and not any(x in last_line for x in ["for ", "while "])
    
    def var_name_action(scores):
        single_letters = []
        for c in "abcdefghijklmnopqrstuvwxyz":
            if c not in "ijk":  # Allow i,j,k for loops
                var_tokens = tokenizer.encode(f" {c}", add_special_tokens=False)
                single_letters.extend(var_tokens)
        
        scores[0, single_letters] -= 1.0
        return scores
    
    rules.append(TokenConstraintRule(
        name="python_var_names",
        description="Discourage single-letter variable names",
        condition=var_name_condition,
        action=var_name_action,
        priority=1
    ))
    
    return rules


# Example of use
def example_usage():
    """Example usage of advanced tensor operations"""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    # Load model and tokenizer
    model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
    
    # Create logits processor with rules
    processor = AdvancedLogitsProcessor(tokenizer, create_python_constraint_rules(tokenizer))
    
    # Example prompt
    prompt = "def calculate_fibonacci(n):"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # Generate with the processor
    outputs = model.generate(
        inputs.input_ids,
        max_length=200,
        do_sample=True,
        logits_processor=[processor],
        temperature=0.7
    )
    
    # Print result
    result = tokenizer.decode(outputs[0])
    print(result)
    
    # Print rule activation stats
    print("\nRule activation statistics:")
    for rule, count in processor.get_activation_stats().items():
        print(f"{rule}: {count} times")


if __name__ == "__main__":
    example_usage()
