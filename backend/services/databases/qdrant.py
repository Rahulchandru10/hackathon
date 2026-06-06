import logging
from qdrant_client import QdrantClient as QC
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse
from backend.config import settings

logger = logging.getLogger(__name__)

class QdrantDBClient:
    def __init__(self):
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.client = None

    def connect(self):
        if not self.client:
            try:
                if settings.LOCAL_MODE:
                    # In-memory Qdrant — no server required
                    self.client = QC(":memory:")
                    logger.info("Using in-memory Qdrant (LOCAL_MODE).")
                else:
                    self.client = QC(host=self.host, port=self.port)
                    logger.info("Successfully connected to Qdrant server.")
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                self.client = None


    def create_collection_if_not_exists(self, collection_name: str, vector_size: int = 384):
        self.connect()
        if not self.client:
            logger.warning("Qdrant client not connected. Skipping collection creation.")
            return False
        
        try:
            self.client.get_collection(collection_name)
            logger.debug(f"Qdrant collection {collection_name} already exists.")
        except (UnexpectedResponse, Exception):
            logger.info(f"Creating Qdrant collection: {collection_name} with size {vector_size}")
            try:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info(f"Successfully created Qdrant collection: {collection_name}")
            except Exception as e:
                logger.error(f"Failed to create Qdrant collection {collection_name}: {e}")
                return False
        return True

    def upsert_vectors(self, collection_name: str, ids: list, vectors: list, payloads: list):
        self.connect()
        if not self.client:
            logger.warning("Qdrant client not connected. Skipping upsert.")
            return False
        
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=qmodels.Batch(
                    ids=ids,
                    vectors=vectors,
                    payloads=payloads
                )
            )
            logger.info(f"Successfully upserted {len(ids)} vectors to Qdrant collection {collection_name}.")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vectors in Qdrant: {e}")
            return False

    def search_similar(self, collection_name: str, query_vector: list, limit: int = 5, filter_dict: dict = None):
        self.connect()
        if not self.client:
            logger.warning("Qdrant client not connected. Skipping search.")
            return []
        
        q_filter = None
        if filter_dict:
            conditions = []
            for key, val in filter_dict.items():
                conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=val)
                    )
                )
            q_filter = qmodels.Filter(must=conditions)

        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=q_filter
            )
            return [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in results]
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

qdrant_client = QdrantDBClient()
