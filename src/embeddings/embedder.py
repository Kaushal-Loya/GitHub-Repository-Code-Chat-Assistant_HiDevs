from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings

@lru_cache(maxsize=1)
def get_embedder() -> HuggingFaceEmbeddings:
    """
    Returns a cached HuggingFace embeddings model instance.
    Uses sentence-transformers/all-MiniLM-L6-v2.
    """
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
