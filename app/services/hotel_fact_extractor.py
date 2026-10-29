from typing import Optional

from pydantic import BaseModel, Field


class HotelFact(BaseModel):
    category: str
    fact_key: str

    value_text: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    unit: Optional[str] = None

    claim: str

    source_url: str
    source_title: Optional[str] = None
    official_source: bool = False

class ExtractedHotelFact(BaseModel):
    fact_key: str

    value_text: Optional[str] = None
    value_number: Optional[float] = None
    value_boolean: Optional[bool] = None
    unit: Optional[str] = None

class HotelFactExtraction(BaseModel):
    facts: list[ExtractedHotelFact] = Field(
        default_factory=list
    )

from app.services.llm_service import model


ALLOWED_FACT_KEYS = {
    "swimming_pool",
    "spa",
    "fitness_centre",
    "kids_club",
    "beach_access",
    "restaurant",
    "airport_shuttle",
    "airport_distance",
    "airport_travel_time",
    "adults_only",
}
FACT_CATEGORIES = {
    "swimming_pool": "facility",
    "spa": "facility",
    "fitness_centre": "facility",
    "kids_club": "facility",
    "beach_access": "facility",
    "restaurant": "facility",
    "airport_shuttle": "transport",
    "airport_distance": "transport",
    "airport_travel_time": "transport",
    "adults_only": "policy",
}


structured_model = model.with_structured_output(
    HotelFactExtraction,
    method="json_mode",
)


def extract_hotel_facts(
    hotel_name: str,
    destination: str,
    web_evidence: list[dict],
) -> list[dict]:

    extracted_facts = []

    for source in web_evidence:

        source_content = source.get("content")

        if not source_content:
            continue

        prompt = f"""
You extract hotel facts from ONE supplied source.

Return valid JSON matching the required HotelFactExtraction structure.

HOTEL:
{hotel_name}

DESTINATION:
{destination}

SOURCE URL:
{source.get("url")}

SOURCE TITLE:
{source.get("title")}

SOURCE CONTENT:
{source_content}

STRICT RULES:

1. Use ONLY the supplied source content.
2. Never use your own knowledge.
3. Never guess or infer a missing fact.
4. If a fact is not explicitly supported, do not return it.
5. Absence of a facility is NOT evidence that it does not exist.
6. Only extract facts about this exact hotel.
7. Do not extract hotel prices, availability, room availability,
   board basis, cancellation terms, refundability or booking data.

8. Only use these fact_key values:

{sorted(ALLOWED_FACT_KEYS)}

9. value_boolean=true only when the source explicitly confirms
   that the facility or property attribute exists.

10. Never output value_boolean=false unless the source explicitly
    states the hotel does not have that facility.

11. The TOP LEVEL JSON must ALWAYS be an object in this form:

{{
  "facts": [
    {{
      "fact_key": "swimming_pool",
      "value_text": null,
      "value_number": null,
      "value_boolean": true,
      "unit": null
    }}
  ]
}}

12. Never return a bare JSON array.

Correct:
{{"facts": [...]}}

Wrong:
[...]

13. For these facts use value_boolean only:

- swimming_pool
- spa
- fitness_centre
- kids_club
- beach_access
- restaurant
- airport_shuttle
- adults_only

14. Never use value_number for the facility or policy facts above.

For example, if the source says there is 1 restaurant,
return restaurant with value_boolean=true.
Do NOT return value_number=1.

15. For airport_distance:
- use value_number
- include the explicitly stated unit

16. For airport_travel_time:
- use value_number
- include the explicitly stated unit

17. Return only:
- fact_key
- value_text
- value_number
- value_boolean
- unit

18. Do not return category, claim, source_url,
source_title or official_source.
The backend creates those fields.

19. If no supported facts are explicitly confirmed, return:

{{"facts": []}}
"""

        result = structured_model.invoke(prompt)

        for fact in result.facts:

            if fact.fact_key not in ALLOWED_FACT_KEYS:
                continue

            category = FACT_CATEGORIES[
                fact.fact_key
            ]

            if fact.value_boolean is True:
                claim = (
                    f"{fact.fact_key.replace('_', ' ')} "
                    f"is available"
                )

            elif fact.value_boolean is False:
                claim = (
                    f"{fact.fact_key.replace('_', ' ')} "
                    f"is explicitly unavailable"
                )

            elif fact.value_number is not None:
                claim = (
                    f"{fact.fact_key.replace('_', ' ')}: "
                    f"{fact.value_number}"
                )

                if fact.unit:
                    claim += f" {fact.unit}"

            elif fact.value_text:
                claim = fact.value_text

            else:
                continue

            extracted_facts.append({
                "category": category,
                "fact_key": fact.fact_key,

                "value_text": fact.value_text,
                "value_number": fact.value_number,
                "value_boolean": fact.value_boolean,
                "unit": fact.unit,

                "claim": claim,

                "source_url": source.get("url"),
                "source_title": source.get("title"),
                "official_source": source.get(
                    "official_source",
                    False,
                ),
            })

    return extracted_facts