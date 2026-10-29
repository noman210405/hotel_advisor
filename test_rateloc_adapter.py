from app.services.rateloc_adapter import map_rateloc_rate


rate = {
    "roomInformation": {
        "rawRoomName": "Junior Suite (One Bedroom) Double",
        "roomPromotion": "",
        "boardBase": "Ultra All Inclusive",
        "roomName": "Junior Suite (One Bedroom) Double",
        "paymentType": "Refundable"
    },
    "price": {
        "totalPrice": 279008.66,
        "currency": "INR",
        "perNightPrice": 93002.89
    },
    "supplier": "113",
    "accId": "12245",
    "refundable": True,
    "deadline": "08-11-2026",
    "actualDeadline": "15-11-2026"
}


hotel = map_rateloc_rate(
    hotel_name="TEST HOTEL",
    rate=rate
)

print(hotel)