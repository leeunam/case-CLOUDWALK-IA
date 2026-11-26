"""Prova manual dentro da imagem já pronta. Usa apenas entradas sintéticas do produto."""
from http.client import HTTPConnection
import json
from pathlib import Path
from time import monotonic
from uuid import uuid4

BASE = Path("/sys/fs/cgroup")
ENDPOINT = "/internal/classification/v1/complete"


def request(path, body=None):
    client = HTTPConnection("127.0.0.1", 8080, timeout=6)
    try:
        started = monotonic()
        if body is None:
            client.request("GET", path)
        else:
            client.request("POST", path, json.dumps(body).encode(), {"Content-Type": "application/json"})
        response = client.getresponse()
        payload = json.loads(response.read())
        return response.status, payload, round(1000 * (monotonic() - started), 2)
    finally:
        client.close()


def main():
    source = json.loads(Path("/app/script/f08/jev/catalog.json").read_bytes())
    catalog = {field: source[field] for field in ("category", "priority")}
    status, initial, _ = request("/ready")
    assert status == 200, initial
    pid = initial["worker_pid"]
    print("ready", initial)
    for provided in ({"category": "pix", "priority": None}, {"category": None, "priority": "basic"}):
        missing = next(field for field, value in provided.items() if value is None)
        for tokens in (129, 128):
            _, before, _ = request("/ready")
            req = dict(contract_version="classification-http/1.0", id=str(uuid4()), catalog_version=7,
                       catalog=catalog, received=provided, text=" ".join(["a"] * (tokens - 2)))
            status, result, http_ms = request(ENDPOINT, req)
            _, state, _ = request("/ready")
            delta = state["counts"]["pipe_writes"] - before["counts"].get("pipe_writes", 0)
            assert state["worker_pid"] == pid and state["ready"]
            if tokens == 128:
                assert status == 200 and delta == 1 and result["calls"][missing] == 1, (status, result)
                assert sum(result["calls"].values()) == 1
            else:
                assert status == 422 and result["error"] == "text_out_of_scope" and delta == 0
            print("boundary", missing, tokens, status, delta, http_ms)
    pix_interrompido = "Sou do caixa da loja. Todos os pagamentos por Pix estão falhando. Estamos sem conseguir vender agora."
    cases = [
        ("Precisamos de outra via do comprovante da transferência Pix de ontem.", {"category": None, "priority": "basic"}),
        ("A maquininha do balcão ficou com a tela apagada. Nenhuma venda passa desde a abertura.",
         {"category": None, "priority": None}),
        (pix_interrompido, {"category": "pix", "priority": None}),
        (pix_interrompido, {"category": None, "priority": None}),
        ("Quero apenas saber onde consulto o comprovante de uma transferência Pix. O caixa segue funcionando.",
         {"category": None, "priority": None}),
    ]
    for text, received in cases:
        req = dict(contract_version="classification-http/1.0", id=str(uuid4()), catalog_version=7,
                   catalog=catalog, text=text, received=received)
        status, result, http_ms = request(ENDPOINT, req)
        assert status == 200 and result["id"] == req["id"], (status, result)
        assert result["calls"] == {field: int(value is None) for field, value in received.items()}
        print("produto", req["id"], result["outcome"], result["applied"], result["calls"],
              round(result["elapsed_ms"], 2), http_ms, result["raw_frame_sha256"])
    status, final, _ = request("/ready")
    assert status == 200 and final["worker_pid"] == pid
    print("ready", final)
    for name in ("memory.current", "memory.peak", "cpu.stat"):
        print(name, (BASE / name).read_text().strip())


if __name__ == "__main__":
    main()
