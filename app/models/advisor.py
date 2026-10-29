from typing import Optional, List

from pydantic import BaseModel, Field


class AdvisorHotelContext(BaseModel):
    hotel_name: str

    address: Optional[str] = None
    rating: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    price: Optional[float] = None
    currency: Optional[str] = None

    room_name: Optional[str] = None
    board_basis: Optional[str] = None
    refundable: Optional[bool] = None
    deadline: Optional[str] = None

    amenities: List[str] = Field(default_factory=list)
    web_evidence: List[dict] = Field(default_factory=list)

class AdvisorChatMessage(BaseModel):
    role: str
    content: str
    
class AdvisorRequest(BaseModel):
    destination: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    child_ages: Optional[List[int]] = None
    history: List[AdvisorChatMessage] = Field(default_factory=list)

    recommended_hotel: Optional[str] = None
    session_id: Optional[str] = None

    question: str

    hotels: List[AdvisorHotelContext]


class AdvisorResponse(BaseModel):
    answer: str
    recommended_hotel: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)

