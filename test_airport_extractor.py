from app.services.research_extractor import (
    extract_airport_claims,
    evaluate_airport_claims,
)


content = """
Easy access to highways & Chhatrapati Shivaji Intl Airport
- 12 KM, 45 min from Chhatrapati Shivaji airport.
204 KM from Pune.

Nearby Airports:
Chhatrapati Shivaji - 1 mile north.
"""


result = extract_airport_claims(
    content
)
evaluation = evaluate_airport_claims(
    result
)

print("EXTRACTED:")
print(
    result.model_dump()
)

print("\nEVALUATED:")
print(
    evaluation
)