
import asyncio
import json
import websockets


async def test_chatbot():

    uri = "ws://127.0.0.1:8000/ws/chat"

    questions = [
        "I am new to exercise. What is a warm-up?",
        "Why is it important before a workout?",
        "How long should I warm up?"
    ]

    async with websockets.connect(uri) as websocket:

        for question in questions:

            print("\nYou:", question)
            await websocket.send(question)

            print("Fitness Bot: ", end="", flush=True)

            while True:

                response = json.loads(await websocket.recv())

                if response["type"] == "token":
                    print(response["content"], end="", flush=True)

                elif response["type"] == "done":
                    print()
                    break


if __name__ == "__main__":
    asyncio.run(test_chatbot())
