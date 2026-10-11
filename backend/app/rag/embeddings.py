import os
import numpy as np
from fastembed import TextEmbedding

# Default model for generating embeddings
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


# adapter around FastEmbed's TextEmbedding to provide a consistent interface for generating embeddings.
class LocalEmbeddingModel:
    """Generate document and query embeddings locally."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = TextEmbedding(
            model_name=model_name,
            cache_dir=os.getenv("FASTEMBED_CACHE_PATH"),
            threads=int(os.getenv("EMBEDDING_THREADS", "1")),
        )

    # Instead of allowing every module to call the model directly,
    # we provide a method to embed documents. This ensures that all embeddings are
    # generated in a consistent manner and allows for additional validation or preprocessing if needed.
    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts or any(
            not isinstance(text, str) or not text.strip() for text in texts
        ):
            raise ValueError("Documents must contain non-empty text")

        vectors = list(self._model.passage_embed(texts, batch_size=4))
        return self._validate_vectors(
            vectors,
            expected_count=len(texts),
        )

    # Similarly, we provide a method to embed queries. This ensures that query embeddings are generated
    # consistently and allows for validation or preprocessing.
    def embed_query(self, query: str) -> np.ndarray:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query cannot be empty")

        vectors = list(self._model.query_embed(query))
        return self._validate_vectors(
            vectors,
            expected_count=1,
        )[0]

    @staticmethod
    def _validate_vectors(
        vectors: list[np.ndarray],
        expected_count: int,
    ) -> np.ndarray:
        array = np.asarray(vectors, dtype=np.float32)

        if array.ndim != 2 or array.shape[0] != expected_count or array.shape[1] == 0:
            raise ValueError("Embedding model returned invalid dimensions")

        if not np.isfinite(array).all():
            raise ValueError("Embedding model returned non-finite values")

        if np.any(np.linalg.norm(array, axis=1) == 0):
            raise ValueError("Embedding model returned zero vectors")

        return array
