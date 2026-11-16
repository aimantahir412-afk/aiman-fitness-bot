from google.genai import types
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")

if not API_KEY:
    raise ValueError("Please add your Gemini API key to the .env file.")

client = genai.Client(api_key=API_KEY)

SYSTEM_INSTRUCTION = """
You are a helpful Fitness and Gym Coach Assistant.

Your responsibilities:
1. Answer general fitness and gym questions.
2. Explain gym equipment and its basic purpose.
3. Provide general information about gym memberships and classes.
4. Explain gym rules and etiquette.
5. Communicate in simple and friendly language.

Safety guidelines:
- Do not diagnose medical conditions.
- Do not recommend extreme exercise routines.
- Encourage users to consult qualified professionals
  for personal medical or health concerns.
- Do not invent gym policies or membership details.

Stay focused on fitness and gym-related topics.
"""

def get_bot_response(user_question):
    response = client.models.generate_content(
        model=MODEL,
        contents=user_question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        ),
    )

    return response.text


if __name__ == "__main__":
    print("=" * 45)
    print("FITNESS & GYM COACH BOT")
    print("=" * 45)

    question = input("\nYou: ")

    try:
        answer = get_bot_response(question)
        print("\nFitness Bot:", answer)
    except Exception as error:
        print("\nError:", error)
    finally:
        client.close()