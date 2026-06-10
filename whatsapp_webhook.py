import os
import logging
import asyncio
from fastapi import FastAPI, Request, Query, HTTPException
from julius.whatsapp.adapter import download_media, transcribe_audio, run_agent
from julius.core.config import WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WEBHOOK_VERIFY_TOKEN, MY_WHATSAPP_NUMBER
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("julius.whatsapp")

app = FastAPI(title="Julius WhatsApp Channel")


# ── Webhook verification (GET) ──────────────────────────────────────────────
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Meta calls this GET endpoint once to verify the webhook URL validity.
    """
    if not hub_mode or not hub_challenge or not hub_verify_token:
        logger.warning("[Webhook] Missing parameters for verification.")
        raise HTTPException(status_code=400, detail="Missing hub parameters")

    if hub_verify_token == WEBHOOK_VERIFY_TOKEN:
        logger.info("[Webhook] Verification successful.")
        try:
            return int(hub_challenge)
        except ValueError:
            return hub_challenge
    
    logger.warning(f"[Webhook] Verification failed — token mismatch. Expected: {WEBHOOK_VERIFY_TOKEN}, got: {hub_verify_token}")
    raise HTTPException(status_code=403, detail="Invalid verify token")


# ── Inbound message handler (POST) ──────────────────────────────────────────
@app.post("/webhook")
async def inbound_message(request: Request):
    """
    Receives WhatsApp message events from Meta Cloud API.
    """
    body = await request.json()

    try:
        # Navigate to the message object in the webhook payload
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        messages = value.get("messages")
        if not messages:
            return {"status": "no_message"}

        msg = messages[0]
        from_number = msg["from"]
        msg_type = msg["type"]

        logger.info(f"[Inbound] from={from_number} type={msg_type}")

        # Security check: whitelist to target number
        if MY_WHATSAPP_NUMBER and from_number != MY_WHATSAPP_NUMBER:
            logger.warning(f"[Security] Ignored message from unknown number: {from_number}")
            return {"status": "ignored"}

        # ── Route by message type ──
        if msg_type == "text":
            transcription = msg["text"]["body"]
            logger.info(f"[Text] Received user input: {transcription}")

        elif msg_type in ("audio", "voice"):
            media_id = msg[msg_type]["id"]
            logger.info(f"[Audio] Downloading media_id={media_id}...")
            audio_bytes = await download_media(media_id)
            
            logger.info(f"[Audio] Running local Whisper transcription in thread pool...")
            transcription = await asyncio.to_thread(transcribe_audio, audio_bytes)
            logger.info(f"[STT] Transcription result: {transcription}")

            if not transcription.strip():
                await send_text(from_number, "I couldn't understand that audio. Could you try again?")
                return {"status": "empty_transcription"}

        else:
            logger.info(f"[Inbound] Unsupported message type: {msg_type}")
            return {"status": "unsupported_type"}

        # ── Run Julius agent ──
        logger.info("[Agent] Invoking LangGraph agent in thread pool...")
        response = await asyncio.to_thread(run_agent, transcription)
        logger.info(f"[Agent] Response generated: {response[:120]}...")

        # ── Send reply ──
        await send_text(from_number, response)
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"[Error] Exception in inbound webhook handler: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}


async def send_text(to: str, text: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        
        logger.info(f"[Send] Sending response to {to}...")
        resp = await client.post(url, headers=headers, json=payload)
        
        if resp.status_code != 200:
            logger.error(f"[Send] API error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
        
        logger.info(f"[Send] Message delivered successfully to {to}")
