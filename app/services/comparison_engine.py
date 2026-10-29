from app.models.comparison import ComparisonRequest
from app.services.comparison_service import calculate_price_comparison
from app.services.ai_comparison_service import build_comparison_context
from app.services.web_search_service import research_comparison_hotels
from app.services.llm_service import generate_hotel_comparison
from app.services.session_service import create_comparison_session


def filter_unsupported_cons(
    cons: list[str],
    hotel_context: dict,
) -> list[str]:

    web_evidence = hotel_context.get(
        "web_evidence",
        []
    )

    evidence_text = str(
        web_evidence
    ).lower()

    facility_rules = {
        "swimming pool": [
            "no swimming pool",
            "no pool",
            "does not have a swimming pool",
            "doesn't have a swimming pool",
            "does not have a pool",
            "doesn't have a pool",
            "lack a swimming pool",
            "lacks a swimming pool",
            "lack a pool",
            "lacks a pool",
            "without a swimming pool",
            "without a pool",
            "instead of a pool",
            "instead of a swimming pool",
        ],
        "fitness centre": [
            "no fitness centre",
            "does not have a fitness centre",
            "doesn't have a fitness centre",
        ],
        "kids club": [
            "no kids club",
            "no children's club",
            "does not have a kids club",
        ],
        "spa": [
            "no spa",
            "does not have a spa",
        ],
        "airport shuttle": [
            "no airport shuttle",
            "does not have an airport shuttle",
        ],
        "restaurant": [
            "no restaurant",
            "does not have a restaurant",
        ],
        "beach access": [
            "no beach access",
            "does not have beach access",
            "doesn't have beach access",
            "not beachfront",
            "no direct beach access",
        ],
    }

    safe_cons = []

    for con in cons:

        con_lower = con.lower()

        unsupported_negative = False

        for facility, negative_phrases in facility_rules.items():

            if facility not in con_lower:
                continue

            claim_is_negative = any(
                phrase in con_lower
                for phrase in [
                    "no ",
                    "does not",
                    "doesn't",
                    "lacks",
                    "without",
                    "not listed",
                ]
            )

            if not claim_is_negative:
                continue

            explicit_negative_evidence = any(
                phrase in evidence_text
                for phrase in negative_phrases
            )

            if not explicit_negative_evidence:
                unsupported_negative = True
                break

        if not unsupported_negative:
            safe_cons.append(con)

    return safe_cons
def filter_unsupported_room_claims(
    claims: list[str],
    hotel_context: dict,
) -> list[str]:

    selected_offer = hotel_context.get(
        "selected_offer",
        {}
    )

    room_name = (
        selected_offer.get("room_name")
        or ""
    ).lower()

    web_evidence = hotel_context.get(
        "web_evidence",
        []
    )

    evidence_text = str(
        web_evidence
    ).lower()

    safe_claims = []

    room_inclusion_phrases = [
        "includes",
        "included",
        "comes with",
        "features",
        "has a private",
        "private pool",
        "private infinity pool",
        "private jacuzzi",
        "private hot tub",
    ]

    for claim in claims:

        claim_lower = claim.lower()

        suggests_room_inclusion = any(
            phrase in claim_lower
            for phrase in room_inclusion_phrases
        )

        if not suggests_room_inclusion:
            safe_claims.append(claim)
            continue

        room_is_explicitly_supported = (
            room_name
            and room_name in evidence_text
        )

        if room_is_explicitly_supported:
            safe_claims.append(claim)

    return safe_claims
def filter_unsupported_free_claims(
    claims: list[str],
    hotel_context: dict,
) -> list[str]:

    web_evidence = hotel_context.get(
        "web_evidence",
        []
    )

    evidence_text = str(
        web_evidence
    ).lower()

    free_words = [
        "free",
        "complimentary",
        "included",
        "included in the rate",
    ]

    safe_claims = []

    for claim in claims:

        claim_lower = claim.lower()

        claims_free_service = any(
            word in claim_lower
            for word in free_words
        )

        if not claims_free_service:
            safe_claims.append(claim)
            continue

        explicitly_supported = any(
            word in evidence_text
            for word in free_words
        )

        if explicitly_supported:
            safe_claims.append(claim)

    return safe_claims
def filter_unsupported_comparative_claims(
    claims: list[str],
) -> list[str]:

    unsafe_comparative_phrases = [
        "fewer amenities",
        "fewer facilities",
        "fewer swimming pool",
        "fewer pool",
        "limited amenities",
        "limited facilities",
        "limited pool",
        "less amenities",
        "less facilities",
    ]

    safe_claims = []

    for claim in claims:
        claim_lower = claim.lower()

        unsupported = any(
            phrase in claim_lower
            for phrase in unsafe_comparative_phrases
        )

        if not unsupported:
            safe_claims.append(claim)

    return safe_claims

