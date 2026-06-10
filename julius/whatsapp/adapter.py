import os
import tempfile
import httpx
from julius.stt import STTTranscriber
from julius.memory import search_memory, save_memory
from julius.agent import agent_graph
from julius.core.config import WHATSAPP_TOKEN, AGENT_LANGUAGE

# Global transcriber instance inside the module
_stt = STTTranscriber()

async def download_media(media_id: str) -> bytes:
    """
    Downloads a media file from WhatsApp Cloud API using the media ID.
    First resolves the media ID to an absolute URL, then downloads the file content.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: resolve media ID to URL
        meta_resp = await client.get(
            f"https://graph.facebook.com/v19.0/{media_id}",
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        )
        meta_resp.raise_for_status()
        media_url = meta_resp.json()["url"]

        # Step 2: download the actual file
        file_resp = await client.get(
            media_url,
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        )
        file_resp.raise_for_status()
        return file_resp.content


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Saves audio bytes to a temp file and transcribes with Faster-Whisper.
    """
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        return _stt.transcribe_file(tmp_path, language=AGENT_LANGUAGE)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def run_agent(transcription: str) -> str:
    """
    Searches memory, invokes LangGraph agent, saves the turn, and returns response text.
    """
    # 1. Look up long-term memory facts
    memories = search_memory(transcription)
    memory_context = "\n".join(memories) if memories else ""

    # 2. Invoke dialog graph
    result = agent_graph.invoke(
        {
            "messages": [("user", transcription)],
            "memory_context": memory_context
        },
        config={
            "configurable": {"thread_id": "wa_interview"},
            "recursion_limit": 8
        }
    )
    response = result["messages"][-1].content

    # 3. Persist the turn to long-term memory asynchronously in the background
    save_memory(f"User: {transcription}\nAgent: {response}")

    return response
