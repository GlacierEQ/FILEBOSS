"""
Utilities for advanced token manipulation and tensor processing in DeepSeek-Coder
"""
import torch
import numpy as np
from typing import List, Dict, Optional, Union, Tuple, Callable


class TokenProcessor:
    """Class for processing and manipulating tokens as tensors"""
    
    def __init__(self, tokenizer):
        """Initialize with a tokenizer"""
        self.tokenizer = tokenizer
        self.special_tokens = {
            "bos_token": tokenizer.bos_token_id if hasattr(tokenizer, 'bos_token_id') else None,
            "eos_token": tokenizer.eos_token_id if hasattr(tokenizer, 'eos_token_id') else None,
            "pad_token": tokenizer.pad_token_id if hasattr(tokenizer, 'pad_token_id') else None,
        }
        
    def encode_to_tensor(self, text: str) -> torch.Tensor:
        """Encode text to token tensor"""
        tokens = self.tokenizer(text, return_tensors="pt")
        return tokens.input_ids
    
    def decode_from_tensor(self, tokens: torch.Tensor, skip_special_tokens: bool = True) -> str:
        """Decode token tensor to text"""
        return self.tokenizer.decode(tokens[0], skip_special_tokens=skip_special_tokens)
    
    def get_token_logprobs(self, model, input_ids: torch.Tensor, attention_mask: torch.Tensor = None) -> torch.Tensor:
        """Get log probabilities for each token"""
        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)
        
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
        # Get log probabilities
        log_probs = torch.log_softmax(logits, dim=-1)
        
        # For each position, get the log probability of the actual token
        token_log_probs = torch.gather(
            log_probs[:, :-1, :], 
            dim=2, 
            index=input_ids[:, 1:].unsqueeze(-1)
        ).squeeze(-1)
        
        return token_log_probs
    
    def find_tokens(self, token_ids: torch.Tensor, target_ids: List[int]) -> List[int]:
        """Find positions of target tokens in a sequence"""
        if isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.cpu().numpy()
            
        target_ids = np.array(target_ids)
        positions = []
        
        for i in range(len(token_ids)):
            if i + len(target_ids) <= len(token_ids):
                if np.array_equal(token_ids[i:i+len(target_ids)], target_ids):
                    positions.append(i)
                    
        return positions
    
    def create_attention_mask(self, 
                             input_ids: torch.Tensor,
                             causal: bool = True,
                             windows_size: Optional[int] = None) -> torch.Tensor:
        """Create custom attention mask tensor"""
        batch_size, seq_len = input_ids.shape
        
        if causal:
            # Causal mask (can't look at future tokens)
            mask = torch.tril(torch.ones((seq_len, seq_len), dtype=torch.float32))
            mask = mask.unsqueeze(0).expand(batch_size, -1, -1)
        else:
            # Full attention
            mask = torch.ones((batch_size, seq_len, seq_len), dtype=torch.float32)
        
        if windows_size is not None:
            # Windowed attention (can only look at nearby tokens)
            window_mask = torch.zeros((seq_len, seq_len), dtype=torch.float32)
            for i in range(seq_len):
                start = max(0, i - windows_size)
                end = min(seq_len, i + windows_size + 1)
                window_mask[i, start:end] = 1.0
            
            mask = mask * window_mask.unsqueeze(0)
        
        return mask
    
    def apply_token_filtering(self, 
                             logits: torch.Tensor, 
                             filter_fn: Callable[[torch.Tensor], torch.Tensor]) -> torch.Tensor:
        """Apply custom filtering to logits"""
        return filter_fn(logits)
    
    def top_k_top_p_filtering(self, 
                             logits: torch.Tensor,
                             top_k: int = 0, 
                             top_p: float = 1.0,
                             temperature: float = 1.0,
                             filter_value: float = -float('Inf')) -> torch.Tensor:
        """
        Filter a distribution of logits using top-k and/or top-p (nucleus) filtering
        
        Args:
            logits: torch.Tensor - logits distribution shape (batch size, vocabulary size)
            top_k: int - keep only top k tokens with highest probability (top-k filtering)
            top_p: float - keep the top tokens with cumulative probability >= top_p (nucleus filtering)
            temperature: float - temperature for softmax
            filter_value: float - value to use for filtered tokens
            
        Returns:
            torch.Tensor - filtered logits
        """
        if temperature != 1.0:
            logits = logits / temperature
            
        if top_k > 0:
            top_k = min(top_k, logits.size(-1))  # Safety check
            # Remove all tokens with a probability less than the last token of the top-k
            indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
            logits[indices_to_remove] = filter_value

        if top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)

            # Remove tokens with cumulative probability above the threshold
            sorted_indices_to_remove = cumulative_probs > top_p
            # Shift the indices to the right to keep also the first token above the threshold
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0

            # Scatter sorted tensors to original indexing
            indices_to_remove = sorted_indices_to_remove.scatter(
                -1, sorted_indices, sorted_indices_to_remove
            )
            logits[indices_to_remove] = filter_value
            
        return logits
    
    def get_token_importance(self, model, input_ids: torch.Tensor, target_labels: torch.Tensor = None) -> torch.Tensor:
        """
        Calculate token importance based on gradients
        
        Args:
            model: the model to use
            input_ids: input token ids
            target_labels: target output labels, if None, uses input_ids shifted right
            
        Returns:
            torch.Tensor containing importance scores for each token
        """
        if target_labels is None:
            target_labels = input_ids.clone()[:, 1:]
            
        input_ids.requires_grad_(True)
        outputs = model(input_ids)
        logits = outputs.logits[:, :-1]
        
        loss = torch.nn.functional.cross_entropy(
            logits.reshape(-1, logits.size(-1)),
            target_labels.reshape(-1),
            reduction='none'
        )
        loss = loss.mean()
        
        loss.backward()
        
        importance = input_ids.grad.abs().sum(dim=-1)
        return importance


