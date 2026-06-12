from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def format_docs(docs: List[Document]) -> str:
    """Formats retrieved documents into a readable context string."""
    formatted = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        formatted.append(f"--- File: {source} ---\n{doc.page_content}")
    return "\n\n".join(formatted)

def get_chat_prompt() -> ChatPromptTemplate:
    """Returns the chat prompt template."""
    system_template = """You are an expert code assistant with deep knowledge of software engineering.
You are currently answering questions about the following repository: {repo_summary}.
Always cite the file path when referencing specific code.
Answer based on the repository details above and the retrieved context below. If you cannot answer from context, say so.

[Retrieved Context]
{context}
"""
    return ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_query}")
    ])
