import os
import ollama

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

async def generate_reply(system_prompt, user_prompt):
    print(f"Configuration: {OLLAMA_MODEL} {OLLAMA_HOST}")
    response = await ollama.AsyncClient(host=OLLAMA_HOST).generate(
        model=OLLAMA_MODEL,
        prompt=user_prompt,
        options={
            "temperature": 0.2,
            "system": system_prompt,
            "max_tokens": 30
        },
        stream=False
    )
    return response['response'].strip()