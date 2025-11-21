from typing import List
import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.VECTOR_API_KEY or settings.OPENAI_API_KEY,
            base_url=settings.VECTOR_BASE_URL
        )
        self.model = settings.VECTOR_MODEL

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text using the configured model.
        """
        if not text:
            return []
            
        try:
            text = text.replace("\n", " ")
            response = self.client.embeddings.create(
                input=[text],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.exception("Error generating embedding text")
            return []

embedding_service = EmbeddingService()
