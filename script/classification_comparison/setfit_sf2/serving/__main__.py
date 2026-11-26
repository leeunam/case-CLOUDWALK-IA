"""Serviço local SetFit R1 da demo."""
import signal

from .bootstrap import load
from .server import Supervisor, serve


def shutdown(*_):
    raise SystemExit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, shutdown)
    serve(("0.0.0.0", 8080), Supervisor(load))
