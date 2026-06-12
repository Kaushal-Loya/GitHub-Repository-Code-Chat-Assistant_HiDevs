from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    Language,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter as CodeTextSplitter

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

def get_language_from_ext(file_path: str) -> Language | None:
    ext = file_path.split('.')[-1].lower()
    mapping = {
        'py': Language.PYTHON,
        'js': Language.JS,
        'ts': Language.TS,
        'java': Language.JAVA,
        'go': Language.GO,
        'cpp': Language.CPP,
    }
    return mapping.get(ext)

def split_documents(documents: List[Document]) -> List[Document]:
    """Routes each document to the appropriate splitter and returns chunks."""
    chunks = []
    
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ])
    
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    for doc in documents:
        file_path = doc.metadata.get("source", "")
        lang = get_language_from_ext(file_path)
        
        if file_path.endswith('.md'):
            # First split markdown by headers
            md_chunks = markdown_splitter.split_text(doc.page_content)
            # Then recursively split large chunks
            for c in md_chunks:
                c.metadata.update(doc.metadata) # Merge original metadata
            chunks.extend(fallback_splitter.split_documents(md_chunks))
            
        elif lang:
            code_splitter = CodeTextSplitter.from_language(
                language=lang,
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP
            )
            code_chunks = code_splitter.split_documents([doc])
            chunks.extend(code_chunks)
            
        else:
            # Fallback
            chunks.extend(fallback_splitter.split_documents([doc]))

    return chunks
