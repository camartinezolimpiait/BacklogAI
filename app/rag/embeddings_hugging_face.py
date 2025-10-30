"""
Embedding Service Module
Handles document and query embeddings using sentence transformers
"""

import numpy as np
from typing import List, Union
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from loguru import logger


class EmbeddingHuggingFaceService:
    """
    Service for generating embeddings using Hugging Face transformers
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the embedding service using Hugging Face Transformers
        Args:
            model_name: Name of the Hugging Face model
        """
        logger.info(f"Initializing embedding service with Hugging Face model: {model_name}")
        from transformers import AutoTokenizer, AutoModel
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
        self.embedding_dim = self.model.config.hidden_size
        logger.info(f"Embedding dimension: {self.embedding_dim}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text using manual tokenization and model forward
        Args:
            text: Input text string
        Returns:
            Embedding vector as numpy array
        """
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use the mean pooling of the last hidden state
                last_hidden = outputs.last_hidden_state
                attention_mask = inputs["attention_mask"]
                mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
                sum_embeddings = torch.sum(last_hidden * mask_expanded, 1)
                sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                embedding = sum_embeddings / sum_mask
                embedding_np = embedding.squeeze().cpu().numpy()
            return embedding_np
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a batch of texts using manual tokenization and model forward
        Args:
            texts: List of text strings
        Returns:
            Array of embeddings
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            inputs = self.tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
                last_hidden = outputs.last_hidden_state
                attention_mask = inputs["attention_mask"]
                mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
                sum_embeddings = torch.sum(last_hidden * mask_expanded, 1)
                sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                embeddings = sum_embeddings / sum_mask
                embeddings_np = embeddings.cpu().numpy()
            return embeddings_np
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
