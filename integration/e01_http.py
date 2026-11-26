"""POST sem redirecionamento com prazo total para DNS, conexão e leitura."""

from contextlib import closing
from http.client import HTTPConnection, HTTPException, HTTPSConnection
import multiprocessing
import os
import socket
from struct import Struct
from threading import Thread
import time


_FRAME = Struct("!HI")


def remaining(deadline):
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise TimeoutError("http_deadline")
    return seconds


def _receive(channel, size, deadline):
    data = bytearray(size)
    pending = memoryview(data)
    while pending:
        channel.settimeout(remaining(deadline))
        count = channel.recv_into(pending)
        if not count:
            raise ConnectionError("http_interrupted")
        pending = pending[count:]
    return bytes(data)


def _watch_parent(channel):
    try:
        channel.recv(1)
    except OSError:
        pass
    os._exit(0)


def _post(channel, connection_factory, host, port, path, headers, body, deadline, response_limit):
    # Cancelar o despacho se o consumidor morrer antes de sair do DNS/TLS.
    Thread(target=_watch_parent, args=(channel,), daemon=True).start()
    with channel:
        try:
            with closing(connection_factory(host, port=port, timeout=remaining(deadline))) as connection:
                connection.auto_open = False
                connection.connect()
                connection.sock.settimeout(remaining(deadline))
                connection.request("POST", path, body=body, headers=headers)
                with closing(connection.getresponse()) as response:
                    if response.getheader("Content-Encoding", "identity").lower() != "identity":
                        raise ConnectionError("http_encoding")
                    payload = response.read(response_limit + 1)
                    if len(payload) > response_limit or response.length not in (None, 0):
                        raise ConnectionError("http_response_size")
                    frame = _FRAME.pack(response.status, len(payload))
            unsent = memoryview(frame + payload)
            while unsent:
                unsent = unsent[os.write(channel.fileno(), unsent):]
        except (OSError, HTTPException, ValueError):
            # Uma resposta incompleta é ambígua. O pai só recebe os códigos internos.
            pass


class DeadlinePost:
    def __init__(self, host, *, port=None, tls=True, response_limit, connection_factory=None):
        self._host = host
        self._port = port
        self._response_limit = response_limit
        self._connection_factory = connection_factory or (HTTPSConnection if tls else HTTPConnection)

    def __call__(self, path, headers, body, *, deadline):
        remaining(deadline)
        context = multiprocessing.get_context("spawn")
        parent, child = socket.socketpair()
        with parent, child:
            process = context.Process(
                target=_post, daemon=True,
                args=(child, self._connection_factory, self._host, self._port,
                      path, headers, body, deadline, self._response_limit),
            )
            try:
                process.start()
                child.close()
                status, size = _FRAME.unpack(_receive(parent, _FRAME.size, deadline))
                if not 100 <= status <= 599 or size > self._response_limit:
                    raise ConnectionError("http_invalid_frame")
                response = _receive(parent, size, deadline)
                remaining(deadline)
                return status, response
            finally:
                if process.pid is not None:
                    if process.is_alive():
                        process.kill()
                    process.join()
                process.close()