class CustomLogitsProcessor:
    """Custom logits processor for controlling token generation"""
    
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.token_processor = TokenProcessor(tokenizer)
        
    def process_logits_for_logical_constraints(self, 
                                              input_ids: torch.Tensor,
                                              scores: torch.Tensor,
                                              logic_fn: Callable) -> torch.Tensor:
        """
        Apply custom logical constraints to logits during generation
        
        Args:
            input_ids: Current input token ids
            scores: Current token scores (logits)
            logic_fn: Function that takes (input_ids, scores) and returns modified scores
            
        Returns:
            torch.Tensor with modified scores
        """
        return logic_fn(input_ids, scores)
    
    def enforce_token_constraints(self,
                                 scores: torch.Tensor,
                                 allowed_tokens: List[int] = None,
                                 disallowed_tokens: List[int] = None,
                                 filter_value: float = -float('Inf')) -> torch.Tensor:
        """
        Enforce constraints on allowed and disallowed tokens
        
        Args:
            scores: logits to modify
            allowed_tokens: list of allowed token ids (if provided, only these tokens are allowed)
            disallowed_tokens: list of disallowed token ids
            filter_value: value to assign to disallowed tokens
            
        Returns:
            torch.Tensor with modified scores
        """
        if allowed_tokens is not None:
            # Create a mask with False everywhere except at allowed token positions
            mask = torch.zeros_like(scores, dtype=torch.bool)
            mask[..., allowed_tokens] = True
            
            # Apply the mask
            scores = torch.where(mask, scores, torch.tensor(filter_value, device=scores.device))
            
        if disallowed_tokens is not None:
            # Set scores for disallowed tokens to filter_value
            scores[..., disallowed_tokens] = filter_value
            
        return scores
    
    def encourage_token_sequence(self,
                                input_ids: torch.Tensor,
                                scores: torch.Tensor,
                                target_sequences: List[List[int]],
                                boost_factor: float = 5.0) -> torch.Tensor:
        """
        Encourage generation of specific token sequences by boosting their probabilities
        
        Args:
            input_ids: Current input token ids
            scores: Current token scores (logits)
            target_sequences: List of token sequences to encourage
            boost_factor: Factor to boost the scores by
            
        Returns:
            torch.Tensor with modified scores
        """
        # For each target sequence
        for target_seq in target_sequences:
            if len(target_seq) > 1:
                # Check if the input might be at the beginning of this sequence
                for seq_len in range(min(len(target_seq)-1, input_ids.shape[1])):
                    if seq_len > 0:
                        check_seq = target_seq[:seq_len]
                        # Check if the last seq_len tokens match the beginning of target_seq
                        if torch.all(input_ids[0, -seq_len:] == torch.tensor(check_seq, device=input_ids.device)):
                            # Boost the next token in the sequence
                            next_token = target_seq[seq_len]
                            scores[0, next_token] += boost_factor
                    
        return scores


