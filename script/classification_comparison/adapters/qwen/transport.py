"""Transporte descartável por requisição com prazo global, sem redirecionamento."""
import http.client
import multiprocessing
import os
import time
from contextlib import closing

HOST = "api.feita.ai"
PATH = "/gateway/v1/chat/completions"
BODY_LIMIT = 256 * 1024


def post(pipe, body, deadline):
    try:
        key = os.environ.get("FEITA_API_KEY")
        if not key or not key.strip():
            pipe.send(("error", "credential"))
            return
        timeout = max(0.001, deadline - time.monotonic())
        with closing(http.client.HTTPSConnection(HOST, timeout=timeout)) as connection:
            connection.connect()
            if time.monotonic() >= deadline:
                raise TimeoutError
            pipe.send(("dispatch", None))
            connection.request("POST", PATH, body=body, headers={
                "Authorization": "Bearer " + key, "Content-Type": "application/json",
                "Accept": "application/json",
            })
            response = connection.getresponse()
            data = response.read(BODY_LIMIT + 1)
        pipe.send(("response", (response.status, data if len(data) <= BODY_LIMIT else b"")))
    except TimeoutError:
        pipe.send(("error", "timeout"))
    except (OSError, ValueError, http.client.HTTPException):
        pipe.send(("error", "transport"))
    finally:
        pipe.close()


class FeitaTransport:
    def __call__(self, body, deadline, dispatched):
        ctx = multiprocessing.get_context("spawn")
        receiver, sender = ctx.Pipe(duplex=False)
        with receiver, sender:
            child = ctx.Process(target=post, args=(sender, body, deadline))
            child.start()
            sender.close()
            try:
                while receiver.poll(max(0, deadline - time.monotonic())):
                    kind, value = receiver.recv()
                    if kind == "dispatch":
                        dispatched()
                    elif kind == "response":
                        return value
                    elif value == "timeout":
                        raise TimeoutError
                    else:
                        raise ConnectionError(value)
                raise TimeoutError
            finally:
                if child.is_alive():
                    child.kill()
                child.join()
                child.close()
