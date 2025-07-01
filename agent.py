import os
import asyncio
from dotenv import load_dotenv
from ollama_client import generate_reply
from messaging import send_message, subscribe_messages

load_dotenv()

AGENT_ID = os.getenv("AGENT_ID")
AGENT_NAME = os.getenv("AGENT_NAME")
SYSTEM_PROMPT = os.getenv("AGENT_SYSTEM_PROMPT")
KEYWORDS = [k.strip().lower() for k in os.getenv("AGENT_TARGET_KEYWORDS", "").split(",") if k]

def should_respond(message, receiver, text):
    if receiver == AGENT_ID:
        return True
    if receiver and receiver != AGENT_ID:
        return False
    return any(k in text.lower() for k in KEYWORDS)

async def handle_incoming_message(payload):
    sender = payload.get("sender")
    receiver = payload.get("receiver")
    text = payload.get("message", "")
    conversation_id = payload.get("conversation_id")
    message_id = payload.get("message_id")
    print(f"[ {sender} ] {text} -> {conversation_id} -> {message_id}:]")

    if sender == AGENT_ID:
        return

    if should_respond(payload, receiver, text):
        print(f"[\U0001F4AC {AGENT_NAME}] Respondiendo a: {text}")
        response = await generate_reply(SYSTEM_PROMPT, text)
        await send_message(
            sender=AGENT_ID,
            message=response,
            receiver=sender,
            conversation_id=conversation_id,
            in_response_to=message_id
        )
    else:
        print(f"[\U0001F9D0 {AGENT_NAME}] Ignorando mensaje: {text}")


def start_agent():
    print(f"\n🤖 Agente '{AGENT_NAME}' ({AGENT_ID}) iniciado.\n")

    initial_message = os.getenv("AGENT_INITIAL_MESSAGE", "").strip()
    if initial_message:
        asyncio.run(send_message(
            sender=AGENT_ID,
            message=initial_message,
            receiver=""
        ))
        print(f"[🚀 {AGENT_NAME}] Inició la conversación con: {initial_message}")

    subscribe_messages(callback=handle_incoming_message)
