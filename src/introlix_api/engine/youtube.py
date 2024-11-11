import os
import httpx
import asyncio
import time
from introlix_api.utils.tags import fetch_tags
from dotenv import load_dotenv
from cachetools import TTLCache

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Cache with TTL of 6 hours (21600 seconds)
cache = TTLCache(maxsize=100, ttl=21600)

async def get_youtube_videos():
    url = "https://www.googleapis.com/youtube/v3/search"
    videos = []

    for tag in fetch_tags():
        if tag in cache:
            videos.append(cache[tag])  # Use cached data
            continue

        params = {
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "q": tag,
            "type": "video",
            "maxResults": 5,
            "order": "viewCount"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
                videos.append(result)
                cache[tag] = result  # Cache the result
            except httpx.HTTPStatusError as e:
                print(f"HTTP error for tag '{tag}': {e}")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Unexpected error: {e}")

        await asyncio.sleep(0.5)

    return videos

async def main():
    data = await get_youtube_videos()
    print(data)

asyncio.run(main())
