
import asyncio
import json
import websockets


async def test_faq():

    uri = "ws://127.0.0.1:8000/ws/chat"

    async with websockets.connect(uri) as websocket:

        question = "Can I pause my gym membership?"

        print("User:", question)

        await websocket.send(question)

        print("\nBot response:")

        while True:

            response = json.loads(await websocket.recv())

            if response["type"] == "tool_call":
                print("\nTool called:", response["name"])
                print("Arguments:", response["arguments"])

            elif response["type"] == "token":
                print(response["content"], end="", flush=True)

            elif response["type"] == "error":
                print("\nError:", response["message"])

            elif response["type"] == "done":
                print("\n\nTest completed!")
                break


if __name__ == "__main__":
    asyncio.run(test_faq())
