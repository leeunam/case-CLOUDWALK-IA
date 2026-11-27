"""Dois clientes compartilham o gate e usam o mesmo correlation_id em sockets distintos."""

import asyncio
import socket
import struct
import unittest
from unittest.mock import patch

import ack_gate


def packet(payload):
    return struct.pack(">i", len(payload)) + payload


class AckGateTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.gate = ack_gate.Gate()
        self.writers = []
        self.tasks = []

    async def connection(self):
        client_sock, proxy_in_sock = socket.socketpair()
        proxy_out_sock, broker_sock = socket.socketpair()
        sockets = (client_sock, proxy_in_sock, proxy_out_sock, broker_sock)
        client, proxy_in, proxy_out, broker = [await asyncio.open_connection(sock=s) for s in sockets]
        self.writers.extend(pair[1] for pair in (client, proxy_in, proxy_out, broker))
        pending = set()
        for source, dest, is_request in ((proxy_in, proxy_out, True), (proxy_out, proxy_in, False)):
            self.tasks.append(asyncio.create_task(ack_gate.relay(
                source[0], dest[1], requests=is_request, correlations=pending, gate=self.gate)))
        return client, broker

    async def asyncTearDown(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        for writer in self.writers:
            writer.close()
        await asyncio.gather(*(writer.wait_closed() for writer in self.writers))

    async def exchange(self, sender, receiver, data):
        sender[1].write(data)
        await sender[1].drain()
        received = await asyncio.wait_for(receiver[0].readexactly(len(data)), 1)
        self.assertEqual(received, data)

    async def hold(self):
        producer, broker = await self.connection()
        await self.gate.command("arm")
        request = packet(struct.pack(">hhi", 0, 9, 17) + b"synthetic-produce")
        await self.exchange(producer, broker, request)
        ack = packet(struct.pack(">i", 17) + b"synthetic-ack")
        broker[1].write(ack)
        self.assertEqual((await self.gate.command("wait"))["phase"], "held")
        with self.assertRaises(TimeoutError):
            await asyncio.wait_for(producer[0].read(1), 0.02)
        return producer, ack

    async def test_commit_flows_and_counts_on_either_side_of_held_ack(self):
        consumer, coordinator = await self.connection()
        producer, ack = await self.hold()
        commit = packet(struct.pack(">hhi", 8, 9, 17) + b"synthetic-commit")
        await self.exchange(consumer, coordinator, commit)
        commit_reply = packet(struct.pack(">i", 17) + b"synthetic-commit-reply")
        await self.exchange(coordinator, consumer, commit_reply)
        released = await self.gate.command("release")
        self.assertEqual(released["commits_before_ack"], 1)
        self.assertEqual(released["commits_after_ack"], 0)
        self.assertEqual(await asyncio.wait_for(producer[0].readexactly(len(ack)), 1), ack)
        await self.exchange(consumer, coordinator, commit)
        self.assertEqual((await self.gate.command("status"))["commits_after_ack"], 1)

    async def test_expiration_delivers_bytes_but_invalidates_measurement(self):
        with patch.object(ack_gate, "ACK_TIMEOUT", 0.1):
            producer, ack = await self.hold()
            self.assertEqual(await asyncio.wait_for(producer[0].readexactly(len(ack)), 1), ack)
            self.assertEqual((await self.gate.command("status"))["phase"], "expired")
            with self.assertRaises(ValueError):
                await self.gate.command("release")

    async def test_partial_and_oversized_frames_stop_before_forwarding(self):
        for raw in (b"\x00\x00", struct.pack(">i", 20_000_000), struct.pack(">i", -1)):
            reader = asyncio.StreamReader()
            reader.feed_data(raw)
            reader.feed_eof()
            with self.assertRaises((ValueError, asyncio.IncompleteReadError)):
                await ack_gate.read_frame(reader, 4)
