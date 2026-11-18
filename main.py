
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")

if not API_KEY:
    raise ValueError("Please add your Gemini API key to the .env file.")

if not MODEL:
    raise ValueError("Please add GEMINI_MODEL to the .env file.")

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

# Initialize FastAPI
app = FastAPI(title="Fitness & Gym Coach Bot")


# System instructions
SYSTEM_INSTRUCTION = """
You are a helpful Fitness and Gym Coach Assistant.

Your responsibilities:
1. Answer general fitness and gym questions.
2. Explain gym equipment and its basic purpose.
3. Provide information about gym memberships and gym classes.
4. Explain general gym rules and etiquette.
5. Communicate in simple and friendly language.

Function calling instructions:
- When a user asks to book or check a session with a
  specific trainer on a specific day, use the book_session tool.
- Do not invent trainer availability.
- If the trainer or day is missing, ask the user for that information.
- Only confirm a booking when the tool returns success.
- Explain that bookings use mock demonstration data.

Safety guidelines:
- Do not diagnose medical conditions.
- Do not recommend extreme exercise routines.
- Encourage users to consult qualified professionals
  for personal medical or health concerns.
- Do not invent gym policies or membership details.

Stay focused on fitness and gym-related topics.
"""


# -----------------------------------
# DAY 3: MOCK GYM SESSION DATA
# -----------------------------------

gym_sessions = {
    "Ali": ["Monday", "Wednesday", "Friday"],
    "Sara": ["Tuesday", "Thursday", "Saturday"],
    "Ahmed": ["Monday", "Thursday", "Saturday"]
}


# -----------------------------------
# DAY 3: CUSTOM PYTHON FUNCTION
# -----------------------------------

def book_session(trainer: str, day: str):

    trainer_name = next(
        (
            name for name in gym_sessions
            if name.lower() == trainer.strip().lower()
        ),
        None
    )

    if trainer_name is None:
        return {
            "success": False,
            "message": f"Trainer {trainer} was not found."
        }

    requested_day = day.strip().title()

    if requested_day not in gym_sessions[trainer_name]:
        return {
            "success": False,
            "message": (
                f"{trainer_name} is not available on {requested_day}."
            )
        }

    return {
        "success": True,
        "trainer": trainer_name,
        "day": requested_day,
        "message": (
            f"Mock booking successful! "
            f"Your session with {trainer_name} is booked for {requested_day}."
        )
    }


# -----------------------------------
# DAY 3: GEMINI JSON TOOL DECLARATION
# -----------------------------------

book_session_declaration = types.FunctionDeclaration(
    name="book_session",
    description=(
        "Check trainer availability and book a mock gym session "
        "for the requested trainer and day."
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "trainer": {
                "type": "string",
                "description": "Name of the gym trainer."
            },
            "day": {
                "type": "string",
                "description": "Requested day of the week."
            }
        },
        "required": ["trainer", "day"]
    }
)


# Register the function declaration as a Gemini tool
book_session_tool = types.Tool(
    function_declarations=[book_session_declaration]
)


# -----------------------------------
# DAY 2 + DAY 3: WEBSOCKET ENDPOINT
# -----------------------------------

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):

    await websocket.accept()

    # Store conversation history for this connection
    messages = []

    try:
        while True:

            # Receive user message
            user_message = await websocket.receive_text()

            if not user_message.strip():
                continue

            # Add user message to conversation history
            messages.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=user_message)
                    ]
                )
            )

            # Tool-calling loop
            max_tool_rounds = 3

            for tool_round in range(max_tool_rounds):

                # Request Gemini response with streaming and tool
                stream = await client.aio.models.generate_content_stream(
                    model=MODEL,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7,
                        tools=[book_session_tool]
                    ),
                )

                bot_response = []
                function_call_parts = []

                # Receive response chunks
                async for chunk in stream:

                    # Stream normal text responses
                    if chunk.text:
                        bot_response.append(chunk.text)

                        await websocket.send_json({
                            "type": "token",
                            "content": chunk.text
                        })

                    # Detect function calls
                    for candidate in chunk.candidates or []:

                        if candidate.content:

                            for part in candidate.content.parts or []:

                                if part.function_call:
                                    function_call_parts.append(part)

                # -----------------------------------
                # CHECK WHETHER GEMINI REQUESTED A TOOL
                # -----------------------------------

                if not function_call_parts:

                    # No function call: save normal bot response
                    complete_response = "".join(bot_response)

                    if complete_response:
                        messages.append(
                            types.Content(
                                role="model",
                                parts=[
                                    types.Part.from_text(
                                        text=complete_response
                                    )
                                ]
                            )
                        )

                    break

                # Save Gemini's function-call message
                messages.append(
                    types.Content(
                        role="model",
                        parts=function_call_parts
                    )
                )

                # -----------------------------------
                # EXECUTE CUSTOM PYTHON FUNCTION
                # -----------------------------------

                function_response_parts = []

                for part in function_call_parts:

                    function_call = part.function_call

                    tool_name = function_call.name
                    tool_args = dict(function_call.args or {})

                    print(
                        f"Calling tool: {tool_name} "
                        f"with arguments: {tool_args}"
                    )

                    # Notify the WebSocket client
                    await websocket.send_json({
                        "type": "tool_call",
                        "name": tool_name,
                        "arguments": tool_args
                    })

                    # Execute the requested Python function
                    if tool_name == "book_session":

                        result = book_session(
                            trainer=str(tool_args.get("trainer", "")),
                            day=str(tool_args.get("day", ""))
                        )

                    else:
                        result = {
                            "success": False,
                            "message": "Unknown tool requested."
                        }

                    print("Tool result:", result)

                    # Prepare function response for Gemini
                    function_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={
                                "result": result
                            }
                        )
                    )

                

                # Send tool results back to Gemini
                messages.append(
                    types.Content(
                        role="user",
                        parts=function_response_parts
                    )
                )



            else:
                # Maximum tool-call rounds reached
                await websocket.send_json({
                    "type": "error",
                    "message": "Maximum tool-call rounds reached."
                })

            # Finish this conversation turn
            await websocket.send_json({
                "type": "done"
            })

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as error:  
        print("WebSocket error:", error)

        try:
            await websocket.send_json({
                "type": "error",
                "message": "The bot encountered an error. Please try again."
            })

            await websocket.send_json({
                "type": "done"
            })

        except Exception:
            pass

