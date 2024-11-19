# websocket_server.py

import asyncio
import websockets
from typing import Set, Dict, Any

class WebSocketServer:
    def __init__(self, host: str = 'localhost', port: int = 8765) -> None:
        self.host: str = host
        self.port: int = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        self.clients.add(websocket)
        # try:
        #     async for message in websocket:
        #         pass  # Handle incoming messages if needed
        # finally:
        #     self.clients.remove(websocket)

    async def send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if self.clients:
            message: str = str({
                'event': event_type,
                'data': data
            })
            await asyncio.wait([client.send(message) for client in self.clients])

    def start_server(self):
        return websockets.serve(self.handler, self.host, self.port)

async def main() -> None:
    server = WebSocketServer()
    server_task = server.start_server()
    await server_task

if __name__ == "__main__":
    asyncio.run(main())