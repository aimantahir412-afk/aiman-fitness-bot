
import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from faq_search import search_faq


# -----------------------------------
# ENVIRONMENT SETUP
# -----------------------------------

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL")

if not API_KEY:
    raise ValueError("Please add your Gemini API key to the .env file.")

if not MODEL:
    raise ValueError("Please add GEMINI_MODEL to the .env file.")

client = genai.Client(api_key=API_KEY)

app = FastAPI(title="Fitness & Gym Coach Bot")


# -----------------------------------
# SYSTEM INSTRUCTIONS
# -----------------------------------

SYSTEM_INSTRUCTION = """
You are a helpful Fitness and Gym Coach Assistant.

Your responsibilities:
1. Answer general fitness and gym questions.
2. Explain gym equipment and its basic purpose.
3. Provide information about gym memberships and gym classes.
4. Explain general gym rules and etiquette.
5. Communicate in simple and friendly language.

FUNCTION CALLING INSTRUCTIONS:

1. BOOK_SESSION:
- When a user asks to book or check a session with
  a specific trainer on a specific day, use book_session.
- If the trainer or day is missing, ask for that information.
- Do not invent trainer availability.
- Only confirm a booking when the tool returns success.
- Explain that bookings use mock demonstration data.

2. SEARCH_FAQ:
- When a user asks about memberships, classes,
  gym policies, or gym rules, use search_faq.
- Use the information returned by the FAQ tool
  to answer the user's question.
- Do not invent gym policies or membership details.
- If no relevant FAQ is found, explain that the
  information is not available in the knowledge base.

SAFETY GUIDELINES:
- Do not diagnose medical conditions.
- Do not recommend extreme exercise routines.
- Encourage users to consult qualified professionals
  for personal medical or health concerns.

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
# DAY 3: BOOK SESSION FUNCTION
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
# DAY 3: BOOK SESSION TOOL DECLARATION
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


# -----------------------------------
# DAY 4: FAQ SEARCH TOOL DECLARATION
# -----------------------------------

search_faq_declaration = types.FunctionDeclaration(
    name="search_faq",
    description=(
        "Search the FitZone Gym FAQ knowledge base for accurate "
        "information about memberships, fitness classes, and gym rules."
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The user's question about gym policies."
            }
        },
        "required": ["question"]
    }
)


# -----------------------------------
# REGISTER BOTH GEMINI TOOLS
# -----------------------------------

gym_tools = types.Tool(
    function_declarations=[
        book_session_declaration,
        search_faq_declaration
    ]
)


# -----------------------------------
# DAY 2 + DAY 3 + DAY 4: WEBSOCKET
# -----------------------------------

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):

    await websocket.accept()

    # Conversation memory for this connection
    messages = []

    try:
        while True:

            # Receive user message
            user_message = await websocket.receive_text()

            if not user_message.strip():
                continue

            # Save user message
            messages.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=user_message)
                    ]
                )
            )

            # Allow multiple tool calls in one conversation turn
            max_tool_rounds = 3

            for tool_round in range(max_tool_rounds):

                # Request Gemini response with both tools
                stream = await client.aio.models.generate_content_stream(
                    model=MODEL,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7,
                        tools=[gym_tools]
                    ),
                )

                bot_response = []
                function_call_parts = []

                # Receive streaming response
                async for chunk in stream:

                    # Stream normal text
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
                # CHECK FOR FUNCTION CALLS
                # -----------------------------------

                if not function_call_parts:

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

                # Save Gemini function-call message
                messages.append(
                    types.Content(
                        role="model",
                        parts=function_call_parts
                    )
                )

                # -----------------------------------
                # EXECUTE REQUESTED TOOLS
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

                    # Notify WebSocket client
                    await websocket.send_json({
                        "type": "tool_call",
                        "name": tool_name,
                        "arguments": tool_args
                    })

                    # Execute book_session
                    if tool_name == "book_session":

                        result = book_session(
                            trainer=str(tool_args.get("trainer", "")),
                            day=str(tool_args.get("day", ""))
                        )

                    # Execute search_faq
                    elif tool_name == "search_faq":

                        result = search_faq(
                            question=str(tool_args.get("question", ""))
                        )

                    else:

                        result = {
                            "success": False,
                            "message": "Unknown tool requested."
                        }

                    print("Tool result:", result)

                    # Prepare response for Gemini
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

                await websocket.send_json({
                    "type": "error",
                    "message": "Maximum tool-call rounds reached."
                })

            # Finish conversation turn
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
