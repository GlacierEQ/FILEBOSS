"""
Tensor management utilities for advanced token operations in DeepSeek-Coder
"""
import torch
import numpy as np
from typing import Dict, List, Optional, Union, Callable, Tuple, Any
from transformers import PreTrainedTokenizer

class TokenTensorManager:
    """Manage token tensors for advanced operations"""
    
    def __init__(self, tokenizer: PreTrainedTokenizer, device: Optional[torch.device] = None):
        """Initialize with tokenizer and optional device"""
        self.tokenizer = tokenizer
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.cached_tensors = {}
        self.special_tokens_ids = {
            'bos': tokenizer.bos_token_id,
            'eos': tokenizer.eos_token_id,
            'pad': tokenizer.pad_token_id,
        }
        
    def clear_cache(self):
        """Clear the tensor cache"""
        self.cached_tensors = {}
        torch.cuda.empty_cache() if self.device.type == 'cuda' else None
        
    def tokenize_batch(self, 
                      texts: List[str], 
                      padding: bool = True, 
                      truncation: bool = True,
                      max_length: Optional[int] = None,
                      cache_key: Optional[str] = None) -> Dict[str, torch.Tensor]:
        """
        Tokenize a batch of texts and return tensors
        
        Args:
            texts: List of input texts
            padding: Whether to pad sequences to max length
            truncation: Whether to truncate sequences exceeding max_length
            max_length: Maximum sequence length
            cache_key: Optional key to cache the tensors
            
        Returns:
            Dictionary of tensors: input_ids, attention_mask, etc.
        """
        # Tokenize inputs
        tokenized = self.tokenizer(
            texts,
            padding=padding,
            truncation=truncation,
            max_length=max_length,
            return_tensors="pt"
        )
        
        # Move to device
        tensors = {k: v.to(self.device) for k, v in tokenized.items()}
        
        # Cache if requested
        if cache_key:
            self.cached_tensors[cache_key] = tensors
        
        return tensors
    
    def get_token_ids(self, text: str) -> List[int]:
        """Get token IDs for a text"""
        return self.tokenizer.encode(text, add_special_tokens=False)
    
    def get_token_names(self, token_ids: Union[List[int], torch.Tensor]) -> List[str]:
        """Get token names from token IDs"""
        if isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.tolist()
        return self.tokenizer.convert_ids_to_tokens(token_ids)
    
    def create_token_mask(self, 
                         input_ids: torch.Tensor, 
                         mask_tokens: List[int]) -> torch.Tensor:
        """Create a mask tensor for specified token IDs"""
        # Create a mask of zeros with same shape as input_ids
        mask = torch.zeros_like(input_ids, dtype=torch.bool)
        
        # Set True for positions with tokens to be masked
        for token_id in mask_tokens:
            mask = mask | (input_ids == token_id)
            
        return mask
    
    def apply_token_mask(self, 
                        input_ids: torch.Tensor, 
                        mask: torch.Tensor, 
                        replacement_id: Optional[int] = None) -> torch.Tensor:
        """
        Apply a mask to input_ids, replacing masked tokens
        
        Args:
            input_ids: Input token IDs
            mask: Boolean mask (True for positions to replace)
            replacement_id: Token ID to use for replacement (None for masking token)
            
        Returns:
            Tensor with masked tokens
        """
        if replacement_id is None:
            replacement_id = self.tokenizer.mask_token_id
            if replacement_id is None:
                # Fall back to PAD token if no mask token
                replacement_id = self.tokenizer.pad_token_id
        
        # Create copy of input_ids
        masked_ids = input_ids.clone()
        
        # Replace masked positions
        masked_ids[mask] = replacement_id
        
        return masked_ids
    
    def merge_token_tensors(self, 
                           tensor1: torch.Tensor, 
                           tensor2: torch.Tensor, 
                           merge_point: int = -1) -> torch.Tensor:
        """
        Merge two token tensors at a specific point
        
        Args:
            tensor1: First tensor
            tensor2: Second tensor
            merge_point: Position in tensor1 to merge tensor2 (-1 for end)
            
        Returns:
            Merged tensor
        """
        if merge_point < 0:
            merge_point = tensor1.size(1) + merge_point + 1
            
        # Split first tensor
        prefix = tensor1[:, :merge_point]
        suffix = tensor1[:, merge_point:]
        
        # Merge tensors
        merged = torch.cat([prefix, tensor2, suffix], dim=1)
        
        return merged
    
    def create_positional_tensor(self,
                                input_ids: torch.Tensor,
                                base_position: int = 0) -> torch.Tensor:
        """Create a tensor of position IDs"""
        batch_size, seq_len = input_ids.shape
        return torch.arange(base_position, base_position + seq_len, 
                           device=input_ids.device).unsqueeze(0).expand(batch_size, -1)
    
    def create_rotary_embeddings(self, 
                               input_ids: torch.Tensor, 
                               dim: int, 
                               base_freq: float = 10000.0) -> torch.Tensor:
        """Create rotary position embeddings (RoPE)"""
        batch_size, seq_len = input_ids.shape
        
        # Create position tensor
        pos = torch.arange(seq_len, device=input_ids.device).unsqueeze(1).float()
        
        # Create frequency tensor
        freqs = torch.pow(base_freq, -torch.arange(0, dim, 2, device=input_ids.device).float() / dim)
        
        # Compute embeddings
        emb = pos * freqs
        cos = torch.cos(emb).unsqueeze(0).expand(batch_size, -1, -1)
        sin = torch.sin(emb).unsqueeze(0).expand(batch_size, -1, -1)
        
        return cos, sin
    
    def apply_tensor_operation(self, 
                              tensor: torch.Tensor, 
                              operation: Callable[[torch.Tensor], torch.Tensor]) -> torch.Tensor:
        """Apply a custom operation to a tensor"""
        return operation(tensor)
    
    def get_subword_groups(self, text: str) -> List[List[Tuple[str, int]]]:
        """
        Group subword tokens by original words
        
        Returns:
            List of word groups, each containing subword tokens and their positions
        """
        # Tokenize text
        tokens = self.tokenizer.tokenize(text)
        ids = self.tokenizer.convert_tokens_to_ids(tokens)
        
        # Initialize groups
        groups = []
        current_group = []
        
        # Track position
        position = 0
        
        # Group subwords
        for token, token_id in zip(tokens, ids):
            # Check if this is a continuation subword
            is_continuation = token.startswith('##') or token.startswith('Ġ') or token.startswith('▁')
            
            if is_continuation and current_group:
                # Add to current group
                current_group.append((token, position))
            else:
                # Start a new group
                if current_group:
                    groups.append(current_group)
                current_group = [(token, position)]
            
            position += 1
        
        # Add the last group if any
        if current_group:
            groups.append(current_group)
            
        return groups
    
    def create_token_type_ids(self, 
                             input_ids: torch.Tensor, 
                             segment_indices: List[int]) -> torch.Tensor:
        """
        Create token type IDs tensor
        
        Args:
            input_ids: Input token IDs
            segment_indices: List of indices where segments start
            
        Returns:
            Tensor of token type IDs
        """
        batch_size, seq_len = input_ids.shape
        token_type_ids = torch.zeros_like(input_ids)
        
        # Set segment IDs
        for i, start_idx in enumerate(segment_indices[1:], 1):
            token_type_ids[:, start_idx:] = i
            
        return token_type_ids
    
    def batch_encode_plus(self, 
                         texts: List[str], 
                         text_pairs: Optional[List[str]] = None,
                         **kwargs) -> Dict[str, torch.Tensor]:
        """
        Enhanced batch encoding with optional text pairs
        
        Args:
            texts: List of input texts
            text_pairs: Optional list of paired texts
            **kwargs: Additional arguments for tokenizer
            
        Returns:
            Dictionary of tensors
        """
        # Tokenize inputs with pairs
        tokenized = self.tokenizer.batch_encode_plus(
            list(zip(texts, text_pairs)) if text_pairs else texts,
            return_tensors="pt",
            **kwargs
        )
        
        # Move to device
        tensors = {k: v.to(self.device) for k, v in tokenized.items()}
        
        return tensors
    
    def prepare_tensors_for_generation(self, 
                                     prompt: str, 
                                     max_length: int = 1024) -> Dict[str, torch.Tensor]:
        """
        Prepare tensors for text generation
        
        Args:
            prompt: The input prompt
            max_length: Maximum length for generation
            
        Returns:
            Dictionary with tensors required for generation
        """
        # Tokenize the prompt
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Create attention mask if not present
        if 'attention_mask' not in inputs:
            inputs['attention_mask'] = torch.ones_like(inputs['input_ids'])
            
        # Add position IDs
        inputs['position_ids'] = self.create_positional_tensor(inputs['input_ids'])
        
        return inputs
