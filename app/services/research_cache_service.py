import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SECRET_KEY"),
)


def get_cached_hotel_research(
    hotel_code: str,
):
    response = (
        supabase
        .table("hotel_research_cache")
        .select("*")
        .eq("hotel_code", hotel_code)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    cached = response.data[0]

    expires_at = datetime.fromisoformat(
        cached["expires_at"].replace(
            "Z",
            "+00:00",
        )
    )

    if expires_at <= datetime.now(timezone.utc):
        return None

    return cached


def save_hotel_research(
    hotel_code: str,
    hotel_name: str,
    destination: str,
    web_evidence: list[dict],
):
    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(days=30)

    payload = {
        "hotel_code": hotel_code,
        "hotel_name": hotel_name,
        "destination": destination,
        "web_evidence": web_evidence,
        "researched_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }

    (
        supabase
        .table("hotel_research_cache")
        .upsert(payload)
        .execute()
    )