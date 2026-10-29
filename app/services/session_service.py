import uuid


comparison_sessions = {}


def create_comparison_session(context: dict) -> str:

    session_id = str(uuid.uuid4())

    comparison_sessions[session_id] = {
        "context": context,
        "history": [],
        "research_cache": {}
    }

    return session_id


def get_comparison_session(session_id: str):

    return comparison_sessions.get(session_id)


def add_message(
    session_id: str,
    role: str,
    content: str
):

    session = comparison_sessions.get(session_id)

    if session is None:
        return

    session["history"].append({
        "role": role,
        "content": content
    })

def get_cached_research(
    session_id: str,
    cache_key: str,
):
    session = comparison_sessions.get(session_id)

    if session is None:
        return None

    return session["research_cache"].get(
        cache_key
    )


def save_cached_research(
    session_id: str,
    cache_key: str,
    research: dict,
):
    session = comparison_sessions.get(session_id)

    if session is None:
        return

    session["research_cache"][cache_key] = research