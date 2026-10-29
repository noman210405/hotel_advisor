from app.services.web_search_service import (
    research_hotel_question,
)

from app.services.research_extractor import (
    extract_airport_claims,
    evaluate_airport_claims,
    evaluate_cross_source_airport_evidence,
)   


result = research_hotel_question(
    hotel_name="Sofitel Mumbai BKC",
    destination="Mumbai",
    address="C 57 Bandra Kurla Complex",
    question="How far is the hotel from Mumbai airport?",
)


all_evaluations = []

for source in result["web_evidence"]:

    extraction = extract_airport_claims(
        source["content"],
        target_airport="Chhatrapati Shivaji International Airport",
    )

    evaluation = evaluate_airport_claims(
        extraction
    )

    all_evaluations.append({
        "url": source["url"],
        "official_source": source.get(
            "official_source",
            False,
        ),
        "evaluation": evaluation,
    })


# IMPORTANT:
# This must be OUTSIDE the loop
cross_source_result = (
    evaluate_cross_source_airport_evidence(
        all_evaluations
    )
)


print("\nCROSS SOURCE RESULT:")
print(cross_source_result)


print("\nREAL SOURCE EVALUATIONS:")

for item in all_evaluations:

    print("\nSOURCE:")
    print(item["url"])

    print("OFFICIAL:")
    print(item["official_source"])

    print("EVALUATION:")
    print(item["evaluation"])