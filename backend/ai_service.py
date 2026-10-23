import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def analyze_release(release_text: str):
    if client is None:
        raise ValueError("GEMINI_API_KEY missing in .env")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Analyze this possible AI product release. "
            "Summarize the tool, its use case, and official URL. "
            "Do not invent facts; mark unknown details as unverified.\n\n"
            + release_text
        ),
    )
    return response.text