def custom_token_generation(model, tokenizer, prompt, 
                          max_new_tokens=50,
                          logical_constraints=None,
                          temperature=0.7,
                          top_k=50,
                          top_p=0.95):
    """
    Generate text with custom token-level logical constraints
    
    Args:
        model: The model to use for generation
        tokenizer: The tokenizer to use
        prompt: The input prompt text
        max_new_tokens: Maximum number of new tokens to generate
        logical_constraints: Custom function for token constraints
        temperature: Temperature for sampling
        top_k: Top-k filtering value
        top_p: Top-p (nucleus) filtering value
        
    Returns:
        Generated text
    """
    # Create token processor and logits processor
    token_processor = TokenProcessor(tokenizer)
    logits_processor = CustomLogitsProcessor(tokenizer)
    
    # Encode the prompt
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
    attention_mask = torch.ones_like(input_ids)
    
    # Generate tokens one at a time with custom constraints
    for _ in range(max_new_tokens):
        # Forward pass through the model
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            
        # Get logits for the next token
        next_token_logits = outputs.logits[:, -1, :]
        
        # Apply temperature
        next_token_logits = next_token_logits / temperature
        
        # Apply top-k and top-p filtering
        next_token_logits = token_processor.top_k_top_p_filtering(
            next_token_logits, top_k=top_k, top_p=top_p
        )
        
        # Apply custom logical constraints if provided
        if logical_constraints is not None:
            next_token_logits = logits_processor.process_logits_for_logical_constraints(
                input_ids, next_token_logits, logical_constraints
            )
        
        # Sample next token
        probs = torch.softmax(next_token_logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        
        # Check for EOS
        if next_token.item() == tokenizer.eos_token_id:
            break
            
        # Concatenate the sampled token to the output
        input_ids = torch.cat([input_ids, next_token], dim=-1)
        attention_mask = torch.cat([
            attention_mask,
            torch.ones((1, 1), dtype=torch.long, device=attention_mask.device)
        ], dim=1)
    
    # Decode the generated text
    generated_text = tokenizer.decode(input_ids[0], skip_special_tokens=True)
    return generated_text


def tensor_manipulation_examples():
    """Examples of tensor manipulation for tokens"""
    print("Token Tensor Manipulation Examples:")
    print("1. Convert tokens to one-hot encodings:")
    print("   tokens = torch.tensor([1, 5, 10])")
    print("   one_hot = F.one_hot(tokens, num_classes=vocab_size)")
    
    print("\n2. Token masking example:")
    print("   # Create a mask to hide certain tokens")
    print("   mask = torch.ones_like(tokens)")
    print("   mask[tokens == special_token_id] = 0")
    print("   masked_tokens = tokens * mask")
    
    print("\n3. Token type embeddings:")
    print("   # Create token type ids (0 for prompt, 1 for completion)")
    print("   token_type_ids = torch.zeros_like(tokens)")
    print("   token_type_ids[prompt_length:] = 1")
    
    print("\n4. Token position analysis:")
    print("   # Find positions of specific tokens")
    print("   positions = (tokens == target_token_id).nonzero()")
    
    print("\n5. Logit manipulation for controlled generation:")
    print("   # Modify logits to promote specific tokens")
    print("   logits[:, preferred_token_ids] += boost_factor")
