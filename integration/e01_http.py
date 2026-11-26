"""POST sem redirecionamento com prazo total para DNS, conexão e leitura."""

from contextlib import closing
from http.client import HTTPConnection, HTTPException, HTTPSConnection
import json
import multiprocessing
import os
from select import select
import socket
from struct import Struct
from threading import Thread
import time


_REQUEST = Struct("!III")
_RESPONSE = Struct("!HI")


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


def _send(channel, deadline, *parts):
    channel.setblocking(False)
    for part in parts:
        pending = memoryview(part)
        while pending:
            _, writable, _ = select([], [channel], [], remaining(deadline))
            if not writable:
                raise TimeoutError("http_deadline")
            remaining(deadline)
            try:
                sent = os.write(channel.fileno(), pending)
            except BlockingIOError:
                continue
            pending = pending[sent:]


def _watch_parent(channel):
    try:
        select([channel], [], [])
    except OSError:
        pass
    os._exit(0)


def _post(channel, connection_factory, host, port, deadline, response_limit):
    with channel:
        try:
            path_size, headers_size, body_size = _REQUEST.unpack(_receive(channel, _REQUEST.size, deadline))
            path = _receive(channel, path_size, deadline).decode("ascii")
            headers = json.loads(_receive(channel, headers_size, deadline))
            body = _receive(channel, body_size, deadline)
            # A partir daqui o pai só lê. Qualquer atividade no sentido inverso
            # significa que ele encerrou a tentativa.
            Thread(target=_watch_parent, args=(channel,), daemon=True).start()
            with closing(connection_factory(host, port=port, timeout=remaining(deadline))) as connection:
                connection.auto_open = False
                connection.connect()
                connection.sock.settimeout(remaining(deadline))
                remaining(deadline)
                connection.request("POST", path, body=body, headers=headers)
                with closing(connection.getresponse()) as response:
                    if response.getheader("Content-Encoding", "identity").lower() != "identity":
                        raise ConnectionError("http_encoding")
                    payload = response.read(response_limit + 1)
                    if len(payload) > response_limit or response.length not in (None, 0):
                        raise ConnectionError("http_response_size")
                    frame = _RESPONSE.pack(response.status, len(payload))
            _send(channel, deadline, frame, payload)
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
        encoded_path = path.encode("ascii")
        encoded_headers = json.dumps(headers).encode("ascii")
        frame = _REQUEST.pack(len(encoded_path), len(encoded_headers), len(body))
        context = multiprocessing.get_context("spawn")
        parent, child = socket.socketpair()
        with parent, child:
            process = context.Process(
                target=_post, daemon=True,
                args=(child, self._connection_factory, self._host, self._port, deadline, self._response_limit),
            )
            try:
                process.start()
                child.close()
                _send(parent, deadline, frame, encoded_path, encoded_headers, body)
                status, size = _RESPONSE.unpack(_receive(parent, _RESPONSE.size, deadline))
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
