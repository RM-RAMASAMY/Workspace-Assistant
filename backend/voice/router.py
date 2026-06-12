import asyncio
import base64
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketDisconnect as StarletteWebSocketDisconnect

from .stt_client import transcribe_audio
from .tts_client import synthesize_speech
from retrieval.query_processor import process_query
from retrieval.hybrid_search import perform_hybrid_search
from retrieval.reranker import rerank_results
from generation.llm_client import OllamaClient
from generation.prompt_templates import SYSTEM_PROMPT, CONVERSATIONAL_PROMPT, format_context
from generation.streaming import sentence_streamer
from generation.citations import strip_citation_markers
from generation.response_utils import should_attach_citations, build_citation_payload

router = APIRouter()
llm_client = OllamaClient()

DISCONNECT_ERRORS = (WebSocketDisconnect, StarletteWebSocketDisconnect, RuntimeError)


async def safe_send_json(websocket: WebSocket, payload: dict) -> bool:
    try:
        await websocket.send_json(payload)
        return True
    except DISCONNECT_ERRORS:
        return False


async def _tts_worker(websocket: WebSocket, queue: asyncio.Queue) -> None:
    """Synthesize and send audio strictly in sentence order."""
    while True:
        sentence = await queue.get()
        if sentence is None:
            break
        try:
            audio_bytes = await synthesize_speech(sentence)
            if audio_bytes:
                await safe_send_json(websocket, {
                    "type": "audio",
                    "data": base64.b64encode(audio_bytes).decode("utf-8"),
                })
        except Exception:
            logging.exception("TTS worker failed")
        finally:
            queue.task_done()


async def _process_voice_turn(websocket: WebSocket, data: bytes, access_level: int) -> None:
    try:
        if not await safe_send_json(websocket, {"type": "status", "data": "Transcribing..."}):
            return

        transcription = (await transcribe_audio(data) or "").strip()

        if not transcription:
            await safe_send_json(websocket, {
                "type": "error",
                "data": "No speech detected. Hold the button, speak, then release.",
            })
            return

        if not await safe_send_json(websocket, {"type": "transcription", "data": transcription}):
            return

        processed = process_query(transcription, [])
        top_chunks = []

        if processed["intent"] == "conversational":
            if not await safe_send_json(websocket, {"type": "status", "data": "Generating response..."}):
                return
            system_prompt = CONVERSATIONAL_PROMPT
        else:
            if not await safe_send_json(websocket, {"type": "status", "data": "Retrieving context..."}):
                return
            candidates = await asyncio.to_thread(
                perform_hybrid_search, processed["rewritten"], access_level
            )
            top_chunks = await asyncio.to_thread(
                rerank_results, processed["rewritten"], candidates
            )
            if not await safe_send_json(websocket, {"type": "status", "data": "Generating response..."}):
                return
            system_prompt = SYSTEM_PROMPT.format(context=format_context(top_chunks))

        token_generator = llm_client.generate_stream(
            processed["rewritten"],
            system_prompt,
        )

        response_parts = []
        tts_queue: asyncio.Queue = asyncio.Queue()
        tts_worker = asyncio.create_task(_tts_worker(websocket, tts_queue))

        async for sentence in sentence_streamer(token_generator):
            clean_sentence = strip_citation_markers(sentence)
            if not clean_sentence:
                continue
            response_parts.append(clean_sentence)
            if not await safe_send_json(websocket, {"type": "text", "data": clean_sentence}):
                break
            await tts_queue.put(clean_sentence)

        full_response = " ".join(response_parts)
        citation_payload = build_citation_payload(top_chunks)
        if should_attach_citations(full_response, top_chunks, processed["intent"]) and citation_payload:
            await safe_send_json(websocket, {
                "type": "citations",
                "data": citation_payload,
            })

        await tts_queue.put(None)
        await tts_worker
    except DISCONNECT_ERRORS:
        raise
    except Exception as e:
        logging.exception("Voice pipeline error")
        await safe_send_json(websocket, {"type": "error", "data": str(e)})
    finally:
        await safe_send_json(websocket, {"type": "status", "data": "Done"})


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    access_level = 2

    try:
        while True:
            try:
                data = await websocket.receive_bytes()
            except DISCONNECT_ERRORS:
                break

            try:
                await _process_voice_turn(websocket, data, access_level)
            except DISCONNECT_ERRORS:
                break

    except WebSocketDisconnect:
        pass
