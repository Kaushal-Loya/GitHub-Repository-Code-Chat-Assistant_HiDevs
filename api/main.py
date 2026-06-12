from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib
from dotenv import load_dotenv
from typing import Optional
from src.ingestion.github_loader import load_repository
from src.ingestion.preprocessor import preprocess_documents
from src.chunking.splitter import split_documents
from src.embeddings.embedder import get_embedder
from src.vector_store.store import build_vector_store, load_vector_store
from src.query_engine.llm_chain import generate_response
from src.memory.mongo_memory import get_memory, clear_memory
from src.utils.github_utils import parse_github_url

load_dotenv()

app = FastAPI(title="GitHub Repo Chat API")

# Setup CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory state (in production, use Redis or DB)
STATE = {
    "vector_store": None,
    "repo_metadata": {}
}

class IngestRequest(BaseModel):
    url: str
    token: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    session_id: str

@app.post("/api/ingest")
async def ingest_repo(req: IngestRequest):
    try:
        repo_name = parse_github_url(req.url)
        docs = load_repository(req.url, req.token)
        clean_docs = preprocess_documents(docs)
        chunks = split_documents(clean_docs)
        
        embedder = get_embedder()
        vector_store = build_vector_store(chunks, embedder, repo_name)
        
        STATE["vector_store"] = vector_store
        
        languages = set()
        folders = set()
        readme_content = ""
        for doc in clean_docs:
            src = doc.metadata.get("source", "")
            if "/" in src:
                folders.add(src.split("/")[0])
            if "." in src:
                languages.add(src.split(".")[-1])
            if src.lower() == "readme.md":
                readme_content = doc.page_content
                
        STATE["repo_metadata"] = {
            "file_count": len(clean_docs),
            "chunk_count": len(chunks),
            "languages": list(languages),
            "root_folders": list(folders),
            "readme": readme_content[:1500], # Include first 1500 chars of README
            "repo_name": repo_name
        }
        
        session_id = hashlib.md5(f"user_{req.url}".encode()).hexdigest()
        
        return {
            "status": "success",
            "session_id": session_id,
            "metadata": STATE["repo_metadata"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not STATE["vector_store"]:
        raise HTTPException(status_code=400, detail="No repository ingested yet.")
        
    try:
        memory = get_memory(req.session_id)
        messages = memory if isinstance(memory, list) else memory.messages
        
        if hasattr(memory, "add_user_message"):
            memory.add_user_message(req.query)
        elif isinstance(memory, list):
            memory.append({"type": "human", "content": req.query})
            
        history = [m for m in messages if getattr(m, "type", "") != "system"]
        
        repo_name = STATE["repo_metadata"].get("repo_name", "the repository")
        root_folders = STATE["repo_metadata"].get("root_folders", [])
        readme = STATE["repo_metadata"].get("readme", "")
        
        summary = f"{repo_name}"
        if root_folders:
            summary += f" (Root folders: {', '.join(root_folders)})"
        if readme:
            summary += f"\n\n--- README Summary ---\n{readme}\n----------------------"
            
        result = generate_response(
            req.query, 
            STATE["vector_store"], 
            history, 
            summary
        )
        
        if hasattr(memory, "add_ai_message"):
            memory.add_ai_message(result["answer"])
        elif isinstance(memory, list):
            memory.append({"type": "ai", "content": result["answer"]})
            
        return {
            "answer": result["answer"],
            "sources": [{"file_path": s.file_path, "url": s.url} for s in result["sources"]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clear")
async def clear_chat(session_id: str):
    clear_memory(session_id)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
