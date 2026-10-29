from app.services.rateloc_adapter import build_comparison_request


rateloc_hotels = [
    {
        "uniqueCode": "39673736",
        "title": "Rixos The Palm Hotel & Suites",
        "address": "Palm Jumeirah, East Crescent",
        "rating": "5",
        "amenities": [
            "Airport Shuttle",
            "Children's Club",
            "Free Wi-Fi",
            "Spa & Wellness Centre"
        ],
        "latitude": 25.122044,
        "longitude": 55.154120,
        "roomName": "Junior Suite (One Bedroom) Double",
        "boardBase": "Ultra All Inclusive",
        "deadline": "08-11-2026",
        "price": {
            "totalPrice": 279008.66,
            "currency": "INR"
        },
        "refundable": True
    },
    {
        "uniqueCode": "TEST002",
        "title": "Test Hotel Two",
        "address": "Dubai",
        "rating": "5",
        "amenities": [
            "Swimming Pool",
            "Free Wi-Fi",
            "Fitness Centre"
        ],
        "latitude": 25.2,
        "longitude": 55.25,
        "roomName": "Deluxe Room",
        "boardBase": "All Inclusive",
        "deadline": None,
        "price": {
            "totalPrice": 310000,
            "currency": "INR"
        },
        "refundable": False
    }
]


comparison_request = build_comparison_request(
    destination="Dubai",
    adults=2,
    children=2,
    child_ages=[8, 12],
    rateloc_hotels=rateloc_hotels,
)


print(comparison_request)