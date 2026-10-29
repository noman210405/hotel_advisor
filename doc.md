# RateLoc AI Hotel Advisor — Internal Notes

## Core Principle

**AI interprets; backend decides.**

Never let the LLM invent or decide:
- Hotel prices
- Availability
- Selected rooms
- Board basis
- Refundability
- Cancellation deadlines
- Cheapest hotel
- Supplier/RateLoc booking facts

Unknown values must remain unknown.

---

## Current Architecture

```text
RateLoc Search API
→ Hotel results
→ User selects 2–3 hotels
→ Comparison preferences
→ Tavily hotel research
→ Verified evidence
→ Comparison context
→ Groq LLM
→ Backend safety filters
→ Comparison UI
→ Saved comparison session
→ Hotel Advisor
```

### Current Model

Comparison + Advisor:
- Groq `openai/gpt-oss-20b`

Web research:
- Tavily Search

Nemotron 3 Ultra and Nemotron 3.5 Lightning were tested via OpenRouter.
- Ultra quality was better but too slow.
- Lightning free endpoint had very poor latency.
- Groq is currently preferred for MVP because it is much faster when combined with backend safeguards.

---

## Sources of Truth

### RateLoc API
Authoritative for:
- Price
- Currency
- Room
- Board basis
- Refundability
- Cancellation deadline
- Live hotel/search information

### Verified Web Evidence
May confirm:
- Swimming pools
- Kids clubs
- Spa/gym
- Restaurants
- Beach access
- Airport information
- Hotel location
- Child policies
- Other descriptive hotel facilities

Missing web/RateLoc data does **not** mean the hotel does not have a facility.

---

## Comparison Flow

`comparison_engine.py`

1. Calculate price facts in Python.
2. Run Tavily research for selected hotels.
3. Build AI comparison context.
4. Send context to Groq.
5. Validate/filter generated claims.
6. Return final comparison.
7. Save comparison context using `session_id`.

Python controls:
- Cheapest hotel
- Price difference
- Price ranking

The LLM should only explain these facts.

---

## Safety Filters Added

Backend filters currently protect against:

### Unsupported negatives
Examples:
- "No swimming pool"
- "No gym"
- "No kids club"

These must not be stated unless evidence explicitly confirms absence.

### Unsupported room claims
Hotel-level facilities must not automatically become room inclusions.

Example:

```text
Hotel has private pool villas
≠
Selected Garden Suite has private pool
```

### Free / complimentary claims

```text
Airport shuttle available
≠
Complimentary airport shuttle
```

Free/complimentary wording requires explicit evidence.

### Unsupported comparisons
Claims such as:
- "limited pool facilities"
- "fewer amenities"
- "fewer pool options"

are filtered when not reliably supported.

---

## Advisor

The Advisor receives:
- Selected hotels
- Traveller details
- Conversation history
- Recommended hotel
- Saved comparison session
- Comparison web evidence
- Fresh research when required

The comparison `session_id` is reused so the Advisor sees the same evidence as the comparison.

This fixed contradictions such as:

```text
Comparison: Kayon has a pool
Advisor: Kayon has no confirmed pool
```

The Advisor now sees the saved Tavily evidence.

---

## Question Routing

Current Advisor intent categories:

- `booking_fact`
- `location`
- `hotel_fact`
- `destination_fact`
- `temporal`
- `general`

Examples:

```text
price / room / refund → booking_fact
airport / distance / drive → location
pool / spa / kids club → hotel_fact
best time to visit → destination_fact
events / festivals → temporal
```

---

## Key Lesson

A stronger LLM alone did not solve hallucinations.

Best current architecture:

```text
Groq
+ Tavily
+ RateLoc facts
+ session evidence
+ Python validation
```

The backend must enforce factual boundaries.

---

## Next Work

Immediate next milestone:

1. Reuse saved comparison evidence before calling Tavily again.
2. Research only the hotel relevant to the user's question.
3. Avoid duplicate Tavily searches.
4. Cache verified hotel facts.
5. Build a proper evaluation suite.
6. Later consider Supabase + RAG for persistent hotel knowledge.
7. Consider vLLM/self-hosting only when real usage/concurrency justifies it.

---

## Long-Term Direction

```text
RateLoc live data
+ verified hotel knowledge
+ deterministic backend rules
+ LLM interpretation
+ evaluation
+ caching/RAG
→ reliable production Hotel Advisor
```