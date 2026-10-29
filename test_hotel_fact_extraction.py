from app.services.research_cache_service import (
    get_cached_hotel_research,
)

from app.services.hotel_fact_extractor import (
    extract_hotel_facts,
)
from app.services.hotel_fact_service import (
    save_hotel_facts,
)


HOTEL_CODE = "39664118"
HOTEL_NAME = "The Kayon Resort"
DESTINATION = "Bali, Indonesia, ID"


cached = get_cached_hotel_research(
    HOTEL_CODE
)

if not cached:
    print("NO CACHED RESEARCH FOUND")

else:
    print("CACHED RESEARCH FOUND")
    print(
        f"SOURCES: "
        f"{len(cached['web_evidence'])}"
    )

    facts = extract_hotel_facts(
        hotel_name=HOTEL_NAME,
        destination=DESTINATION,
        web_evidence=cached[
            "web_evidence"
        ],
    )

    print("\nEXTRACTED FACTS:")

    for fact in facts:
        print(fact)
        
    save_hotel_facts(
        hotel_code=HOTEL_CODE,
        hotel_name=HOTEL_NAME,
        destination=DESTINATION,
        facts=facts,
    )

    print("\nFACTS SAVED TO SUPABASE")