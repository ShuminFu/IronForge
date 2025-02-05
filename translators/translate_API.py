import asyncio
import aiohttp
import json
import time
import sys

async def translate(text, target):
    url = "http://10.1.20.124:5000/translate"
    payload = {
        "q": text,
        "source": "auto",
        "target": target,
        "format": "text",
        "alternatives": 3,
        "api_key": ""
    }
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()

    print(json.dumps(result, ensure_ascii=False, indent=2))

async def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <text> <target_language>")
        return

    text = sys.argv[1]
    target = sys.argv[2]
    await translate(text, target)

if __name__ == "__main__":
    asyncio.run(main())