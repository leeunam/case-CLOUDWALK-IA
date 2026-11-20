"""Listener Kafka interno e exclusivo da ponte events. Nunca registra os corpos."""

import asyncio
import contextlib
import json
import struct

PRODUCE = 0
OFFSET_COMMIT = 8
FRAME_LIMIT = 16 * 1024 * 1024
# O produtor de produto usa message.timeout.ms=1500. Uma expiração invalida a prova.
ACK_TIMEOUT = 1.2


class Gate:
    def __init__(self):
        self.phase = "idle"
        self.produces = self.early_commits = self.late_commits = 0
        self.held = asyncio.Event()
        self.resume = asyncio.Event()
        self.forwarded = asyncio.Event()

    def status(self):
        return {"phase": self.phase, "produce_requests": self.produces,
                "commits_before_ack": self.early_commits, "commits_after_ack": self.late_commits}

    def request(self, api):
        if self.phase not in {"armed", "held", "released"}:
            return False
        if api == OFFSET_COMMIT:
            if self.phase == "released":
                self.late_commits += 1
            else:
                self.early_commits += 1
        if api == PRODUCE:
            self.produces += 1
            return self.phase == "armed"
        return False

    async def send_ack(self, writer, frame):
        if self.phase == "armed":
            self.phase = "held"
            self.held.set()
            try:
                await asyncio.wait_for(self.resume.wait(), ACK_TIMEOUT)
            except TimeoutError:
                self.phase = "expired"
        writer.write(frame)
        if self.phase == "held":
            self.phase = "released"
        self.forwarded.set()

    async def command(self, verb):
        if verb == "arm" and self.phase == "idle":
            self.phase = "armed"
        elif verb == "wait":
            await asyncio.wait_for(self.held.wait(), 15)
        elif verb == "release" and self.phase == "held":
            self.resume.set()
            await asyncio.wait_for(self.forwarded.wait(), 2)
        elif verb == "cancel":
            self.phase = "cancelled"
            self.resume.set()
        elif verb != "status":
            raise ValueError("transição inválida")
        return self.status()


async def read_frame(reader, minimum):
    prefix = await reader.readexactly(4)
    size, = struct.unpack(">i", prefix)
    if not minimum <= size <= FRAME_LIMIT:
        raise ValueError("tamanho de frame fora dos limites")
    return prefix + await reader.readexactly(size)


async def relay(reader, writer, *, requests, correlations, gate):
    while True:
        frame = await read_frame(reader, 8 if requests else 4)
        if requests:
            api, _version, correlation = struct.unpack_from(">hhi", frame, 4)
            if gate.request(api):
                correlations.add(correlation)
        else:
            correlation, = struct.unpack_from(">i", frame, 4)
            if correlation in correlations:
                correlations.remove(correlation)
                await gate.send_ack(writer, frame)
                await writer.drain()
                continue
        writer.write(frame)
        await writer.drain()


async def proxy(client, to_client, gate, upstream=("kafka", 19092)):
    try:
        broker, to_broker = await asyncio.wait_for(asyncio.open_connection(*upstream), 3)
    except (OSError, TimeoutError):
        to_client.close()
        return
    correlations = set()  # correlation_id é local à conexão TCP
    tasks = [
        asyncio.create_task(relay(client, to_broker, requests=True, correlations=correlations, gate=gate)),
        asyncio.create_task(relay(broker, to_client, requests=False, correlations=correlations, gate=gate)),
    ]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        to_client.close()
        to_broker.close()


async def controller(reader, writer, gate):
    try:
        verb = (await asyncio.wait_for(reader.readline(), 2)).strip().decode("ascii")
        response = await gate.command(verb)
    except (ValueError, TimeoutError):
        response = {**gate.status(), "error": "comando expirado ou inválido"}
    try:
        writer.write(json.dumps(response).encode() + b"\n")
        await asyncio.wait_for(writer.drain(), 2)
    finally:
        writer.close()


async def main():
    gate = Gate()
    kafka = await asyncio.start_server(lambda r, w: proxy(r, w, gate), "0.0.0.0", 9092)
    control = await asyncio.start_server(lambda r, w: controller(r, w, gate), "0.0.0.0", 8081, limit=64)
    async with kafka, control:
        await asyncio.gather(kafka.serve_forever(), control.serve_forever())


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
