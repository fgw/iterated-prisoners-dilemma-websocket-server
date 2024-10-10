import asyncio
from websockets.sync.client import connect

def hello():
    with connect("ws://localhost:8000/67fdcfb0-a8d4-436b-93cf-df6a3eaac62d?participant=a", additional_headers={'authorization': "asdf"}) as websocket:
    # with connect("ws://localhost:8000/67fdcfb0-a8d4-436b-93cf-df6a3eaac62d", additional_headers={'authorization': "asdf"}) as websocket:
    # with connect("ws://localhost:8000?participant=a", additional_headers={'authorization': "asdf"}) as websocket:
        websocket.send("Hello world!")
        message = websocket.recv()
        print(f"Received: {message}")

hello()