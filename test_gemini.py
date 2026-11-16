
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={"timeout": 15000}
)

print("Testing Gemini connection...")

try:
    start = time.time()

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Reply with exactly: Hello, connection works!"
    )

    print("\nResponse:", response.text)
    print("Time taken:", round(time.time() - start, 2), "seconds")

except Exception as error:
    print("\nTEST FAILED:")
    print(type(error).__name__)
    print(error)

finally:
    client.close()
