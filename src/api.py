from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time
import asyncio

app = FastAPI(title="Enterprise AI Knowledge Brain API")

# Allow Next.js frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Source(BaseModel):
    name: str
    snippet: str

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    reasoning: List[str]
    sources: List[dict]

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Receives a query from the Next.js frontend.
    TODO: Wire this up to src.agents.query.py once the LangGraph reasoning engine is built.
    For now, it returns a placeholder response so the frontend integration is complete.
    """
    # Simulate processing time for graph traversal
    await asyncio.sleep(1.5)
    
    return ChatResponse(
        answer=f"You asked: '{request.query}'. \n\nThe LangGraph and Neo4j backend is currently under construction. Once we build `src/agents/query.py`, this response will contain real data extracted from your graph.",
        reasoning=[
            "Received request at FastAPI /chat endpoint",
            "Checking Neo4j connection (Pending)",
            "Checking Groq API connection (Pending)",
            "Returning API connection success to frontend."
        ],
        sources=[
            {"name": "System Architecture", "snippet": "Frontend is wired to FastAPI correctly."}
        ]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
