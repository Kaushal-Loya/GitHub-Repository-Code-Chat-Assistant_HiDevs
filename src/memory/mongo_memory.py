import os
# pyrefly: ignore [missing-import]
from langchain_mongodb import MongoDBChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

def get_memory(session_id: str):
    """
    Returns the MongoDB-backed conversation memory.
    If MONGODB_URI is not set, returns a local in-memory list as a fallback.
    """
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        # Fallback to in-memory list for local testing without DB
        if "local_history" not in os.environ:
            os.environ["local_history"] = "{}"
        return []

    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=mongo_uri,
        database_name=os.getenv("MONGODB_DB_NAME", "github_chat_assistant"),
        collection_name="chat_histories",
    )

def clear_memory(session_id: str):
    """Clears the conversation history for a given session."""
    memory = get_memory(session_id)
    if hasattr(memory, "clear"):
        memory.clear()
