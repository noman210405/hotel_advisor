from datetime import datetime, timedelta, timezone

from app.services.research_cache_service import supabase


def get_hotel_facts(
    hotel_code: str,
):
    response = (
        supabase
        .table("hotel_facts")
        .select("*")
        .eq("hotel_code", hotel_code)
        .gt(
            "expires_at",
            datetime.now(timezone.utc).isoformat(),
        )
        .execute()
    )

    return response.data
def build_compact_fact_context(
    hotel_code: str,
):
    facts = get_hotel_facts(
        hotel_code
    )

    if not facts:
        return []

    grouped = {}

    for fact in facts:

        fact_key = fact["fact_key"]

        if fact_key not in grouped:

            grouped[fact_key] = {
                "fact_key": fact_key,
                "value_text": fact.get(
                    "value_text"
                ),
                "value_number": fact.get(
                    "value_number"
                ),
                "value_boolean": fact.get(
                    "value_boolean"
                ),
                "unit": fact.get("unit"),
                "claims": [],
                "sources": [],
            }

        grouped[fact_key][
            "claims"
        ].append(
            fact["claim"]
        )

        grouped[fact_key][
            "sources"
        ].append({
            "source_url": fact[
                "source_url"
            ],
            "official_source": fact[
                "official_source"
            ],
        })

    return list(
        grouped.values()
    )
def save_hotel_facts(
    hotel_code: str,
    hotel_name: str,
    destination: str,
    facts: list[dict],
):
    if not facts:
        return

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30)

    rows = []

    for fact in facts:
        rows.append({
            "hotel_code": hotel_code,
            "hotel_name": hotel_name,
            "destination": destination,

            "category": fact["category"],
            "fact_key": fact["fact_key"],

            "value_text": fact.get("value_text"),
            "value_number": fact.get("value_number"),
            "value_boolean": fact.get("value_boolean"),
            "unit": fact.get("unit"),

            "claim": fact["claim"],

            "source_url": fact["source_url"],
            "source_title": fact.get("source_title"),
            "official_source": fact.get(
                "official_source",
                False,
            ),

            "verified": True,

            "researched_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        })

    (
        supabase
        .table("hotel_facts")
        .upsert(
            rows,
            on_conflict="hotel_code,fact_key,source_url",
        )
        .execute()
    )