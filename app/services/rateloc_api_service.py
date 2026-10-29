import os

import httpx
from dotenv import load_dotenv


load_dotenv()


BASE_URL = "https://api.rateloc.com"

AUTHORIZATION = os.getenv("RATELOC_AUTHORIZATION")


def get_headers():
    return {
        "Authorization": AUTHORIZATION,
        "Content-Type": "application/json",
    }


async def start_hotel_search(payload: dict):

    async with httpx.AsyncClient(
        timeout=30
    ) as client:

        response = await client.post(
            f"{BASE_URL}/accommodation/v2/search",
            headers=get_headers(),
            json=payload,
        )

        response.raise_for_status()

        return response.json()

async def stream_hotel_search(search_id: str):

    url = (
        f"{BASE_URL}/accommodation/v2/search/"
        f"{search_id}/stream"
    )

    async with httpx.AsyncClient(
        timeout=None
    ) as client:

        async with client.stream(
            "GET",
            url,
            headers=get_headers(),
        ) as response:

            response.raise_for_status()

            async for chunk in response.aiter_bytes():
                yield chunk