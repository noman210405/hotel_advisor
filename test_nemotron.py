from app.services.llm_service import nemotron_model


response = nemotron_model.invoke(
    "Reply with exactly: Nemotron connected"
)

print(response.content)