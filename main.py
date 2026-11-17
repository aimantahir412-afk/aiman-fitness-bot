
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")

if not API_KEY:
    raise ValueError("Please add your Gemini API key to the .env file.")

if not MODEL:
    raise ValueError("Please add GEMINI_MODEL to the .env file.")

client = genai.Client(api_key=API_KEY)

app = FastAPI(title="Fitness & Gym Coach Bot")

SYSTEM_INSTRUCTION = """
You are a helpful Fitness and Gym Coach Assistant.

Your responsibilities:
1. Answer general fitness and gym questions.
2. Explain gym equipment and its basic purpose.
3. Provide information about gym memberships and gym classes.
4. Explain general gym rules and etiquette.
5. Communicate in simple and friendly language.

Safety guidelines:
- Do not diagnose medical conditions.
- Do not recommend extreme exercise routines.
- Encourage users to consult qualified professionals
  for personal medical or health concerns.
- Do not invent gym policies or membership details.

Stay focused on fitness and gym-related topics.
"""


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):

    await websocket.accept()

    # Store conversation history for this connection
    messages = []

    try:
        while True:

            # Receive message from the user
            user_message = await websocket.receive_text()

            if not user_message.strip():
                continue

            # Add user's message to conversation history
            messages.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)]
                )
            )

            bot_response = []

            # Generate a streaming response
            stream = await client.aio.models.generate_content_stream(
                model=MODEL,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.7,
                ),
            )

            # Send response chunks one by one
            async for chunk in stream:

                if chunk.text:
                    bot_response.append(chunk.text)

                    await websocket.send_json({
                        "type": "token",
                        "content": chunk.text
                    })

            # Save the complete bot response
            complete_response = "".join(bot_response)

            messages.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text=complete_response)
                    ]
                )
            )

            # Tell the client this turn is finished
            await websocket.send_json({
                "type": "done"
            })

    except WebSocketDisconnect:
        print("Client disconnected")
