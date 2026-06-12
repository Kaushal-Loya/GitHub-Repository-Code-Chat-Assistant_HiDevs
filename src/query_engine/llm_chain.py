import os
from dataclasses import dataclass
from typing import List
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from .prompt_builder import get_chat_prompt, format_docs
from .retriever import retrieve_context

@dataclass
class SourceCitation:
    file_path: str
    url: str

def get_llm():
    """Initializes the Groq LLM."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    return ChatGroq(
        api_key=api_key,
        model_name="llama-3.1-8b-instant",
        temperature=0.1
    )

def generate_response(query: str, vector_store, history, repo_summary: str = "GitHub Repository"):
    """
    Executes the full RAG pipeline: retrieval -> prompt -> LLM.
    Returns the generated answer and a list of sources.
    """
    # Retrieve docs
    docs = retrieve_context(query, vector_store)
    
    # Extract sources
    sources = []
    seen = set()
    for d in docs:
        path = d.metadata.get("source", "Unknown")
        url = d.metadata.get("url", "")
        if path not in seen:
            seen.add(path)
            sources.append(SourceCitation(file_path=path, url=url))
            
    # Format context
    context_str = format_docs(docs)
    
    # Build prompt
    prompt = get_chat_prompt()
    
    # Run LLM
    llm = get_llm()
    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({
        "context": context_str,
        "repo_summary": repo_summary,
        "history": history,
        "user_query": query
    })
    
    return {
        "answer": response,
        "sources": sources
    }
