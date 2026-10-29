from app.models.comparison import ComparisonRequest


def calculate_price_comparison(request: ComparisonRequest):

    priced_hotels = [
        hotel
        for hotel in request.hotels
        if (
            hotel.selected_offer.price is not None
            and hotel.selected_offer.currency is not None
        )
    ]

    currencies = {
        hotel.selected_offer.currency
        for hotel in priced_hotels
    }

    cheapest_hotel = None
    price_difference = None

    if len(priced_hotels) >= 2 and len(currencies) == 1:

        sorted_hotels = sorted(
            priced_hotels,
            key=lambda hotel: hotel.selected_offer.price
        )

        cheapest_hotel = sorted_hotels[0].hotel_name

        price_difference = round(
            sorted_hotels[-1].selected_offer.price
            - sorted_hotels[0].selected_offer.price,
            2
        )

    return cheapest_hotel, price_difference