from app.services.hotel_fact_service import (
    build_compact_fact_context,
)


HOTEL_CODE = "39664118"


facts = build_compact_fact_context(
    HOTEL_CODE
)

print("COMPACT HOTEL FACTS:")
print()

for fact in facts:
    print(fact)