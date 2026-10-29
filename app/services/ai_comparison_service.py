from app.models.comparison import ComparisonRequest
from app.services.hotel_fact_service import (
    build_compact_fact_context,
)

def build_comparison_context(
    request: ComparisonRequest,
    web_research: list[dict] | None = None,
):
    research_by_hotel = {}

    if web_research:
        research_by_hotel = {
            item["hotel_name"]: item.get("web_evidence", [])
            for item in web_research
        }

    hotels = []

    for hotel in request.hotels:
        structured_facts = build_compact_fact_context(
            hotel.hotel_code
        )
        hotels.append({
            "hotel_code": hotel.hotel_code,
            "hotel_name": hotel.hotel_name,
            "address": hotel.address,
            "rating": hotel.rating,
            "latitude": hotel.latitude,
            "longitude": hotel.longitude,
            "amenities": hotel.amenities,
            "selected_offer": {
                "room_name": hotel.selected_offer.room_name,
                "board_basis": hotel.selected_offer.board_basis,
                "price": hotel.selected_offer.price,
                "currency": hotel.selected_offer.currency,
                "refundable": hotel.selected_offer.refundable,
                "deadline": hotel.selected_offer.deadline,
            },
            "structured_facts": structured_facts,

            "web_evidence": (
                []
                if structured_facts
                else research_by_hotel.get(
                    hotel.hotel_name,
                    []
                )
            ),
        })

    if request.children and request.children > 0:
        traveller_type = "family"
    elif request.adults == 1:
        traveller_type = "solo"
    else:
        traveller_type = "adults"

    preferences = (
        request.comparison_preferences.model_dump()
        if request.comparison_preferences
        else {
            "priorities": [],
            "custom_requirement": None,
            "price_preference": "best_value",
        }
    )

    return {
        "destination": request.destination,
        "traveller_profile": {
            "traveller_type": traveller_type,
            "adults": request.adults,
            "children": request.children,
            "child_ages": request.child_ages,
        },
        "comparison_preferences": preferences,
        "hotels": hotels,
    }
