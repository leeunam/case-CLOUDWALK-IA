"""Exercita prazos e vida útil do processo com uma conexão HTTPS dupla."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http.client import RemoteDisconnected
import multiprocessing
from pathlib import Path
import tempfile
import time
import unittest

from adapters.luna.transport import BODY_LIMIT, LunaTransport

KEY = "credencial-artificial"
BODY = b'{"artificial":true}'
RECEIPT = b'{"usage":{"cost":"0.000026","cost_unit":"USD"}}'


def record(log, event):
    with log.open("a", encoding="utf-8") as stream:
        stream.write(event + "\n")


class DoubleResponse:
    def __init__(self, log, behavior):
        self.log = log
        self.behavior = behavior
        self.status = behavior if isinstance(behavior, int) else 200
        self.will_close = behavior == "server_close"
        self.length = None

    def read(self, count):
        record(self.log, "read")
        if self.behavior == "slow_read":
            time.sleep(3)
        if self.behavior == "oversize":
            return b"x" * count
        if self.behavior == "truncated":
            self.length = 1
        return RECEIPT

    def close(self):
        pass


class DoubleConnection:
    def __init__(self, log, behaviors, connect_pause):
        self.log = log
        self.behaviors = behaviors
        self.connect_pause = connect_pause
        self.sock = self
        self.auto_open = True
        record(log, "new")

    def connect(self):
        record(self.log, "connect")
        time.sleep(self.connect_pause)

    def settimeout(self, timeout):
        if timeout <= 0:
            raise AssertionError("socket recebeu um prazo vencido")
        record(self.log, "settimeout")

    def request(self, method, path, *, body, headers):
        assert method == "POST" and path == "/gateway/v1/chat/completions"
        assert body == BODY and headers["Authorization"] == f"Bearer {KEY}"
        assert self.auto_open is False
        index = self.log.read_text().splitlines().count("post")
        self.behavior = self.behaviors[index]
        record(self.log, "post")
        if self.behavior == "stale":
            raise BrokenPipeError

    def getresponse(self):
        if self.behavior == "eof":
            raise RemoteDisconnected
        return DoubleResponse(self.log, self.behavior)

    def close(self):
        record(self.log, "close")


@dataclass(frozen=True)
class DoubleConnectionFactory:
    log: Path
    behaviors: tuple
    connect_pause: float = 0

    def __call__(self, host, *, timeout):
        assert host == "api.feita.ai" and timeout > 0
        return DoubleConnection(self.log, self.behaviors, self.connect_pause)


class LunaTransportTests(unittest.TestCase):
    def setup_transport(self, *behaviors, connect_pause=0):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        log = Path(folder.name) / "channel.log"
        log.touch()
        transport = LunaTransport(KEY, connection_factory=DoubleConnectionFactory(log, behaviors, connect_pause))
        self.addCleanup(transport.close)
        return transport, log

    def call(self, transport, log, seconds=2):
        return transport(BODY, time.monotonic() + seconds, lambda: record(log, "dispatch"))

    def test_preguicoso_e_reutiliza_processo_socket_e_timeout(self):
        transport, log = self.setup_transport(200, 200, connect_pause=0.05)
        self.assertEqual(log.read_text(), "")
        self.assertIsNone(transport._worker)
        started = time.monotonic()
        self.assertEqual(self.call(transport, log), (200, RECEIPT))
        self.assertGreaterEqual(time.monotonic() - started, 0.05)
        pid = transport._worker.pid
        self.assertEqual(self.call(transport, log), (200, RECEIPT))
        self.assertEqual(transport._worker.pid, pid)
        self.assertEqual(log.read_text().splitlines(), ["new", "connect", "dispatch", "settimeout", "post", "read",
                                                       "dispatch", "settimeout", "post", "read"])
        transport.close()
        transport.close()
        self.assertNotIn(pid, {process.pid for process in multiprocessing.active_children()})

    def test_servidor_fecha_e_caso_seguinte_abre_nova_conexao(self):
        transport, log = self.setup_transport("server_close", 200)
        self.assertEqual(self.call(transport, log), (200, RECEIPT))
        self.assertEqual(self.call(transport, log), (200, RECEIPT))
        events = log.read_text().splitlines()
        self.assertEqual(events.count("connect"), 2)
        self.assertEqual(events.count("post"), 2)

    def test_prazo_frio_cobre_dns_tls_antes_de_post(self):
        transport, log = self.setup_transport(200, connect_pause=3)
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            self.call(transport, log, 1.2)
        self.assertLess(time.monotonic() - started, 2.5)
        self.assertEqual(log.read_text().splitlines(), ["new", "connect"])
        with self.assertRaises(ConnectionError):
            self.call(transport, log)

    def test_prazo_absoluto_interrompe_leitura_mesmo_com_socket_quente(self):
        transport, log = self.setup_transport(200, "slow_read")
        self.assertEqual(self.call(transport, log), (200, RECEIPT))
        pid = transport._worker.pid
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            self.call(transport, log, 0.5)
        self.assertLess(time.monotonic() - started, 2)
        with self.assertRaises(ConnectionError):
            self.call(transport, log)
        self.assertNotIn(pid, {process.pid for process in multiprocessing.active_children()})
        events = log.read_text().splitlines()
        self.assertEqual((events.count("connect"), events.count("dispatch"), events.count("post")), (1, 2, 2))

    def test_socket_obsoleto_e_eof_sem_reabertura_ou_reenvio(self):
        for behavior in ("stale", "eof"):
            with self.subTest(behavior=behavior):
                transport, log = self.setup_transport(200, behavior)
                self.call(transport, log)
                with self.assertRaises((ConnectionError, EOFError)):
                    self.call(transport, log)
                with self.assertRaises(ConnectionError):
                    self.call(transport, log)
                events = log.read_text().splitlines()
                self.assertEqual((events.count("connect"), events.count("post")), (1, 2))

    def test_http_de_erro_preserva_bytes_e_impede_proximo_post(self):
        for status in (307, 429, 503):
            with self.subTest(status=status):
                transport, log = self.setup_transport(status)
                self.assertEqual(self.call(transport, log), (status, RECEIPT))
                with self.assertRaises(ConnectionError):
                    self.call(transport, log)
                self.assertEqual(log.read_text().splitlines().count("post"), 1)

    def test_resposta_excedente_ou_truncada_encerra_sem_reenvio(self):
        for behavior in ("oversize", "truncated"):
            with self.subTest(behavior=behavior):
                transport, log = self.setup_transport(behavior)
                with self.assertRaises(ConnectionError):
                    self.call(transport, log)
                self.assertEqual(BODY_LIMIT, 262144)
                self.assertEqual(log.read_text().splitlines().count("post"), 1)

    def test_falha_ao_registrar_despacho_impede_post(self):
        transport, log = self.setup_transport(200)

        def reject_dispatch():
            raise RuntimeError("registro local indisponível")

        with self.assertRaisesRegex(RuntimeError, "registro local indisponível"):
            transport(BODY, time.monotonic() + 2, reject_dispatch)
        events = log.read_text().splitlines()
        self.assertEqual(events[:2], ["new", "connect"])
        self.assertNotIn("post", events)

    def test_eof_de_vida_do_pai_interrompe_trabalhador_bloqueado(self):
        transport, log = self.setup_transport("slow_read")
        with ThreadPoolExecutor(max_workers=1) as executor:
            call = executor.submit(self.call, transport, log, 6)
            until = time.monotonic() + 2
            while "read" not in log.read_text().splitlines() and time.monotonic() < until:
                time.sleep(0.01)
            self.assertIn("read", log.read_text().splitlines())
            pid = transport._worker.pid
            transport._lifetime.close()
            with self.assertRaises(EOFError):
                call.result(timeout=1)
        self.assertNotIn(pid, {process.pid for process in multiprocessing.active_children()})


if __name__ == "__main__":
    unittest.main()
