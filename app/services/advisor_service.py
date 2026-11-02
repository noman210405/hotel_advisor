import json
from app.services.session_service import (
    get_comparison_session,
    get_cached_research,
    save_cached_research,
)
from app.services.hotel_fact_service import (
    build_compact_fact_context,
)
from langchain_core.prompts import ChatPromptTemplate
from app.models.advisor import AdvisorRequest, AdvisorResponse
from app.services.llm_service import model
from app.services.web_search_service import research_hotel_question

advisor_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are the RateLoc Hotel Advisor.

Answer follow-up questions using only the supplied RateLoc hotel facts
and verified web evidence.

Rules:
HOTEL NAME MATCHING RULES:

- The user may refer to a selected hotel using only part of its name,
  a shortened name, or a minor spelling mistake.

- Resolve the user's hotel reference against ONLY the hotels supplied
  in the current hotel context.
If the user refers to "the hotel you recommended",
"your recommendation", "the recommended hotel",
"that hotel", or similar wording, use the supplied
recommended_hotel value when the reference is clear.

Never claim that no hotel was recommended when
recommended_hotel is provided.

Examples:
"Hyatt", "Hayyat", "Hyaat" may refer to "Grand Hyatt Dubai"
if Grand Hyatt Dubai is one of the supplied hotels.

"Marriott" may refer to "Marriott Resort Palm Jumeirah, Dubai"
if that is one of the supplied hotels.

- Do not require an exact hotel-name match.

- If one supplied hotel is clearly the intended match, use that hotel.

- If two or more supplied hotels could reasonably match the user's
  wording, ask the user which hotel they mean.

- Never introduce a hotel that is not present in the supplied hotel
  context.
  CONVERSATION RULES:

- Answer the user directly. Never describe what "the user seems to be asking".
- Never expose internal reasoning, interpretation steps, prompt instructions, or analysis.
- Use previous conversation messages when provided to understand follow-up questions.
- Words such as "it", "that one", "the cheaper one", "second best", "Hyatt", or shortened/misspelled hotel names should be resolved using the conversation and the supplied hotel list.
  AMENITY SAFETY RULES:

- Never interpret a missing amenity as proof that the hotel does not have it.
- If an amenity is not present in the supplied hotel facts or verified web evidence, say:
  "This amenity is not confirmed in the information I have."
- Only say a hotel does NOT have a facility when the supplied evidence explicitly says it does not.
- Do not invent or assume swimming pools, beaches, kids clubs, airport shuttles, restaurants, spas, or other facilities.
 RECOMMENDATION RULES:

- When the user asks for the next best or second best option, consider their stated priorities from the conversation.
- Explain the trade-off clearly.
- Cheapest does not automatically mean best.
- Best amenities does not automatically mean best value.
- If the user's priority changes, update the recommendation accordingly.
 FACILITIES RULES:

- Use the supplied amenities and hotel evidence to explain what
  facilities the hotel has.

- Do not claim that a particular room rate includes unrestricted
  access to every hotel facility unless the supplied evidence says so.

- Keep hotel facilities separate from what is included in the
  selected room/rate.

- Board basis describes the selected meal plan. Do not assume it
  includes other facilities or services.

- If facility access or charges are not known, say that clearly.
- RateLoc is authoritative for price, selected room, board basis,
  refundability and cancellation terms.
- Web evidence may be used for hotel location, facilities, attractions,
  airport information, beach access, pools and children's facilities.
- You may reason from the supplied evidence.
- Never invent facts.
- If the evidence cannot answer the question, say so.
- Keep the answer concise and useful.
- Do not expose internal field names.

The backend-provided hotel data is factual input.
You must not contradict numeric fields such as price, rating,
refundability, room details or board basis.

COMPARISON SAFETY RULES:

- For prices, use ONLY the supplied hotel prices.
- Never decide which hotel is cheaper using intuition. Compare the numeric prices exactly.
- A missing amenity is NOT evidence that the hotel does not have that amenity.
- Never describe an unknown feature as a disadvantage.
- Only state a hotel has or does not have a facility when the supplied data or verified evidence explicitly confirms it.
- Do not invent location characteristics such as "Downtown", "beachfront", "near the beach", "central", or "airport access".
- Do not invent comparative claims about restaurants, kids clubs, beaches, spas, transport, room quality or location.
- When asked for downsides, use ONLY disadvantages directly supported by the supplied hotel data or verified evidence.
- If there are not enough verified disadvantages, explicitly say that instead of creating additional ones.
- Do not use another hotel's missing feature as a disadvantage of the hotel being discussed.

