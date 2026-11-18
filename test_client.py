
import asyncio
import json
import websockets


async def test_chatbot():

    uri = "ws://127.0.0.1:8000/ws/chat"

    questions = [
        "Please book a gym session with trainer Ali on Monday."
    ]

    async with websockets.connect(uri) as websocket:

        for question in questions:

            print("\nYou:", question)
            await websocket.send(question)

            print("\nFitness Bot:", end=" ", flush=True)

            while True:

                response = json.loads(await websocket.recv())

                if response["type"] == "tool_call":
                    print(
                        f"\n[TOOL CALLED: {response['name']}]"
                    )
                    print("Arguments:", response["arguments"])

                elif response["type"] == "token":
                    print(response["content"], end="", flush=True)

                elif response["type"] == "error":
                    print("\nError:", response["message"])

                elif response["type"] == "done":
                    print("\n")
                    break


if __name__ == "__main__":
    asyncio.run(test_chatbot())

