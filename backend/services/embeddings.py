import os
import logging
from typing import List
from backend.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self._model = None

    def _load_model(self):
        if self._model is None:
            # Import sentence_transformers inside function to defer heavy imports
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {self.model_name}...")
            # Configure cache directory
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".model_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            self._model = SentenceTransformer(self.model_name, cache_folder=cache_dir)
            logger.info("Embedding model loaded successfully.")

    def get_embedding(self, text: str) -> List[float]:
        self._load_model()
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._load_model()
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()

embedding_service = EmbeddingService()
