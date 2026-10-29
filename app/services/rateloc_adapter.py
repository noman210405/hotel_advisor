from app.models.comparison import (
    HotelComparisonItem,
    SelectedOffer,
    ComparisonRequest,
    ComparisonPreferences,
)


def map_rateloc_hotel(rateloc_hotel: dict) -> HotelComparisonItem:
    price_info = rateloc_hotel.get("price", {})

    selected_offer = SelectedOffer(
        room_name=rateloc_hotel.get("roomName"),
        board_basis=rateloc_hotel.get("boardBase"),
        price=price_info.get("totalPrice"),
        currency=price_info.get("currency"),
        refundable=rateloc_hotel.get("refundable"),
        deadline=rateloc_hotel.get("deadline"),
    )

    return HotelComparisonItem(
        hotel_code=rateloc_hotel.get("uniqueCode"),
        hotel_name=rateloc_hotel.get("title"),
        address=rateloc_hotel.get("address"),
        rating=int(rateloc_hotel["rating"])
        if rateloc_hotel.get("rating") is not None
        else None,
        latitude=rateloc_hotel.get("latitude"),
        longitude=rateloc_hotel.get("longitude"),
        amenities=rateloc_hotel.get("amenities", []),
        selected_offer=selected_offer,
    )


def build_comparison_request(
    destination: str,
    adults: int,
    children: int,
    child_ages: list[int],
    rateloc_hotels: list[dict],
    comparison_preferences: ComparisonPreferences | None = None,
) -> ComparisonRequest:
    hotels = [
        map_rateloc_hotel(hotel)
        for hotel in rateloc_hotels
    ]

    return ComparisonRequest(
        destination=destination,
        adults=adults,
        children=children,
        child_ages=child_ages,
        comparison_preferences=comparison_preferences,
        hotels=hotels,
    )
