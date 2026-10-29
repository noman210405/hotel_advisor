import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def test_openai_connection():

    response = client.responses.create(
        model="gpt-4.1-mini",
        input="Reply with exactly: OpenAI connection working"
    )

    return response.output_text