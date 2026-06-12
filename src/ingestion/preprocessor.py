from typing import List
from langchain_core.documents import Document
import hashlib
import re

def normalize_content(content: str) -> str:
    """Normalize whitespace and remove multiple blank lines."""
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()

def deduplicate_documents(documents: List[Document]) -> List[Document]:
    """Deduplicate documents based on content hash."""
    seen_hashes = set()
    unique_docs = []
    for doc in documents:
        content_hash = hashlib.md5(doc.page_content.encode('utf-8')).hexdigest()
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_docs.append(doc)
    return unique_docs

def preprocess_documents(documents: List[Document]) -> List[Document]:
    """Main preprocessing pipeline."""
    for doc in documents:
        doc.page_content = normalize_content(doc.page_content)
    
    return deduplicate_documents(documents)
