from typing import Optional, List, Literal

from pydantic import BaseModel, Field


class SelectedOffer(BaseModel):
    room_name: Optional[str] = None
    board_basis: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    refundable: Optional[bool] = None
    deadline: Optional[str] = None


class HotelComparisonItem(BaseModel):
    hotel_code: Optional[str] = None
    hotel_name: str
    address: Optional[str] = None
    rating: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    amenities: List[str] = Field(default_factory=list)
    selected_offer: SelectedOffer


class ComparisonPreferences(BaseModel):
    priorities: List[str] = Field(default_factory=list)
    custom_requirement: Optional[str] = None
    price_preference: Literal[
        "cheapest_possible",
        "best_value",
        "price_less_important",
    ] = "best_value"


class ComparisonRequest(BaseModel):
    destination: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    child_ages: Optional[List[int]] = None
    comparison_preferences: Optional[ComparisonPreferences] = None
    hotels: List[HotelComparisonItem] = Field(min_length=2, max_length=4)


class HotelComparisonResult(BaseModel):
    hotel_name: str
    price: Optional[float] = None
    currency: Optional[str] = None
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    recommendation_reason: Optional[str] = None


class ComparisonResponse(BaseModel):
    recommended_hotel: Optional[str] = None
    cheapest_hotel: Optional[str] = None
    price_difference: Optional[float] = None
    session_id: Optional[str] = None
    summary: Optional[str] = None
    hotels: List[HotelComparisonResult]


class RateLocComparisonRequest(BaseModel):
    destination: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    child_ages: Optional[List[int]] = None
    comparison_preferences: Optional[ComparisonPreferences] = None
    hotels: List[dict] = Field(min_length=2, max_length=4)


class AIHotelResult(BaseModel):
    hotel_name: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    recommendation_reason: Optional[str] = None


class AIComparisonResult(BaseModel):
    recommended_hotel: str
    summary: str
    hotels: List[AIHotelResult]
