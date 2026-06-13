import asyncio
import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketDisconnect as StarletteWebSocketDisconnect

from .stt_client import transcribe_audio
from .tts_client import synthesize_speech
from retrieval.query_processor import process_query, _normalize_history
from retrieval.hybrid_search import perform_hybrid_search
from retrieval.reranker import rerank_results
from generation.llm_client import OllamaClient
from generation.prompt_templates import (
    SYSTEM_PROMPT,
    CONVERSATIONAL_PROMPT,
    CONTEXT_CHUNK_LIMIT,
    format_context,
)
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
    try:
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
            except DISCONNECT_ERRORS:
                raise
            except Exception:
                logging.exception("TTS worker failed")
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        pass


def _cancel_tts_task(tts_holder: dict) -> None:
    task = tts_holder.get("task")
    if task and not task.done():
        task.cancel()


async def _receive_turn(websocket: WebSocket) -> tuple[bytes, list]:
    """Read optional JSON history metadata, then audio bytes for this turn."""
    first = await websocket.receive()
    history = []

    if first.get("type") == "websocket.disconnect":
        raise WebSocketDisconnect()

    if first.get("text"):
        try:
            meta = json.loads(first["text"])
            history = _normalize_history(meta.get("history", []))
        except json.JSONDecodeError:
            logging.warning("Ignoring invalid turn metadata JSON")

        second = await websocket.receive()
        if second.get("type") == "websocket.disconnect":
            raise WebSocketDisconnect()
        return second.get("bytes") or b"", history

    return first.get("bytes") or b"", history


async def _process_voice_turn(
    websocket: WebSocket,
    data: bytes,
    access_level: int,
    tts_holder: dict,
    history: list | None = None,
) -> None:
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

        processed = process_query(transcription, history)
        top_chunks = []
        context_chunks = []
        search_query = processed["search_query"]
        chat_history = processed["history"]

        if processed["intent"] == "conversational":
            if not await safe_send_json(websocket, {"type": "status", "data": "Thinking..."}):
                return
            system_prompt = CONVERSATIONAL_PROMPT
        else:
            if not await safe_send_json(websocket, {"type": "status", "data": "Retrieving context..."}):
                return
            candidates = await asyncio.to_thread(
                perform_hybrid_search, search_query, access_level, 12
            )
            reranked_pool = await asyncio.to_thread(
                rerank_results, search_query, candidates, 8
            )
            top_chunks = reranked_pool
            context_chunks = reranked_pool[:CONTEXT_CHUNK_LIMIT]
            if not await safe_send_json(websocket, {"type": "status", "data": "Thinking..."}):
                return
            system_prompt = SYSTEM_PROMPT.format(context=format_context(context_chunks))

        token_generator = llm_client.generate_stream(
            processed["rewritten"],
            system_prompt,
            chat_history,
        )

        response_parts = []
        tts_queue: asyncio.Queue = asyncio.Queue()
        tts_holder["task"] = asyncio.create_task(_tts_worker(websocket, tts_queue))

        async for sentence in sentence_streamer(token_generator):
            clean_sentence = strip_citation_markers(sentence)
            if not clean_sentence:
                continue
            response_parts.append(clean_sentence)
            if not await safe_send_json(websocket, {"type": "text", "data": clean_sentence}):
                break
            await tts_queue.put(clean_sentence)

        full_response = " ".join(response_parts)
        if not full_response.strip():
            fallback = (
                "I couldn't generate a response for that question. "
                "Please try rephrasing or ask again."
            )
            logging.warning("LLM returned empty content for query")
            response_parts.append(fallback)
            await safe_send_json(websocket, {"type": "text", "data": fallback})
            full_response = fallback

        citation_payload = []
        if processed["intent"] != "conversational":
            citation_payload = await asyncio.to_thread(
                build_citation_payload,
                top_chunks,
                search_query,
                full_response,
                context_chunks,
            )
            if await asyncio.to_thread(
                should_attach_citations,
                full_response,
                top_chunks,
                processed["intent"],
                search_query,
                context_chunks,
            ) and citation_payload:
                await safe_send_json(websocket, {
                    "type": "citations",
                    "data": citation_payload,
                })

        await tts_queue.put(None)
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
    tts_holder: dict = {"task": None}

    try:
        while True:
            try:
                data, history = await _receive_turn(websocket)
            except DISCONNECT_ERRORS:
                break

            _cancel_tts_task(tts_holder)

            try:
                await _process_voice_turn(websocket, data, access_level, tts_holder, history)
            except DISCONNECT_ERRORS:
                break

    except WebSocketDisconnect:
        pass
    finally:
        _cancel_tts_task(tts_holder)
