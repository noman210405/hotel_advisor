from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from app.models.comparison import ComparisonRequest
from app.services.research_cache_service import (
    get_cached_hotel_research,
    save_hotel_research,
)
from app.services.hotel_fact_extractor import (
    extract_hotel_facts,
)

from app.services.hotel_fact_service import (
    get_hotel_facts,
    save_hotel_facts,
)
from urllib.parse import urlparse
import tldextract
import re
load_dotenv()


search_tool = TavilySearch(
    max_results=5,
    topic="general"
)

def search_hotel(hotel_name: str, destination: str):

    query = f"""
    "{hotel_name}" "{destination}"
    official website hotel
    location facilities family kids club beach pool airport
    """

    return search_tool.invoke({
        "query": query
    })


def prepare_web_evidence(search_result: dict):

    evidence = []

    for result in search_result.get("results", []):
        evidence.append({
            "title": result.get("title"),
            "url": result.get("url"),
            "content": result.get("content"),
            "score": result.get("score"),
        })

    return evidence

def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return (
        value.lower()
        .replace("&", "and")
        .replace(",", " ")
        .replace("-", " ")
        .replace("  ", " ")
        .strip()
    )


def is_official_source(url: str, hotel_name: str) -> bool:

    extracted = tldextract.extract(url)

    registered_domain = normalize_text(
        extracted.domain
    )

    generic_words = {
        "hotel",
        "hotels",
        "resort",
        "resorts",
        "suite",
        "suites",
        "the",
        "and",
        "spa",
        "beach",
        "palm",
        "mumbai",
        "dubai",
        "doha",
        "makkah",
        "madinah",
    }

    hotel_tokens = [
        word
        for word in normalize_text(hotel_name).split()
        if (
            len(word) >= 4
            and word not in generic_words
        )
    ]

    destination_words = {
        "mumbai",
        "dubai",
        "doha",
        "makkah",
        "madinah",
        "london",
        "paris",
        "istanbul",
        "antalya",
        "bali",
        "singapore",
    }

    brand_tokens = [
        token
        for token in hotel_tokens
        if token not in destination_words
    ]

    return any(
        token == registered_domain
        or token in registered_domain
        for token in brand_tokens
    )

def verify_hotel_source(
    hotel_name: str,
    destination: str | None,
    address: str | None,
    result: dict,
) -> dict:

    title = normalize_text(result.get("title"))
    content = normalize_text(result.get("content"))
    combined_text = f"{title} {content}"

    hotel_tokens = [
        word
        for word in normalize_text(hotel_name).split()
        if len(word) > 2
    ]

    matched_hotel_tokens = [
        word
        for word in hotel_tokens
        if word in combined_text
    ]

    hotel_match_ratio = (
        len(matched_hotel_tokens) / len(hotel_tokens)
        if hotel_tokens
        else 0
    )

    destination_match = True

    if destination:
        destination_tokens = [
            word
            for word in normalize_text(destination).split()
            if len(word) > 2
            and word not in {"indonesia"}
        ]

        destination_match = any(
            word in combined_text
            for word in destination_tokens
        )

    address_match = None

    if address:
        address_words = [
            word
            for word in normalize_text(address).split()
            if len(word) > 3
        ]

        if address_words:
            address_match = any(
                word in combined_text
                for word in address_words
            )

    official = is_official_source(
        result.get("url", ""),
        hotel_name
    )

    verified = (
        hotel_match_ratio >= 0.6
        and destination_match
    )

    return {
        **result,
        "verified": verified,
        "hotel_match_ratio": round(hotel_match_ratio, 2),
        "destination_match": destination_match,
        "address_match": address_match,
        "official_source": official,
    }

def select_verified_sources(
    hotel_name: str,
    destination: str | None,
    address: str | None,
    search_result: dict,
    max_sources: int = 2,
):

    verified_sources = []

    for result in search_result.get("results", []):

        checked = verify_hotel_source(
            hotel_name=hotel_name,
            destination=destination,
            address=address,
            result=result,
        )

        if checked["verified"]:
            verified_sources.append(checked)

    verified_sources.sort(
        key=lambda item: (
            item["official_source"],
            item.get("score", 0),
        ),
        reverse=True,
    )

    return verified_sources[:max_sources]

def search_official_hotel_source(
    hotel_name: str,
    destination: str,
):
    query = f"""
    "{hotel_name}" "{destination}"
    official hotel website
    """

    return search_tool.invoke({
        "query": query
    })

def research_hotel(
    hotel_name: str,
    destination: str,
    address: str | None = None,
):

    search_result = search_hotel(
        hotel_name=hotel_name,
        destination=destination
    )

    evidence = select_verified_sources(
        hotel_name=hotel_name,
        destination=destination,
        address=address,
        search_result=search_result,
        max_sources=2,
    )

    has_official = any(
        source["official_source"]
        for source in evidence
    )

    if not has_official:

        official_search_result = search_official_hotel_source(
            hotel_name=hotel_name,
            destination=destination
        )

        official_evidence = select_verified_sources(
            hotel_name=hotel_name,
            destination=destination,
            address=address,
            search_result=official_search_result,
            max_sources=2,
        )

        official_only = [
            source
            for source in official_evidence
            if source["official_source"]
        ]

        if official_only:
            evidence = official_only[:1] + evidence[:1]

    return {
        "hotel_name": hotel_name,
        "web_evidence": evidence,
    }

