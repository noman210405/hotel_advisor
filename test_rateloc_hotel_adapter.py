from app.services.rateloc_adapter import map_rateloc_hotel


rateloc_hotel = {
    "uniqueCode": "39673736",
    "title": "Rixos The Palm Hotel & Suites",
    "address": "Palm Jumeirah, East Crescent",
    "rating": "5",
    "amenities": [
        "Television",
        "Airport Shuttle",
        "Children's Club",
        "Free Wi-Fi",
        "Spa & Wellness Centre"
    ],
    "latitude": 25.122044,
    "longitude": 55.154120,
    "roomName": "Junior Suite (One Bedroom) Double",
    "boardBase": "Ultra All Inclusive",
    "paymentType": "Refundable",
    "deadline": "08-11-2026",
    "price": {
        "totalPrice": 279008.66,
        "currency": "INR"
    },
    "refundable": True
}


hotel = map_rateloc_hotel(rateloc_hotel)

print(hotel)