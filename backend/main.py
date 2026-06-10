from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base

import logging

from auth.router import router as auth_router
from documents.router import router as docs_router
from voice.router import router as voice_router
from observability.router import router as obs_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Voice RAG Chatbot API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For PoC, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database initialized.")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(docs_router, prefix="/documents", tags=["Documents"])
app.include_router(voice_router, prefix="/voice", tags=["Voice"])
app.include_router(obs_router, prefix="/admin/observability", tags=["Observability"])
