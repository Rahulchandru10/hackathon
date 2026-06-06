import uuid
from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.embeddings import embedding_service
import numpy as np

class DuplicateDetectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("duplicate_detection")
        self.similarity_threshold = 0.85

    async def run(self, state: ScreeningState) -> dict:
        raw_articles = state["raw_articles"]
        if not raw_articles:
            return {"deduplicated_articles": []}

        # Extract texts (title + snippet) to encode
        texts = [
            f"{art.get('title', '')} {art.get('snippet', '')}" 
            for art in raw_articles
        ]
        
        # Calculate embeddings
        try:
            embeddings = embedding_service.get_embeddings(texts)
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings for duplicate detection: {e}. Falling back to exact title matching.")
            # Fallback simple title matching:
            seen_titles = {}
            dedup = []
            for art in raw_articles:
                t = art.get("title", "").strip().lower()
                if t not in seen_titles:
                    cluster_id = str(uuid.uuid4())
                    art["cluster_id"] = cluster_id
                    seen_titles[t] = cluster_id
                    dedup.append(art)
            return {"deduplicated_articles": dedup}

        # Cluster using cosine similarity matrix
        num_items = len(raw_articles)
        visited = [False] * num_items
        clustered_articles = []
        
        # Convert embeddings to numpy array
        emb_matrix = np.array(embeddings)
        
        for i in range(num_items):
            if visited[i]:
                continue
                
            cluster_id = str(uuid.uuid4())
            primary_art = raw_articles[i]
            primary_art["cluster_id"] = cluster_id
            clustered_articles.append(primary_art)
            visited[i] = True
            
            # Find similar articles
            for j in range(i + 1, num_items):
                if visited[j]:
                    continue
                
                # Compute cosine similarity
                dot_product = np.dot(emb_matrix[i], emb_matrix[j])
                norm_i = np.linalg.norm(emb_matrix[i])
                norm_j = np.linalg.norm(emb_matrix[j])
                similarity = dot_product / (norm_i * norm_j) if norm_i > 0 and norm_j > 0 else 0.0
                
                if similarity >= self.similarity_threshold:
                    raw_articles[j]["cluster_id"] = cluster_id
                    visited[j] = True
                    # If this duplicate has a higher authority source, we could swap the primary,
                    # but for now we just group them under the same cluster_id

        self.logger.info(f"Deduplicated {num_items} raw articles into {len(clustered_articles)} unique clusters.")
        return {"deduplicated_articles": clustered_articles}
