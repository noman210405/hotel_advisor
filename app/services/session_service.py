from datetime import datetime, timezone
import uuid
from app.services.research_cache_service import supabase


def create_comparison_session(
    context: dict,
):
    session_id = str(uuid.uuid4())

    now = datetime.now(
        timezone.utc
    ).isoformat()

    payload = {
        "session_id": session_id,
        "context": context,
        "history": [],
        "research_cache": {},
        "created_at": now,
        "updated_at": now,
    }

    supabase.table(
        "comparison_sessions"
    ).insert(
        payload
    ).execute()

    return session_id


def get_comparison_session(
    session_id: str,
):
    result = (
        supabase.table(
            "comparison_sessions"
        )
        .select("*")
        .eq(
            "session_id",
            session_id,
        )
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def add_message(
    session_id: str,
    role: str,
    content: str,
):
    session = get_comparison_session(
        session_id
    )

    if not session:
        return

    history = session.get(
        "history"
    ) or []

    history.append(
        {
            "role": role,
            "content": content,
        }
    )

    supabase.table(
        "comparison_sessions"
    ).update(
        {
            "history": history,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }
    ).eq(
        "session_id",
        session_id,
    ).execute()


def get_cached_research(
    session_id: str,
    cache_key: str,
):
    session = get_comparison_session(
        session_id
    )

    if not session:
        return None

    research_cache = session.get(
        "research_cache"
    ) or {}

    return research_cache.get(
        cache_key
    )


def save_cached_research(
    session_id: str,
    cache_key: str,
    research,
):
    session = get_comparison_session(
        session_id
    )

    if not session:
        return

    research_cache = session.get(
        "research_cache"
    ) or {}

    research_cache[
        cache_key
    ] = research

    supabase.table(
        "comparison_sessions"
    ).update(
        {
            "research_cache": research_cache,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }
    ).eq(
        "session_id",
        session_id,
    ).execute()