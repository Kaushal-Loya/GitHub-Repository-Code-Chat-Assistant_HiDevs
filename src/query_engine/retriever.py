from typing import List
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

def retrieve_context(query: str, vector_store: VectorStore, top_k: int = 5) -> List[Document]:
    """
    Retrieves the top-k most relevant chunks for a given query.
    """
    results = vector_store.similarity_search(query, k=top_k)
    return results