def filter_unsupported_summary(
    summary: str,
    hotel_context_by_name: dict,
) -> str:

    if not summary:
        return summary

    sentences = summary.split(". ")

    safe_sentences = []

    for sentence in sentences:

        sentence_is_safe = True

        for hotel_name, hotel_context in hotel_context_by_name.items():

            if hotel_name.lower() not in sentence.lower():
                continue

            checked = filter_unsupported_cons(
                [sentence],
                hotel_context,
            )

            if not checked:
                sentence_is_safe = False
                break

        if sentence_is_safe:
            safe_sentences.append(sentence)

    return ". ".join(safe_sentences)

def run_comparison(request: ComparisonRequest):

    print("STEP 1: Calculating RateLoc prices...")
    cheapest_hotel, price_difference = calculate_price_comparison(request)
    price_ranking = sorted(
        [
            {
                "hotel_name": hotel.hotel_name,
                "price": hotel.selected_offer.price,
                "currency": hotel.selected_offer.currency,
            }
            for hotel in request.hotels
        ],
        key=lambda item: item["price"],
    )
    print("STEP 1 DONE")

    try:
        print("STEP 2: Starting Tavily research...")

        web_research = research_comparison_hotels(request)
        print("\nCOMPARISON WEB RESEARCH:")
        print(web_research)

        print("STEP 2 DONE: Tavily research completed")

    except Exception as error:
        print(
            f"Web research unavailable: "
            f"{type(error).__name__}: {error}"
        )
        web_research = []

    print("STEP 3: Building AI context...")

    ai_context = build_comparison_context(
        request=request,
        web_research=web_research
    )
    ai_context["backend_price_facts"] = {
        "cheapest_hotel": cheapest_hotel,
        "price_difference": price_difference,
        "price_ranking": price_ranking,
    }
    hotel_context_by_name = {
        hotel["hotel_name"]: hotel
        for hotel in ai_context["hotels"]
    }
    print("\nAI COMPARISON CONTEXT:")
    print(ai_context)
    session_id = create_comparison_session(ai_context)

    print("STEP 3 DONE")

    try:
        print("STEP 4: Sending comparison to configured model...")

        ai_result = generate_hotel_comparison(ai_context)

        print("STEP 4 DONE: model responded")

    except Exception as error:
        print(
            f"AI comparison unavailable: "
            f"{type(error).__name__}: {error}"
        )
        ai_result = None

    safe_summary = None

    if ai_result:
        safe_summary = filter_unsupported_summary(
            ai_result.summary,
            hotel_context_by_name,
        )

    print("STEP 5: Building final response...")

    results = []

    for hotel in request.hotels:

        ai_hotel = None

        if ai_result is not None:
            ai_hotel = next(
                (
                    item
                    for item in ai_result.hotels
                    if item.hotel_name == hotel.hotel_name
                ),
                None
            )

        results.append({
            "hotel_name": hotel.hotel_name,
            "price": hotel.selected_offer.price,
            "currency": hotel.selected_offer.currency,
            "pros": (
                filter_unsupported_free_claims(
                    filter_unsupported_room_claims(
                        ai_hotel.pros,
                        hotel_context_by_name.get(
                            hotel.hotel_name,
                            {}
                        ),
                    ),
                    hotel_context_by_name.get(
                        hotel.hotel_name,
                        {}
                    ),
                )
                if ai_hotel
                else []
            ),
            "cons": (
                filter_unsupported_comparative_claims(
                    filter_unsupported_cons(
                        ai_hotel.cons,
                        hotel_context_by_name.get(
                            hotel.hotel_name,
                            {}
                        ),
                    )
                )
                if ai_hotel
                else []
            ),
            "recommendation_reason": (
                ai_hotel.recommendation_reason
                if ai_hotel
                else None
            ),
        })

    print("STEP 5 DONE")

    return {
        "session_id": session_id,
        "recommended_hotel": (
            ai_result.recommended_hotel
            if ai_result
            else None
        ),
        "cheapest_hotel": cheapest_hotel,
        "price_difference": price_difference,
        "summary": (
            safe_summary
            if safe_summary
            else "AI comparison is temporarily unavailable. RateLoc booking facts are still shown."
        ),
        "hotels": results,
    }