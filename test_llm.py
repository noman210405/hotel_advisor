from app.services.llm_service import generate_hotel_comparison


context = {
    "destination": "Dubai",
    "adults": 2,
    "children": 2,
    "child_ages": [8, 12],
    "hotels": [
        {
            "hotel_name": "Rixos The Palm Hotel & Suites",
            "amenities": [
                "Children's Club",
                "Airport Shuttle",
                "Free Wi-Fi"
            ],
            "selected_offer": {
                "room_name": "Junior Suite",
                "board_basis": "Ultra All Inclusive",
                "price": 279008.66,
                "currency": "INR",
                "refundable": True
            }
        },
        {
            "hotel_name": "Hotel B",
            "amenities": [
                "Free Wi-Fi",
                "Fitness Centre"
            ],
            "selected_offer": {
                "room_name": "Deluxe Room",
                "board_basis": "All Inclusive",
                "price": 310000,
                "currency": "INR",
                "refundable": False
            }
        }
    ]
}


result = generate_hotel_comparison(context)

print(result)

print("\nJSON:")
print(result.model_dump_json(indent=2))