"""Image utilities for generating and comparing image embeddings."""

import numpy as np
import requests
from PIL import Image
from io import BytesIO
from typing import Optional
import open_clip
import torch


class ImageEmbeddingGenerator:
    """Generate image embeddings using CLIP model."""
    
    def __init__(self, model_name: str = 'ViT-B-32', pretrained: str = 'openai'):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: CLIP model architecture
            pretrained: Pretrained weights to use
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained=pretrained,
            device=self.device
        )
        self.model.eval()
    
    def download_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """
        Download an image from a URL.
        
        Args:
            url: Image URL
            timeout: Request timeout in seconds
            
        Returns:
            PIL Image or None if download fails
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return img.convert('RGB')  # Ensure RGB format
        except Exception as e:
            print(f"Failed to download image from {url}: {e}")
            return None
    
    def generate_embedding(self, image: Image.Image) -> np.ndarray:
        """
        Generate CLIP embedding for an image.
        
        Args:
            image: PIL Image
            
        Returns:
            Numpy array of image embedding
        """
        with torch.no_grad():
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            image_features = self.model.encode_image(image_input)
            
            # Normalize embedding
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embedding = image_features.cpu().numpy().flatten()
            
        return embedding.astype(np.float32)
    
    def generate_embedding_from_url(self, url: str) -> Optional[np.ndarray]:
        """
        Download an image and generate its embedding.
        
        Args:
            url: Image URL
            
        Returns:
            Numpy array of image embedding or None if failed
        """
        image = self.download_image(url)
        if image is None:
            return None
        return self.generate_embedding(image)


# Global instance (lazy loaded)
_embedding_generator: Optional[ImageEmbeddingGenerator] = None


def get_embedding_generator() -> ImageEmbeddingGenerator:
    """Get or create the global embedding generator instance."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = ImageEmbeddingGenerator()
    return _embedding_generator


def generate_image_embedding(image_url: str) -> Optional[np.ndarray]:
    """
    Generate an image embedding from a URL.
    
    This is a convenience function that uses the global embedding generator.
    
    Args:
        image_url: URL of the image
        
    Returns:
        Numpy array of image embedding or None if failed
    """
    generator = get_embedding_generator()
    return generator.generate_embedding_from_url(image_url)


def calculate_image_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two image embeddings.
    
    Args:
        embedding1: First image embedding
        embedding2: Second image embedding
        
    Returns:
        Similarity score (0-1, where 1 is most similar)
    """
    if embedding1 is None or embedding2 is None:
        return 0.0
    
    # Ensure embeddings are normalized
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    embedding1_norm = embedding1 / norm1
    embedding2_norm = embedding2 / norm2
    
    # Cosine similarity
    similarity = np.dot(embedding1_norm, embedding2_norm)
    
    # Clip to [0, 1] range (cosine similarity is [-1, 1])
    similarity = (similarity + 1) / 2
    
    return float(similarity)


def batch_generate_embeddings(image_urls: list[str]) -> list[Optional[np.ndarray]]:
    """
    Generate embeddings for multiple images.
    
    Args:
        image_urls: List of image URLs
        
    Returns:
        List of embeddings (same length as input, None for failed downloads)
    """
    generator = get_embedding_generator()
    embeddings = []
    
    for url in image_urls:
        embedding = generator.generate_embedding_from_url(url)
        embeddings.append(embedding)
    
    return embeddings

