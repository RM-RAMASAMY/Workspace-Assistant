from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import base64
from typing import Optional

from .stt_client import transcribe_audio
from .tts_client import synthesize_speech
from retrieval.query_processor import process_query
from retrieval.hybrid_search import perform_hybrid_search
from retrieval.reranker import rerank_results
from generation.llm_client import OllamaClient
from generation.prompt_templates import SYSTEM_PROMPT, format_context
from generation.streaming import sentence_streamer
from auth.dependencies import get_current_user

# Note: WebSocket auth requires passing token via query param or initial message
router = APIRouter()
llm_client = OllamaClient()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # In a real app, perform auth using a token sent in the first message.
    # We will assume a default access level for the demo if auth not provided over WS
    access_level = 2 # INTERNAL
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            
            # Step 1: STT
            await websocket.send_json({"type": "status", "data": "Transcribing..."})
            transcription = await transcribe_audio(data)
            await websocket.send_json({"type": "transcription", "data": transcription})
            
            # Step 2: Query Processing
            await websocket.send_json({"type": "status", "data": "Retrieving context..."})
            processed = process_query(transcription, [])
            
            # Step 3: Retrieval
            candidates = perform_hybrid_search(processed["rewritten"], access_level=access_level)
            top_chunks = rerank_results(processed["rewritten"], candidates)
            
            # Send citations to client
            citations = [{"id": c["id"], "text": c["text"], "title": c["metadata"].get("title")} for c in top_chunks]
            await websocket.send_json({"type": "citations", "data": citations})
            
            # Step 4: LLM + TTS Streaming
            await websocket.send_json({"type": "status", "data": "Generating response..."})
            context_str = format_context(top_chunks)
            token_generator = llm_client.generate_stream(processed["rewritten"], SYSTEM_PROMPT.format(context=context_str))
            
            async for sentence in sentence_streamer(token_generator):
                await websocket.send_json({"type": "text", "data": sentence})
                audio_bytes = await synthesize_speech(sentence)
                if audio_bytes:
                    await websocket.send_json({"type": "audio", "data": base64.b64encode(audio_bytes).decode('utf-8')})
                    
            await websocket.send_json({"type": "status", "data": "Done"})
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "data": str(e)})
