from typing import List, Optional
import os
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS

def build_vector_store(chunks: List[Document], embedder, repo_name: str, persist_dir: str = "./chroma_db") -> VectorStore:
    """Builds or updates the ChromaDB collection for the given repo."""
    collection_name = repo_name.replace("/", "_").replace(".", "_")
    
    try:
        store = Chroma.from_documents(
            documents=chunks,
            embedding=embedder,
            collection_name=collection_name,
            persist_directory=persist_dir
        )
        return store
    except Exception as e:
        print(f"ChromaDB failed: {e}. Falling back to FAISS.")
        return FAISS.from_documents(chunks, embedder)

def load_vector_store(repo_name: str, embedder, persist_dir: str = "./chroma_db") -> Optional[VectorStore]:
    """Loads an existing ChromaDB collection if present."""
    collection_name = repo_name.replace("/", "_").replace(".", "_")
    
    try:
        # Check if persist dir exists
        if os.path.exists(persist_dir):
            store = Chroma(
                collection_name=collection_name,
                embedding_function=embedder,
                persist_directory=persist_dir
            )
            # Simple check to see if it has documents
            if store._collection.count() > 0:
                return store
    except Exception:
        pass
    
    return None
