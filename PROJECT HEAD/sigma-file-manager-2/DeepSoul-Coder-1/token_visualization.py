"""
Token attention and tensor visualization utilities for DeepSeek-Coder
"""
import numpy as np
import torch
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import List, Dict, Optional, Union, Tuple, Any
from transformers import PreTrainedTokenizer, PreTrainedModel
import io
import base64
from PIL import Image

class TokenVisualizer:
    """Visualize token attention and embeddings"""
    
    def __init__(self, tokenizer: PreTrainedTokenizer, model: Optional[PreTrainedModel] = None):
        """Initialize with tokenizer and optional model"""
        self.tokenizer = tokenizer
        self.model = model
        
    def plot_attention_heads(self, 
                             query: str, 
                             layer_idx: int = -1,
                             head_indices: Optional[List[int]] = None,
                             output_filename: Optional[str] = None) -> Union[str, None]:
        """
        Plot attention patterns from different attention heads
        
        Args:
            query: Input text
            layer_idx: Index of transformer layer (-1 for last layer)
            head_indices: List of attention head indices to plot (None for all)
            output_filename: Optional filename to save the plot
            
        Returns:
            Base64 encoded image if no output_filename is provided, None otherwise
        """
        if self.model is None:
            raise ValueError("Model is required for attention visualization")
            
        # Tokenize input and get attention
        inputs = self.tokenizer(query, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        # Get output with attention weights
        with torch.no_grad():
            outputs = self.model(**inputs, output_attentions=True)
            
        # Get attention weights
        attentions = outputs.attentions  # Tuple of attention weights for each layer
        if layer_idx < 0:
            layer_idx = len(attentions) + layer_idx
        attention_layer = attentions[layer_idx].detach().cpu()  # Shape: [batch, num_heads, seq_len, seq_len]
        
        # Get tokens
        tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
        
        # Determine which heads to plot
        num_heads = attention_layer.size(1)
        if head_indices is None:
            head_indices = list(range(min(4, num_heads)))  # Default to first 4 heads
        
        # Create figure
        fig, axes = plt.subplots(1, len(head_indices), figsize=(4*len(head_indices), 4), dpi=100)
        if len(head_indices) == 1:
            axes = [axes]  # Make it indexable for a single head
        
        # Plot each head
        for i, head_idx in enumerate(head_indices):
            ax = axes[i]
            att_matrix = attention_layer[0, head_idx].numpy()
            
            # Plot attention matrix
            im = ax.imshow(att_matrix, cmap="viridis")
            
            # Set labels
            ax.set_title(f"Head {head_idx}")
            ax.set_xticks(np.arange(len(tokens)))
            ax.set_yticks(np.arange(len(tokens)))
            ax.set_xticklabels(tokens, rotation=90, fontsize=8)
            ax.set_yticklabels(tokens, fontsize=8)
            
            # Format tick labels for long sequences
            if len(tokens) > 10:
                ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
                ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
                
            # Add colorbar
            plt.colorbar(im, ax=ax)
        
        plt.tight_layout()
        
        # Return or save figure
        if output_filename:
            plt.savefig(output_filename, bbox_inches='tight')
            plt.close(fig)
            return None
        else:
            # Return base64 encoded image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{img_str}"
    
    def get_token_importance(self, 
                            query: str, 
                            output_filename: Optional[str] = None) -> Union[Dict[str, float], str, None]:
        """
        Calculate and visualize token importance
        
        Args:
            query: Input text
            output_filename: Optional filename to save the visualization
            
        Returns:
            Dictionary mapping tokens to importance scores if no output_filename,
            Base64 encoded image if output_filename is None but visualization is requested,
            None if output_filename is provided
        """
        if self.model is None:
            raise ValueError("Model is required for token importance calculation")
        
        # Tokenize input
        inputs = self.tokenizer(query, return_tensors="pt")
        input_ids = inputs['input_ids'].to(self.model.device)
        
        # Calculate token importance using gradients
        input_ids.requires_grad_(True)
        
        # Forward pass
        outputs = self.model(input_ids=input_ids)
        logits = outputs.logits
        
        # Backward pass to get gradient-based importance
        # Using the prediction loss of the next token as the objective
        prediction_logits = logits[:, :-1]  # Exclude last position
        target_ids = input_ids[:, 1:]  # Shift right to get next token
        
        loss = torch.nn.functional.cross_entropy(
            prediction_logits.reshape(-1, prediction_logits.size(-1)),
            target_ids.reshape(-1)
        )
        
        loss.backward()
        
        # Calculate importance as gradient magnitude
        importance = input_ids.grad.abs().sum(dim=-1)
        importance = importance[0].detach().cpu().numpy()
        
        # Get tokens
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        
        # Create importance dictionary
        importance_dict = {token: float(imp) for token, imp in zip(tokens, importance)}
        
        if output_filename is not None or output_filename is None:
            # Create visualization
            plt.figure(figsize=(12, 6))
            
            # Plot importance
            bars = plt.bar(range(len(tokens)), importance)
            plt.xlabel("Position")
            plt.ylabel("Importance Score")
            plt.title("Token Importance")
            plt.xticks(range(len(tokens)), tokens, rotation=90)
            
            # Color-code by importance (normalize by max)
            max_imp = importance.max()
            for i, bar in enumerate(bars):
                bar.set_color(plt.cm.viridis(importance[i] / max_imp))
                
            plt.tight_layout()
            
            # Return or save figure
            if output_filename:
                plt.savefig(output_filename, bbox_inches='tight')
                plt.close()
                return None
            else:
                # Return base64 encoded image
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                plt.close()
                buf.seek(0)
                img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
                return f"data:image/png;base64,{img_str}"
        
        return importance_dict
    
    def visualize_token_embeddings(self, 
                                  tokens: List[str], 
                                  method: str = 'pca', 
                                  output_filename: Optional[str] = None) -> Union[str, None]:
        """
        Visualize token embeddings in 2D or 3D space
        
        Args:
            tokens: List of tokens or words to visualize
            method: Dimensionality reduction method ('pca' or 'tsne')
            output_filename: Optional filename to save the visualization
            
        Returns:
            Base64 encoded image if no output_filename is provided, None otherwise
        """
        if self.model is None:
            raise ValueError("Model is required for embedding visualization")
            
        # Get embeddings for each token
        embeddings = []
        for token in tokens:
            # Tokenize and get embedding
            inputs = self.tokenizer(token, return_tensors="pt")
            input_ids = inputs['input_ids'].to(self.model.device)
            
            with torch.no_grad():
                # Get embeddings from first layer
                embedding = self.model.get_input_embeddings()(input_ids)
                # Use the first token embedding if multiple tokens
                embedding = embedding[0, 0].detach().cpu().numpy()
                embeddings.append(embedding)
                
        # Convert to numpy array
        embeddings = np.array(embeddings)
        
        # Apply dimensionality reduction
        if method == 'pca':
            from sklearn.decomposition import PCA
            if len(embeddings) < 3:
                n_components = len(embeddings)
            else:
                n_components = 3 if len(tokens) > 2 else 2
                
            pca = PCA(n_components=n_components)
            reduced = pca.fit_transform(embeddings)
        else:  # Use t-SNE
            from sklearn.manifold import TSNE
            tsne = TSNE(n_components=2, perplexity=min(30, max(5, len(embeddings) / 5)), random_state=42)
            reduced = tsne.fit_transform(embeddings)
        
        # Create visualization
        fig = plt.figure(figsize=(10, 8))
        
        if reduced.shape[1] == 3 and len(tokens) > 2:
            # 3D plot
            ax = fig.add_subplot(111, projection='3d')
            ax.scatter(reduced[:, 0], reduced[:, 1], reduced[:, 2], s=100)
            
            # Add labels
            for i, token in enumerate(tokens):
                ax.text(reduced[i, 0], reduced[i, 1], reduced[i, 2], token)
                
            ax.set_title(f'Token Embeddings ({method.upper()})')
            
        else:
            # 2D plot
            plt.scatter(reduced[:, 0], reduced[:, 1], s=100)
            
            # Add labels
            for i, token in enumerate(tokens):
                plt.annotate(token, (reduced[i, 0], reduced[i, 1]))
                
            plt.title(f'Token Embeddings ({method.upper()})')
            
        plt.tight_layout()
        
        # Return or save figure
        if output_filename:
            plt.savefig(output_filename, bbox_inches='tight')
            plt.close(fig)
            return None
        else:
            # Return base64 encoded image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{img_str}"
