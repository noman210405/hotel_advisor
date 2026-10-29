from app.services.web_search_service import research_hotel


result = research_hotel(
    hotel_name="Rixos The Palm Hotel & Suites",
    destination="Dubai",
    address="Palm Jumeirah, East Crescent"
)

for source in result["web_evidence"]:
    print(source["title"])
    print("verified:", source["verified"])
    print("official:", source["official_source"])
    print("name ratio:", source["hotel_match_ratio"])
    print("destination:", source["destination_match"])
    print("address:", source["address_match"])
    print()