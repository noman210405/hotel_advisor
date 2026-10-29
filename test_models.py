from app.models.comparison import ComparisonRequest


data = {
    "destination": "Antalya",
    "adults": 2,
    "children": 2,
    "child_ages": [4, 7],
    "hotels": [
    {
        "hotel_name": "Rixos Downtown Antalya",
        "price": 3550.20,
        "currency": "GBP"
    }
    ]
}

comparison = ComparisonRequest(**data)

print(comparison)
print()
print(comparison.hotels[0].hotel_name)