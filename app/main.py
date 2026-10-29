from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from app.services.comparison_service import (calculate_price_comparison)
from app.services.ai_comparison_service import build_comparison_context
from app.services.rateloc_adapter import build_comparison_request
from app.models.advisor import AdvisorRequest, AdvisorResponse
from app.services.advisor_service import answer_advisor_question
from app.services.comparison_engine import run_comparison
from app.models.comparison import (
    ComparisonRequest,
    ComparisonResponse,
    RateLocComparisonRequest
)
from app.services.rateloc_api_service import (
    start_hotel_search,
    stream_hotel_search,
)

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

@app.get("/")
def home():
    return FileResponse(
        "app/static/index.html"
    )
@app.post("/compare", response_model=ComparisonResponse)
def compare_hotels(request: ComparisonRequest):
    return run_comparison(request)

@app.post("/compare/rateloc", response_model=ComparisonResponse)
def compare_rateloc_hotels(request: RateLocComparisonRequest):

    comparison_request = build_comparison_request(
        destination=request.destination,
        adults=request.adults,
        children=request.children,
        child_ages=request.child_ages,
        rateloc_hotels=request.hotels,
        comparison_preferences=request.comparison_preferences,
    )

    return run_comparison(comparison_request)

@app.post("/advisor", response_model=AdvisorResponse)
def advisor(request: AdvisorRequest):

    try:
        return answer_advisor_question(request)

    except Exception as error:
        print(
            f"Advisor unavailable: "
            f"{type(error).__name__}: {error}"
        )

        return AdvisorResponse(
            answer="Hotel Advisor is temporarily unavailable.",
            recommended_hotel=None,
            reasons=[]
        )

@app.post("/rateloc/search")
async def rateloc_search(payload: dict):

    try:
        return await start_hotel_search(payload)

    except Exception as error:
        print(
            f"RateLoc search failed: "
            f"{type(error).__name__}: {error}"
        )

        return {
            "status": False,
            "message": "RateLoc hotel search failed"
        }

@app.get("/rateloc/search/{search_id}/stream")
async def rateloc_search_stream(search_id: str):

    return StreamingResponse(
        stream_hotel_search(search_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )