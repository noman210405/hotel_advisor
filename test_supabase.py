from app.services.research_cache_service import supabase


response = (
    supabase
    .table("hotel_research_cache")
    .select("*")
    .limit(1)
    .execute()
)

print("SUPABASE CONNECTED")
print(response.data)