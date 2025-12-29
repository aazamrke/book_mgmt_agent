import httpx
from app.config import settings

async def generate_summary(content: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
            json={
                "model": "meta-llama/llama-3-8b-instruct",
                "messages": [
                    {"role": "user", "content": f"Summarize this book:\n{content}"}
                ]
            }
        )
    return response.json()["choices"][0]["message"]["content"]