def research_comparison_hotels(
    request: ComparisonRequest
):

    researched_hotels = []

    for hotel in request.hotels:

        cached = get_cached_hotel_research(
            hotel.hotel_code
        )

        if cached:
            print(
                f"SUPABASE CACHE HIT: "
                f"{hotel.hotel_name}"
            )
            existing_facts = get_hotel_facts(
                hotel.hotel_code
            )

            if not existing_facts:

                try:
                    facts = extract_hotel_facts(
                        hotel_name=hotel.hotel_name,
                        destination=request.destination,
                        web_evidence=cached[
                            "web_evidence"
                        ],
                    )

                    if facts:
                        save_hotel_facts(
                            hotel_code=hotel.hotel_code,
                            hotel_name=hotel.hotel_name,
                            destination=request.destination,
                            facts=facts,
                        )

                        print(
                            f"STRUCTURED FACTS SAVED: "
                            f"{hotel.hotel_name}"
                        )

                except Exception as exc:
                    print(
                        f"STRUCTURED FACT EXTRACTION FAILED "
                        f"for {hotel.hotel_name}: {exc}"
                    )

            researched_hotels.append({
                "hotel_name": hotel.hotel_name,
                "web_evidence": cached[
                    "web_evidence"
                ],
            })
        

            continue

        print(
            f"SUPABASE CACHE MISS: "
            f"{hotel.hotel_name}"
        )

        research = research_hotel(
            hotel_name=hotel.hotel_name,
            destination=request.destination,
            address=hotel.address,
        )

        save_hotel_research(
            hotel_code=hotel.hotel_code,
            hotel_name=hotel.hotel_name,
            destination=request.destination,
            web_evidence=research[
                "web_evidence"
            ],
        )

        researched_hotels.append(
            research
        )

    return researched_hotels

def research_hotel_question(
    hotel_name: str,
    destination: str,
    question: str,
    address: str | None = None,
):
    query = f"""
    "{hotel_name}" "{destination}"
    {question}
    official hotel website
    """

    search_result = search_tool.invoke({
        "query": query
    })
    print("\nRAW TAVILY RESULT:")
    print(search_result)

    evidence = select_verified_sources(
        hotel_name=hotel_name,
        destination=destination,
        address=address,
        search_result=search_result,
        max_sources=3,
    )
    print("\nVERIFIED EVIDENCE:")
    print(evidence)

    return {
        "hotel_name": hotel_name,
        "question": question,
        "web_evidence": evidence,
    }
def extract_airport_facts(web_evidence: list[dict]) -> dict:
    extracted_facts = []

    for source in web_evidence:
        content = source.get("content") or ""

        source_facts = {
            "url": source.get("url"),
            "official_source": source.get("official_source", False),
            "distances_km": [],
            "times_minutes": [],
        }

        # Example:
        # "12 KM, 45 min from Chhatrapati Shivaji airport"
        distance_before_airport = re.findall(
            r"(\d+(?:\.\d+)?)\s*km"
            r"[^.\n]{0,80}?"
            r"airport",
            content,
            flags=re.IGNORECASE,
        )

        # Example:
        # "airport - 2.4 km"
        distance_after_airport = re.findall(
            r"airport"
            r"[^.\n]{0,80}?"
            r"(\d+(?:\.\d+)?)\s*km",
            content,
            flags=re.IGNORECASE,
        )

        # Example section:
        # Airports
        # Chhatrapati Shivaji International
        # 2.4 km
        airport_section_distance = re.findall(
            r"airports?"
            r".{0,120}?"
            r"(\d+(?:\.\d+)?)\s*km",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )

        time_before_airport = re.findall(
            r"(\d+)\s*"
            r"(?:minute|minutes|min)"
            r"[^.\n]{0,80}?"
            r"airport",
            content,
            flags=re.IGNORECASE,
        )

        time_after_airport = re.findall(
            r"airport"
            r"[^.\n]{0,80}?"
            r"(\d+)\s*"
            r"(?:minute|minutes|min)",
            content,
            flags=re.IGNORECASE,
        )

        distances = (
            distance_before_airport
            + distance_after_airport
            + airport_section_distance
        )

        times = (
            time_before_airport
            + time_after_airport
        )

        source_facts["distances_km"] = sorted(
            set(float(value) for value in distances)
        )

        source_facts["times_minutes"] = sorted(
            set(int(value) for value in times)
        )

        if (
            source_facts["distances_km"]
            or source_facts["times_minutes"]
        ):
            extracted_facts.append(source_facts)

    all_distances = sorted({
        distance
        for source in extracted_facts
        for distance in source["distances_km"]
    })

    all_times = sorted({
        minutes
        for source in extracted_facts
        for minutes in source["times_minutes"]
    })

    return {
        "sources": extracted_facts,
        "distances_km": all_distances,
        "times_minutes": all_times,
        "distance_conflict": len(all_distances) > 1,
        "time_conflict": len(all_times) > 1,
    }