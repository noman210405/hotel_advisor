import json

from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from langchain_core.prompts import ChatPromptTemplate

from app.services.llm_service import model


class DistanceClaim(BaseModel):
    value: float
    unit: Literal["km", "mile", "miles"]
    evidence: str

    @field_validator("unit", mode="before")
    @classmethod
    def normalize_unit(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value


class TimeClaim(BaseModel):
    value: int
    unit: Literal["minute", "minutes", "min"]
    evidence: str

    @field_validator("unit", mode="before")
    @classmethod
    def normalize_unit(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value

class AirportFactExtraction(BaseModel):
    distance_claims: list[DistanceClaim] = Field(
        default_factory=list
    )

    time_claims: list[TimeClaim] = Field(
        default_factory=list
    )


extractor_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a strict factual extraction engine.

Extract ONLY airport distance and airport travel-time claims
that are explicitly stated in the supplied source text.

Rules:

- Do not infer anything.
- Do not calculate anything.
- Do not convert units.
- Do not guess.
- Ignore distances to train stations, attractions,
  city centres, other cities or any non-airport location.
- A number must be clearly associated with an airport.
- If no valid airport fact exists, return an empty list.
- Preserve the exact numeric value found in the text.
- evidence must contain the short source text supporting the claim.
- Extract claims ONLY about the TARGET AIRPORT supplied by the user.
- Ignore distances or travel times for all other airports.
- Airport names may be shortened or slightly different, but they must clearly refer to the target airport.
- For example, if the target is Chhatrapati Shivaji International Airport,
  "Chhatrapati Shivaji", "Mumbai International Airport", or similar clear references may match.
- Lohegaon Airport, Surat Airport, or any other airport must be ignored.
Return ONLY valid JSON:

{{
    "distance_claims": [
        {{
            "value": 2.4,
            "unit": "km",
            "evidence": "Chhatrapati Shivaji International - 2.4 km"
        }}
    ],
    "time_claims": [
        {{
            "value": 15,
            "unit": "minutes",
            "evidence": "15 minutes drive from Chhatrapati Shivaji International airport"
        }}
    ]
}}
"""
        ),
        (
    "human",
    """
TARGET AIRPORT:
{target_airport}

SOURCE TEXT:

{content}
"""
)
    ]
)


extractor_chain = extractor_prompt | model

def extract_airport_claims(
    content: str,
) -> AirportFactExtraction:

    response = extractor_chain.invoke({
        "content": content,
    })

    raw_text = response.content.strip()

    if not raw_text:
        raise ValueError(
            "Empty airport extraction response"
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

    return AirportFactExtraction.model_validate(
        parsed
    )

def normalize_distance_to_km(
    value: float,
    unit: str,
) -> float:

    unit = unit.lower()

    if unit == "km":
        return round(value, 2)

    if unit in {"mile", "miles"}:
        return round(value * 1.60934, 2)

    raise ValueError(
        f"Unsupported distance unit: {unit}"
    )

def evaluate_airport_claims(
    extraction: AirportFactExtraction,
) -> dict:

    normalized_distances = []

    for claim in extraction.distance_claims:

        distance_km = normalize_distance_to_km(
            claim.value,
            claim.unit,
        )

        normalized_distances.append({
            "value_km": distance_km,
            "original_value": claim.value,
            "original_unit": claim.unit,
            "evidence": claim.evidence,
        })


    times_minutes = [
        {
            "value_minutes": claim.value,
            "evidence": claim.evidence,
        }
        for claim in extraction.time_claims
    ]


    unique_distances = sorted({
        item["value_km"]
        for item in normalized_distances
    })


    unique_times = sorted({
        item["value_minutes"]
        for item in times_minutes
    })


    return {
        "distance_claims": normalized_distances,
        "time_claims": times_minutes,

        "unique_distances_km":
            unique_distances,

        "unique_times_minutes":
            unique_times,

        "distance_conflict":
            len(unique_distances) > 1,

        "time_conflict":
            len(unique_times) > 1,
    }

def evaluate_cross_source_airport_evidence(
    source_evaluations: list[dict],
) -> dict:

    distance_claims = []
    time_claims = []

    for source in source_evaluations:

        url = source["url"]
        official_source = source.get(
            "official_source",
            False,
        )

        evaluation = source["evaluation"]

        for claim in evaluation["distance_claims"]:
            distance_claims.append({
                "url": url,
                "official_source": official_source,
                "value_km": claim["value_km"],
                "evidence": claim["evidence"],
            })

        for claim in evaluation["time_claims"]:
            time_claims.append({
                "url": url,
                "official_source": official_source,
                "value_minutes": claim["value_minutes"],
                "evidence": claim["evidence"],
            })


    unique_distances = sorted({
        claim["value_km"]
        for claim in distance_claims
    })

    unique_times = sorted({
        claim["value_minutes"]
        for claim in time_claims
    })


    distance_conflict = False

    if len(unique_distances) > 1:

        minimum = min(unique_distances)
        maximum = max(unique_distances)

        distance_conflict = (
            maximum - minimum > 2
        )


    time_conflict = False

    if len(unique_times) > 1:

        minimum_time = min(unique_times)
        maximum_time = max(unique_times)

        time_conflict = (
            maximum_time - minimum_time > 10
        )


    can_answer_distance_exactly = (
        len(unique_distances) == 1
        or not distance_conflict
    )


    can_answer_time_exactly = (
        len(unique_times) == 1
        or not time_conflict
    )


    return {
        "distance_claims": distance_claims,
        "time_claims": time_claims,

        "unique_distances_km":
            unique_distances,

        "unique_times_minutes":
            unique_times,

        "distance_conflict":
            distance_conflict,

        "time_conflict":
            time_conflict,

        "can_answer_distance_exactly":
            can_answer_distance_exactly,

        "can_answer_time_exactly":
            can_answer_time_exactly,
    }