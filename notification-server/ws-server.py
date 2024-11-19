import asyncio
import websockets

CONNECTIONS = set()


async def handler(websocket):
    if websocket not in CONNECTIONS:
        print(f"New connection: {websocket.remote_address}")
        CONNECTIONS.add(websocket)
    async for message in websocket:
        print(f"Received message from {websocket.remote_address}: {message}")
        websockets.broadcast(CONNECTIONS, message)


async def main():
    async with websockets.serve(handler, "localhost", 8765, ping_timeout=None):
        print("WS Server started.")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
