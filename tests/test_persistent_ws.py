import asyncio

import pytest
import websockets

from casebuilder.services.persistent_ws import PersistentWebSocketClient


@pytest.mark.asyncio
async def test_websocket_connect_and_send():
    async def echo(ws):
        async for message in ws:
            await ws.send(message)

    server = await websockets.serve(echo, "localhost", 8765)
    async with PersistentWebSocketClient(
        "ws://localhost:8765", reconnect_delay=0.1
    ) as client:
        await asyncio.sleep(0.2)
        await client.send("hello")
        assert await client.recv() == "hello"

    server.close()
    await server.wait_closed()


@pytest.mark.asyncio
async def test_websocket_reconnect():
    messages = []

    async def echo_once(ws):
        async for message in ws:
            messages.append(message)
            await ws.send(message)
            await ws.close()

    server = await websockets.serve(echo_once, "localhost", 8766)
    async with PersistentWebSocketClient(
        "ws://localhost:8766", reconnect_delay=0.1
    ) as client:
        await asyncio.sleep(0.2)

        await client.send("first")
        assert await client.recv() == "first"
        await asyncio.sleep(0.2)

        server.close()
        await server.wait_closed()
        server = await websockets.serve(echo_once, "localhost", 8766)
        await asyncio.sleep(0.3)

        await client.send("second")
        assert await client.recv() == "second"

        server.close()
        await server.wait_closed()
    assert messages == ["first", "second"]