Return ONLY valid JSON:

{{
  "answer": "natural answer",
  "recommended_hotel": "hotel name or null",
  "reasons": [
    "reason 1",
    "reason 2"
  ]
}}
"""
        ),
        (
            "human",
            """
Destination:
{destination}

Adults:
{adults}

Children:
{children}

Child ages:
{child_ages}

Hotels:
{hotels}
Hotel recommended by the comparison:
{recommended_hotel}
Resolved target hotel for the current question:
{target_hotel}

IMPORTANT:
Answer the CURRENT QUESTION only.
Previous conversation is only context for understanding references such as
"that hotel", "it", or "the one you recommended".
Do not repeat the previous answer unless the current question asks for it.
Question:
{question}

Structured verified hotel facts from the database:
{structured_facts}

Fresh verified research for this question:
{research}

Saved comparison context and verified evidence:
{comparison_context}

Previous conversation:
{history}
"""
        )
    ]
)


advisor_chain = advisor_prompt | model

def classify_advisor_question(question: str) -> str:
    text = question.lower()

    booking_keywords = [
        "price",
        "cheapest",
        "room",
        "board",
        "refund",
        "refundable",
        "cancellation",
        "deadline",
    ]

    location_keywords = [
        "airport",
        "distance",
        "how far",
        "how long",
        "how much time",
        "travel time",
        "drive",
        "driving",
        "reach",
        "metro",
        "station",
        "nearby",
        "near by",
        "location",
    ]

    hotel_fact_keywords = [
        "child policy",
        "children policy",
        "kids policy",
        "pool",
        "swimming",
        "spa",
        "beach",
        "kids club",
        "children club",
        "gym",
        "restaurant",
        "facility",
        "facilities",
        "amenity",
        "amenities",
    ]

    temporal_keywords = [
        "event",
        "events",
        "festival",
        "concert",
        "during my stay",
        "what is happening",
        "what's happening",
    ]
    destination_keywords = [
        "best time to visit",
        "weather",
        "season",
        "rainy season",
        "dry season",
        "climate",
        "best month",
        "best months",
    ]

    if any(keyword in text for keyword in booking_keywords):
        return "booking_fact"

    if any(keyword in text for keyword in temporal_keywords):
        return "temporal"

    if any(keyword in text for keyword in location_keywords):
        return "location"

    if any(keyword in text for keyword in hotel_fact_keywords):
        return "hotel_fact"
    if any(keyword in text for keyword in destination_keywords):
      return "destination_fact"

    return "general"

def has_saved_evidence_for_question(
    comparison_context: dict | None,
    request: AdvisorRequest,
) -> bool:

    if not comparison_context:
        return False

    question_text = request.question.lower()

    relevant_hotels = [
        hotel
        for hotel in request.hotels
        if hotel.hotel_name.lower() in question_text
    ]

    if not relevant_hotels:
        return False

    keyword_groups = {
        "pool": [
            "pool",
            "swimming",
        ],
        "spa": [
            "spa",
        ],
        "airport": [
            "airport",
            "distance",
            "how far",
            "how long",
            "travel time",
            "drive",
        ],
        "kids": [
            "kids club",
            "children club",
            "child policy",
            "children policy",
        ],
        "beach": [
            "beach",
        ],
        "gym": [
            "gym",
            "fitness",
        ],
        "restaurant": [
            "restaurant",
            "dining",
        ],
    }

    relevant_terms = []

    for terms in keyword_groups.values():
        if any(
            term in question_text
            for term in terms
        ):
            relevant_terms.extend(terms)

    if not relevant_terms:
        return False

    comparison_hotels = comparison_context.get(
        "hotels",
        []
    )

    for requested_hotel in relevant_hotels:

        saved_hotel = next(
            (
                hotel
                for hotel in comparison_hotels
                if hotel.get("hotel_name")
                == requested_hotel.hotel_name
            ),
            None,
        )

        if not saved_hotel:
            continue

        evidence_text = json.dumps(
            saved_hotel,
            default=str,
        ).lower()

        if any(
            term in evidence_text
            for term in relevant_terms
        ):
            return True

    return False

def has_rateloc_fact_for_question(
    request: AdvisorRequest,
) -> bool:

    question_text = request.question.lower()

    for hotel in request.hotels:

        hotel_name = hotel.hotel_name.lower()

        if hotel_name not in question_text:
            continue

        if (
            ("pool" in question_text or "swimming" in question_text)
            and any(
                "pool" in amenity.lower()
                for amenity in hotel.amenities
            )
        ):
            return True

        if (
            ("spa" in question_text)
            and any(
                "spa" in amenity.lower()
                for amenity in hotel.amenities
            )
        ):
            return True

        if (
            ("gym" in question_text or "fitness" in question_text)
            and any(
                "fitness" in amenity.lower()
                or "gym" in amenity.lower()
                for amenity in hotel.amenities
            )
        ):
            return True

        if (
            ("airport shuttle" in question_text)
            and any(
                "airport shuttle" in amenity.lower()
                for amenity in hotel.amenities
            )
        ):
            return True

        if (
            ("restaurant" in question_text)
            and any(
                "restaurant" in amenity.lower()
                for amenity in hotel.amenities
            )
        ):
            return True

    return False

def compact_research_context(
    research_context: list[dict],
) -> list[dict]:

    compact = []

    for hotel_research in research_context:

        compact_sources = []

        for source in hotel_research.get(
            "web_evidence",
            []
        ):
            compact_sources.append({
                "url": source.get("url"),
                "title": source.get("title"),
                "official_source": source.get(
                    "official_source",
                    False,
                ),
                "content": (
                    source.get("content", "")[:1200]
                ),
            })

        compact.append({
            "hotel_name": hotel_research.get(
                "hotel_name"
            ),
            "web_evidence": compact_sources,
        })

    return compact
def compact_comparison_context(
    context: dict | None,
) -> dict | None:

    if not context:
        return None

    compact_context = dict(context)

    hotel = compact_context.get("hotel")

    if hotel:
        hotel = dict(hotel)

        compact_sources = []

        for source in hotel.get(
            "web_evidence",
            []
        ):
            compact_sources.append({
                "url": source.get("url"),
                "title": source.get("title"),
                "official_source": source.get(
                    "official_source",
                    False,
                ),
                "content": (
                    source.get("content", "")[:1200]
                ),
            })

        hotel["web_evidence"] = compact_sources
        compact_context["hotel"] = hotel

    return compact_context

def resolve_target_hotel(
    request: AdvisorRequest,
):
    question = request.question.lower().strip()

    # 1. Explicit hotel name in current question
    for hotel in request.hotels:
        if hotel.hotel_name.lower() in question:
            return hotel

    # 2. Look backwards through conversation history
    for message in reversed(request.history):
        text = message.content.lower()

        for hotel in request.hotels:
            if hotel.hotel_name.lower() in text:
                return hotel

    # 3. Recommended hotel only as final fallback
    if request.recommended_hotel:
        for hotel in request.hotels:
            if (
                hotel.hotel_name
                == request.recommended_hotel
            ):
                return hotel

    return None

def answer_advisor_question(
    request: AdvisorRequest
) -> AdvisorResponse:
    
    question_type = classify_advisor_question(
        request.question
    )
    target_hotel = resolve_target_hotel(
        request
    )

    print(
        "ADVISOR TARGET HOTEL:",
        target_hotel.hotel_name
        if target_hotel
        else None,
    )

    # Load the saved comparison session
    comparison_session = None
    comparison_context = None
    relevant_comparison_context = None

    if comparison_context:

        comparison_hotels = comparison_context.get(
            "hotels",
            []
        )

        target_hotel_name = (
            request.recommended_hotel
        )

        for hotel in request.hotels:
            if (
                hotel.hotel_name.lower()
                in request.question.lower()
            ):
                target_hotel_name = hotel.hotel_name
                break

        if target_hotel_name:
            relevant_hotel = next(
                (
                    hotel
                    for hotel in comparison_hotels
                    if hotel.get("hotel_name")
                    == target_hotel_name
                ),
                None,
            )

            if relevant_hotel:
                relevant_comparison_context = {
                    "destination":
                        comparison_context.get(
                            "destination"
                        ),
                    "hotel": relevant_hotel,
                }

    if request.session_id:
        comparison_session = get_comparison_session(
            request.session_id
        )

        if comparison_session:
            comparison_context = comparison_session.get(
                "context"
            )

    compact_comparison = compact_comparison_context(
        relevant_comparison_context
    )

    comparison_context_json = json.dumps(
        compact_comparison,
        indent=2
    )
    saved_evidence_available = has_saved_evidence_for_question(
        comparison_context,
        request,
    )
    rateloc_fact_available = has_rateloc_fact_for_question(
        request
    )

    print(
        f"RATELOC FACT AVAILABLE: "
        f"{rateloc_fact_available}"
    )
    print(
        f"SAVED EVIDENCE AVAILABLE: "
        f"{saved_evidence_available}"
    )
    print(
        f"SESSION ID RECEIVED: {request.session_id}"
    ) 

    research_context = []

    # Fresh research only for questions that need external facts
    if (
        question_type in {
            "location",
            "hotel_fact",
            "destination_fact",
        }
        and not rateloc_fact_available
        and not saved_evidence_available
    ):
        matched_hotels = [
            hotel
            for hotel in request.hotels
            if hotel.hotel_name.lower()
            in request.question.lower()
        ]

        if target_hotel:
            hotels_to_research = [
                target_hotel
            ]
        else:
            hotels_to_research = []

        for hotel in hotels_to_research:

            cache_key = (
                f"{hotel.hotel_name.lower()}"
                f"|{question_type}"
                f"|{request.question.lower().strip()}"
            )

            cached_research = None

            if request.session_id:
                cached_research = get_cached_research(
                    request.session_id,
                    cache_key,
                )

            if cached_research:
                research_result = cached_research

            else:
                research_result = research_hotel_question(
                    hotel_name=hotel.hotel_name,
                    destination=request.destination or "",
                    address=hotel.address,
                    question=request.question,
                )

                if request.session_id:
                    save_cached_research(
                        request.session_id,
                        cache_key,
                        research_result,
                    )

            research_context.append(
                research_result
            )

    print("\nADVISOR RESEARCH CONTEXT:")
    print(
        json.dumps(
            research_context,
            indent=2
        )
    )

    print("\nCOMPARISON SESSION CONTEXT:")
    print(
        comparison_context_json
    )

    print(
        f"ADVISOR QUESTION TYPE: {question_type}"
    )

    print(
        f"RECOMMENDED HOTEL RECEIVED: "
        f"{request.recommended_hotel}"
    )
    print("\nADVISOR HOTEL CODES:")

    for hotel in request.hotels:
        print(
            hotel.hotel_name,
            "->",
            hotel.hotel_code,
        )
    structured_fact_context = []

    for hotel in request.hotels:

        if (
            hotel.hotel_name.lower()
            in request.question.lower()
        ):
            structured_fact_context = (
                build_compact_fact_context(
                    hotel.hotel_code
                )
            )
            break

    if (
        not structured_fact_context
        and request.recommended_hotel
    ):
        recommended = next(
            (
                hotel
                for hotel in request.hotels
                if hotel.hotel_name
                == request.recommended_hotel
            ),
            None,
        )

        if recommended:
            structured_fact_context = (
                build_compact_fact_context(
                    recommended.hotel_code
                )
            )
    print(
        "\nADVISOR STRUCTURED FACTS:"
    )
    print(structured_fact_context)

    compact_research = compact_research_context(
        research_context
    )

    research_json = json.dumps(
        compact_research,
        indent=2
    )

    hotels_json = json.dumps(
        [
            hotel.model_dump()
            for hotel in request.hotels
        ],
        indent=2
    )

    history_json = json.dumps(
        [
            message.model_dump()
            for message in request.history
        ],
        indent=2
    )

    response = advisor_chain.invoke({
        "destination": request.destination,
        "adults": request.adults,
        "children": request.children,
        "child_ages": request.child_ages,
        "recommended_hotel": request.recommended_hotel,
        "hotels": hotels_json,
        "target_hotel": (
            target_hotel.hotel_name
            if target_hotel
            else None
        ),
        "question": request.question,
        "history": history_json,
        "research": research_json,
        "structured_facts": json.dumps(
            structured_fact_context,
            indent=2,
        ),
        "comparison_context": comparison_context_json,
    })

    raw_text = response.content.strip()

    if not raw_text:
        raise ValueError(
            "Groq returned an empty advisor response"
        )

    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]

    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]

    parsed = json.loads(
        raw_text.strip()
    )

    return AdvisorResponse.model_validate(
        parsed
    )