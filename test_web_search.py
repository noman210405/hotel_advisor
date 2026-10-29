from app.services.web_search_service import (
    search_hotel,
    prepare_web_evidence,
)


result = search_hotel(
    hotel_name="Rixos The Palm Hotel & Suites",
    destination="Dubai"
)

evidence = prepare_web_evidence(result)

for item in evidence:
    print("\nSOURCE:")
    print(item["title"])
    print(item["url"])

    print("\nEVIDENCE:")
    print(item["content"])

    print("\nSCORE:")
    print(item["score"])