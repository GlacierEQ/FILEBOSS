"""
Memory-Efficient Generation - Utilities for memory-efficient text generation
"""
import gc
import torch
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from transformers import PreTrainedModel, PreTrainedTokenizer

from .memory_manager import get_memory_manager
from implementation.oom_protected_execution import oom_protected, MemoryEfficientContext

logger = logging.getLogger("DeepSoul-MemoryEfficientGeneration")

class MemoryEfficientGenerator:
    """
    Memory-efficient text generation with OOM protection
    """
    
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer):
        """
        Initialize the memory-efficient generator
        
        Args:
            model: Pre-trained model
            tokenizer: Tokenizer for the model
        """
        self.model = model
        self.tokenizer = tokenizer
        self.memory_manager = get_memory_manager()
        self.device = next(model.parameters()).device
    
    @oom_protected(retry_on_cpu=True)
    def generate(self, 
                prompt: str, 
                max_new_tokens: int = 256,
                top_p: float = 0.95,
                temperature: float = 0.7,
                **generation_kwargs) -> str:
        """
        Generate text with OOM protection
        
        Args:
            prompt: Text prompt
            max_new_tokens: Maximum number of tokens to generate
            top_p: Top-p sampling parameter
            temperature: Sampling temperature
            **generation_kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        # Move to eval mode
        self.model.eval()
        
        # Check if batch size is provided, if not set to 1
        batch_size = generation_kwargs.get("batch_size", 1)
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Check memory before generation
        if self.device.type == "cuda":
            available_memory = self._check_available_memory()
            logger.info(f"Available GPU memory before generation: {available_memory:.2f} MB")
            
            # Adjust max_new_tokens if memory is low
            if available_memory < 500 and max_new_tokens > 128:
                old_max_tokens = max_new_tokens
                max_new_tokens = min(max_new_tokens, 128)  # Reduce token count
                logger.warning(f"Low memory detected. Reducing max_new_tokens from {old_max_tokens} to {max_new_tokens}")
        
        # Generate text with memory protection
        with torch.no_grad(), MemoryEfficientContext():
            generation_kwargs.update({
                "max_new_tokens": max_new_tokens,
                "top_p": top_p,
                "temperature": temperature,
                "do_sample": temperature > 0.0
            })
            
            outputs = self.model.generate(
                **inputs,
                **generation_kwargs
            )
            
            # Decode and return
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return generated_text
    
    def stream_generate(self, 
                       prompt: str, 
                       max_new_tokens: int = 256,
                       top_p: float = 0.95,
                       temperature: float = 0.7,
                       **generation_kwargs) -> List[str]:
        """
        Generate text in a streaming fashion with OOM protection
        
        Args:
            prompt: Text prompt
            max_new_tokens: Maximum number of tokens to generate
            top_p: Top-p sampling parameter
            temperature: Sampling temperature
            **generation_kwargs: Additional generation parameters
            
        Yields:
            Chunks of generated text
        """
        # Move to eval mode
        self.model.eval()
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Check if we need to switch to CPU for very low memory
        if self.device.type == "cuda":
            available_memory = self._check_available_memory()
            if available_memory < 200:  # Very low memory
                logger.warning(f"Very low GPU memory ({available_memory:.2f} MB). Using CPU for generation.")
                self.model = self.model.cpu()
                inputs = {k: v.cpu() for k, v in inputs.items()}
            elif available_memory < 500:  # Low memory
                # Reduce token count
                old_max_tokens = max_new_tokens
                max_new_tokens = min(max_new_tokens, 128)
                logger.warning(f"Low memory detected. Reducing max_new_tokens from {old_max_tokens} to {max_new_tokens}")
        
        # Set up streaming parameters
        generation_kwargs.update({
            "max_new_tokens": max_new_tokens,
            "top_p": top_p,
            "temperature": temperature,
            "do_sample": temperature > 0.0,
            "streamer": None  # Could use transformers.TextStreamer if available
        })
        
        try:
            # Set up batched generation for streaming
            with torch.no_grad(), MemoryEfficientContext():
                # Start generation
                generated_ids = inputs["input_ids"]
                past_key_values = None
                
                # Get input length
                input_length = generated_ids.shape[1]
                
                # Track generated text for yielding new tokens
                generated_text = ""
                
                # Generate text token by token
                for _ in range(max_new_tokens):
                    # Forward pass with past key values for efficiency
                    outputs = self.model(
                        input_ids=generated_ids[:, -1:] if past_key_values is not None else generated_ids,
                        past_key_values=past_key_values,
                        use_cache=True
                    )
                    
                    # Get logits and past key values
                    logits = outputs.logits[:, -1, :]
                    past_key_values = outputs.past_key_values
                    
                    # Apply temperature and top-p sampling
                    if temperature > 0:
                        logits = logits / temperature
                        
                    # Apply top-p sampling
                    if top_p < 1.0:
                        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                        cumulative_probs = torch.cumsum(torch.nn.functional.softmax(sorted_logits, dim=-1), dim=-1)
                        
                        # Remove tokens with cumulative probability above the threshold
                        sorted_indices_to_remove = cumulative_probs > top_p
                        # Shift the indices to the right to keep also the first token above the threshold
                        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                        sorted_indices_to_remove[..., 0] = 0
                        
                        indices_to_remove = sorted_indices[sorted_indices_to_remove]
                        logits[:, indices_to_remove] = float('-inf')
                    
                    # Sample from the distribution
                    probs = torch.nn.functional.softmax(logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                    
                    # Check for EOS token
                    if next_token.item() == self.tokenizer.eos_token_id:
                        break
                    
                    # Add to generated ids
                    generated_ids = torch.cat([generated_ids, next_token], dim=-1)
                    
                    # Get new text
                    new_text = self.tokenizer.decode(generated_ids[0, input_length:], skip_special_tokens=True)
                    
                    # Only yield if we have new tokens
                    if len(new_text) > len(generated_text):
                        # Get the new part only
                        yield new_text[len(generated_text):]
                        generated_text = new_text
                
                # Return any remaining text
                final_text = self.tokenizer.decode(generated_ids[0, input_length:], skip_special_tokens=True)
                if final_text != generated_text:
                    yield final_text[len(generated_text):]
        
        finally:
            # Move model back to original device if needed
            if self.model.device != self.device:
                self.model = self.model.to(self.device)
    
    def _check_available_memory(self) -> float:
        """
        Check available GPU memory in MB
        
        Returns:
            Available memory in MB
        """
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            total_memory = torch.cuda.get_device_properties(self.device).total_memory
            allocated_memory = torch.cuda.memory_allocated(self.device)
            available_memory = (total_memory - allocated_memory) / (1024 * 1024)  # Convert to MB
            return available_memory
        return 0.0
    
    def batch_generate(self, 
                     prompts: List[str], 
                     batch_size: Optional[int] = None,
                     **generation_kwargs) -> List[str]:
        """
        Generate text for multiple prompts with automatic batching based on memory
        
        Args:
            prompts: List of text prompts
            batch_size: Batch size (if None, determined automatically)
            **generation_kwargs: Additional generation parameters
            
        Returns:
            List of generated texts
        """
        if not prompts:
            return []
        
        # Determine optimal batch size if not specified
        if batch_size is None:
            if self.device.type == "cuda":
                available_memory = self._check_available_memory()
                estimated_per_sample = 200  # Rough estimate MB per sample
                memory_based_batch = max(1, int(available_memory / estimated_per_sample))
                batch_size = min(memory_based_batch, len(prompts))
            else:
                # On CPU, use smaller batches
                batch_size = min(4, len(prompts))
        
        logger.info(f"Using batch size {batch_size} for {len(prompts)} prompts")
        results = []
        
        # Process in batches
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i:i+batch_size]
            
            try:
                # Tokenize batch
                batch_inputs = self.tokenizer(
                    batch_prompts, 
                    return_tensors="pt", 
                    padding=True
                ).to(self.device)
                
                # Generate
                with torch.no_grad(), MemoryEfficientContext():
                    outputs = self.model.generate(
                        **batch_inputs,
                        **generation_kwargs
                    )
                    
                    # Decode outputs
                    batch_results = self.tokenizer.batch_decode(
                        outputs, 
                        skip_special_tokens=True
                    )
                    
                    results.extend(batch_results)
                    
            except RuntimeError as e:
                if "CUDA out of memory" in str(e) and batch_size > 1:
                    # Reduce batch size and retry
                    logger.warning(f"CUDA OOM with batch size {batch_size}. Falling back to sequential processing.")
                    
                    # Clear memory
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    gc.collect()
                    
                    # Process individually
                    for prompt in batch_prompts:
                        try:
                            result = self.generate(prompt, **generation_kwargs)
                            results.append(result)
                        except Exception as inner_e:
                            logger.error(f"Error generating text: {str(inner_e)}")
                            results.append(f"Error: {str(inner_e)}")
                else:
                    # Other error, re-raise
                    raise
        
        return results

# Convenience function to create a memory-efficient generator
def create_generator(model, tokenizer) -> MemoryEfficientGenerator:
    """
    Create a memory-efficient generator
    
    Args:
        model: Model to use for generation
        tokenizer: Tokenizer for the model
        
    Returns:
        MemoryEfficientGenerator instance
    """
    return MemoryEfficientGenerator(model, tokenizer)
