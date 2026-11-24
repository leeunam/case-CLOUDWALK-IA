"""Sessão Feita da Luna, com I/O HTTPS isolado sob prazo monotônico."""
from contextlib import closing
from http.client import HTTPException, HTTPSConnection
import multiprocessing
import os
import socket
from struct import Struct
from threading import Thread
import time

from adapters.qwen.transport import BODY_LIMIT, HOST, PATH

REQUEST = Struct("!dI")
RESPONSE = Struct("!HI")


def remaining(deadline):
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise TimeoutError
    return seconds


def receive(channel, size, deadline=None):
    data = bytearray(size)
    unread = memoryview(data)
    while unread:
        if deadline is not None:
            channel.settimeout(remaining(deadline))
        count = channel.recv_into(unread)
        if not count:
            raise EOFError("canal Luna encerrado")
        unread = unread[count:]
    return bytes(data)


def send(channel, data, deadline):
    channel.settimeout(remaining(deadline))
    channel.sendall(data)


def watch_parent(lifetime):
    # Só o pai retém a ponta de escrita. EOF também interrompe DNS/TLS/leitura bloqueados.
    try:
        lifetime.recv_bytes()
    except (EOFError, OSError):
        os._exit(0)


def serve(channel, lifetime, api_key, connection_factory):
    Thread(target=watch_parent, args=(lifetime,), daemon=True).start()
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json", "Accept": "application/json"}
    connection = None
    try:
        while True:
            deadline, size = REQUEST.unpack(receive(channel, REQUEST.size))
            body = receive(channel, size)
            if connection is None:
                connection = connection_factory(HOST, timeout=remaining(deadline))
                connection.auto_open = False
                connection.connect()
            remaining(deadline)
            # O POST só é tentado depois que o pai registrou a possibilidade de envio.
            channel.sendall(b"D")
            if receive(channel, 1) != b"A":
                raise ConnectionError("despacho Luna não confirmado")
            connection.sock.settimeout(remaining(deadline))
            connection.request("POST", PATH, body=body, headers=headers)
            with closing(connection.getresponse()) as response:
                data = response.read(BODY_LIMIT + 1)
                if len(data) > BODY_LIMIT or response.length not in (None, 0):
                    raise ConnectionError("resposta Luna excedente ou incompleta")
                status = response.status
                will_close = response.will_close
            channel.sendall(b"R" + RESPONSE.pack(status, len(data)) + data)
            if status != 200:
                return
            if will_close:
                connection.close()
                connection = None
    except EOFError:
        pass
    except (OSError, HTTPException, ValueError) as error:
        try:
            channel.sendall(b"T" if isinstance(error, TimeoutError) else b"E")
        except OSError:
            pass
    finally:
        if connection is not None:
            connection.close()
        channel.close()


class LunaTransport:
    def __init__(self, api_key, *, connection_factory=HTTPSConnection):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("credencial Feita ausente")
        self._api_key = api_key
        self._connection_factory = connection_factory
        self._channel = None
        self._lifetime = None
        self._worker = None
        self._closed = False

    def _start(self):
        ctx = multiprocessing.get_context("spawn")
        self._channel, child = socket.socketpair()
        with child:
            lifetime_reader, self._lifetime = ctx.Pipe(duplex=False)
            with lifetime_reader:
                self._worker = ctx.Process(target=serve, args=(child, lifetime_reader, self._api_key,
                                                               self._connection_factory), daemon=True)
                self._worker.start()

    def __call__(self, body, deadline, dispatched):
        if self._closed:
            raise ConnectionError("sessão HTTPS Luna encerrada")
        try:
            remaining(deadline)
            if self._worker is None:
                self._start()
            send(self._channel, REQUEST.pack(deadline, len(body)) + body, deadline)
            event = receive(self._channel, 1, deadline)
            if event == b"D":
                dispatched()
                send(self._channel, b"A", deadline)
                event = receive(self._channel, 1, deadline)
            if event == b"T":
                raise TimeoutError
            if event != b"R":
                raise ConnectionError("falha de transporte Luna")
            status, size = RESPONSE.unpack(receive(self._channel, RESPONSE.size, deadline))
            data = receive(self._channel, size, deadline)
            if status != 200:
                self._close(abort=True)
            return status, data
        except BaseException:
            self._close(abort=True)
            raise

    def close(self):
        self._close(abort=False)

    def _close(self, *, abort):
        if self._closed:
            return
        self._closed = True
        if self._channel is not None:
            self._channel.close()
        if self._worker is not None:
            if self._worker.pid is not None:
                if not abort:
                    self._worker.join(timeout=0.05)
                if self._worker.is_alive():
                    self._worker.kill()
                self._worker.join()
            self._worker.close()
        if self._lifetime is not None:
            self._lifetime.close()
