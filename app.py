
import json
import uuid

import streamlit as st
import websocket


# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------

st.set_page_config(
    page_title="FitZone Gym Assistant",
    page_icon="💪",
    layout="centered"
)

st.title("💪 FitZone Gym Assistant")
st.caption("Your friendly Fitness & Gym Coach")


# -----------------------------------
# WEBSOCKET CONFIGURATION
# -----------------------------------

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/chat"


# -----------------------------------
# SESSION STATE
# -----------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


# -----------------------------------
# DISPLAY CHAT HISTORY
# -----------------------------------

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -----------------------------------
# CHAT INPUT
# -----------------------------------

user_input = st.chat_input(
    "Ask me about gym memberships, classes, or fitness..."
)


# -----------------------------------
# PROCESS USER MESSAGE
# -----------------------------------

if user_input:

    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):

        response_placeholder = st.empty()
        response_text = ""
        ws = None

        try:

            # Open a fresh connection for this question
            ws = websocket.create_connection(
                WEBSOCKET_URL,
                timeout=120
            )

            # Send session ID and message
            request_data = {
                "session_id": st.session_state.session_id,
                "message": user_input
            }

            ws.send(json.dumps(request_data))

            # Receive response
            while True:

                raw_response = ws.recv()
                response = json.loads(raw_response)

                event_type = response.get("type")

                if event_type == "token":

                    response_text += response.get("content", "")
                    response_placeholder.markdown(response_text)

                elif event_type == "tool_call":

                    tool_name = response.get("name", "unknown")
                    st.caption(f"🔧 Using tool: {tool_name}")

                elif event_type == "error":

                    raise RuntimeError(
                        response.get(
                            "message",
                            "Unknown server error"
                        )
                    )

                elif event_type == "done":

                    break

            if not response_text:
                response_placeholder.info(
                    "The assistant did not return a text response."
                )

        except Exception as error:

            response_text = (
                "Unable to complete your request. "
                "Please check the chatbot server and try again."
            )

            response_placeholder.error(response_text)
            st.caption(f"Technical details: {error}")

        finally:

            # Close this question's connection
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_text
        })
