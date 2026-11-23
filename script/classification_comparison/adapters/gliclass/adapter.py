"""Adaptador C04 do protocolo JSONL 1.1. O modelo recebe campos, jamais IDs."""
import ctypes
from dataclasses import dataclass
import json
import multiprocessing
import os
from pathlib import Path
import platform
import re
import resource
import signal
import sys
import time

from model import MODEL, REVISION, ContextOverflow

ROOT = Path(__file__).resolve().parents[4]
FIELDS = ("category", "priority")
VERSION = "1.1.0"
ABSTENTION = "informacao_insuficiente"
LOCAL_USAGE = dict(input_tokens=None, output_tokens=None, observed_api_usd=0,
                   estimated_api_usd=None, tariff=None)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic_json(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)


@dataclass(frozen=True)
class Context:
    catalog: dict
    prompts: dict
    definitions: dict
    priority_notes: str
    policy: dict

    @classmethod
    def load(cls, env):
        rubric = Path(env["CLASSIFICATION_RUBRIC"]).read_text(encoding="utf-8")
        catalog = read_json(ROOT / "script/f08/jev/catalog.json")
        prompts = read_json(env["CLASSIFICATION_PROMPT"])
        policy = read_json(env["CLASSIFICATION_POLICY"])
        definitions = {}
        for field, heading in zip(FIELDS, ("Categoria", "Prioridade"), strict=True):
            section = re.search(rf"(?m)^## {heading}\n([\s\S]*?)(?=^## |\Z)", rubric).group(1)
            definitions[field] = {
                code: " ".join(description.split())
                for code, description in re.findall(r"(?m)^- `([^\n`]+)`: (.*(?:\n  [^\n]+)*)", section)
            }
            if set(definitions[field]) != set(catalog[field]) | {ABSTENTION}:
                raise ValueError(f"rubrica e catálogo divergem: {field}")
            if field == "priority":
                priority_notes = section.strip().split("\n\n")[-1]
                priority_notes = " ".join(priority_notes.split())
        if not priority_notes.startswith("Prioridade mede urgência/impacto") or policy["examples"]:
            raise ValueError("rubrica de urgência ou baseline de zero exemplos incompatível")
        return cls(catalog, prompts, definitions, priority_notes, policy)

    def request(self, item, field):
        descriptions = self.catalog[field]
        definitions = self.definitions[field]
        labels = {}
        for code in (*descriptions, ABSTENTION):
            catalog_text = descriptions.get(code, "")
            label = " ".join(value for value in (code, catalog_text, definitions[code]) if value)
            labels[label] = code
        prompt = self.prompts[field]
        if field == "priority":
            prompt = f"{prompt} {self.priority_notes}"
        received = [f"{key}: {value}" for key, value in item["received"].items() if key not in item["missing"]]
        if received:
            prompt = f"{prompt} Campos válidos do canal: {', '.join(received)}."
        return item["text"], labels, prompt + "\nRelato:\n"

    def eligible(self, item):
        if item.get("contract_version") != VERSION or item.get("catalog") != self.catalog:
            return False
        received = item["received"]
        missing = [field for field in FIELDS if received.get(field) is None or
                   isinstance(received[field], str) and not received[field].strip()]
        return bool(missing) and item["missing"] == missing and all(
            isinstance(received[field], str) and received[field] in self.catalog[field]
            for field in FIELDS if field not in missing
        )


def error(reason):
    return dict(status="error", raw=None, reason=reason, score=None)


def invalid(reason):
    return dict(status="invalid", raw=None, reason=reason, score=None)


def choice_from_output(output, labels, score_kind):
    if output == [[]]:
        return invalid("missing_output")
    if not isinstance(output, list) or len(output) != 1 or not isinstance(output[0], list):
        return invalid("invalid_output")

    scores = {}
    for row in output[0]:
        if not isinstance(row, dict):
            return invalid("invalid_output")
        label, score = row.get("label"), row.get("score")
        if (not isinstance(label, str) or label not in labels or label in scores or
                type(score) not in (int, float) or not 0 <= score <= 1):
            return invalid("invalid_output")
        scores[label] = score
    if scores.keys() != labels.keys():
        return invalid("missing_output")

    high = max(scores.values())
    winners = [labels[label] for label, value in scores.items() if value == high]
    score = dict(kind=score_kind, value=high)
    if len(winners) != 1:
        return dict(status="abstained", raw={"tied_codes": winners}, reason="policy", score=score)
    raw = winners[0]
    if raw == ABSTENTION:
        return dict(status="abstained", raw=raw, reason="explicit", score=score)
    return dict(status="predicted", raw=raw, reason=None, score=score)


def infer(pipeline, request, policy):
    text, labels, prompt = request
    result = pipeline(text, list(labels), prompt=prompt, examples=None,
                      batch_size=1, threshold=policy["pipeline_threshold"])
    return choice_from_output(result, labels, policy["score_kind"])


def worker_main(parent, request_pipe, result_pipe, unused_request, unused_result, loader, context):
    unused_request.close()
    unused_result.close()
    # O avaliador pode encerrar o adaptador por SIGKILL em caso de interrupção.
    if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
        return
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    try:
        started = time.monotonic()
        pipeline, metadata = loader(context.policy)
        loaded = time.monotonic()
        sample = dict(text="Mensagem sintética usada para aquecer o runtime.", received={}, missing=list(FIELDS))
        for field in FIELDS:
            observed = infer(pipeline, context.request(sample, field), context.policy)
            if observed["status"] == "invalid":
                raise RuntimeError("saída do aquecimento fora da interface")
        result_pipe.send(dict(metadata, load_ms=(loaded - started) * 1000,
                              warmup_ms=(time.monotonic() - loaded) * 1000))
    except Exception as exc:
        print(f"C04 inicialização: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return
    while True:
        try:
            request = request_pipe.recv()
        except EOFError:
            return
        started = time.monotonic()
        try:
            choice = infer(pipeline, request, context.policy)
        except ContextOverflow as exc:
            print(f"C04 limite de representação: {exc}", file=sys.stderr, flush=True)
            choice = error("adapter_error")
        except Exception as exc:
            print(f"C04 erro na inferência: {type(exc).__name__}", file=sys.stderr, flush=True)
            choice = error("adapter_error")
        result_pipe.send((choice, (time.monotonic() - started) * 1000))


class Worker:
    """Processo único de inferência com cancelamento sem esperar pelo PyTorch."""

    def __init__(self, loader, context):
        ctx = multiprocessing.get_context("fork")
        child_request, self.requests = ctx.Pipe(duplex=False)
        self.results, child_result = ctx.Pipe(duplex=False)
        self.limit = context.policy["max_worker_rss_bytes"]
        self.stopped = False
        self.process = ctx.Process(target=worker_main, args=(
            os.getpid(), child_request, child_result, self.requests, self.results, loader, context,
        ))
        self.process.start()
        child_request.close()
        child_result.close()

    def receive(self, deadline):
        while (remaining := deadline - time.monotonic()) > 0:
            try:
                rss = int(Path(f"/proc/{self.process.pid}/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")
            except (FileNotFoundError, ProcessLookupError):
                rss = 0
            if rss > self.limit:
                self.kill()
                raise MemoryError("RSS do worker ultrapassou o orçamento")
            if self.results.poll(min(remaining, 0.05)):
                return self.results.recv()
        self.kill()
        raise TimeoutError("prazo do worker esgotado")

    def kill(self):
        self.stopped = True
        if self.process.is_alive():
            self.process.kill()

    def close(self):
        self.requests.close()
        self.process.join(timeout=1)
        self.kill()
        self.process.join(timeout=1)
        self.results.close()


def observe(item, worker, context, identity, run_id, model, revision):
    started = time.monotonic()
    policy = context.policy
    deadline = started + (policy["case_timeout_ms"] - policy["response_reserve_ms"]) / 1000
    choices = {}
    requests = 0
    durations = []
    unavailable = None
    for field in item["missing"]:
        if unavailable:
            choices[field] = error(unavailable)
            continue
        if worker.stopped or not worker.process.is_alive():
            unavailable = "adapter_error"
            choices[field] = error(unavailable)
            continue
        if time.monotonic() >= deadline:
            unavailable = "timeout"
            choices[field] = error(unavailable)
            continue
        try:
            worker.requests.send(context.request(item, field))
            requests += 1
            choice, duration = worker.receive(deadline)
            choices[field] = choice
            durations.append(duration)
        except TimeoutError:
            unavailable = "timeout"
            choices[field] = error(unavailable)
        except (EOFError, OSError, MemoryError):
            unavailable = "adapter_error"
            choices[field] = error(unavailable)
    real = identity["mode"] == "real"
    inference_ms = sum(durations) if real and requests and len(durations) == requests else None
    return dict(contract_version=VERSION, id=item["id"], run_id=run_id, attempt=1, origin="candidate",
                identity=identity, returned_model=model, weights_revision=revision, choices=choices,
                temperature_state="warm" if real else "unknown",
                elapsed_ms=(time.monotonic() - started) * 1000 if real else None,
                load_ms=None, inference_ms=inference_ms, requests=requests, questions=requests,
                request_usage=[dict(LOCAL_USAGE, observed_api_usd=0 if real else None)
                               for _ in range(requests)])


def hardware(policy):
    cpu = re.search(r"^model name\s*:\s*(.+)", Path("/proc/cpuinfo").read_text(), re.M)
    ram = re.search(r"^MemTotal:\s*(\d+) kB", Path("/proc/meminfo").read_text(), re.M)
    return json.dumps(dict(cpu=cpu.group(1) if cpu else platform.machine(), device="cpu",
                           logical_cpus=os.cpu_count(), affinity_cpus=len(os.sched_getaffinity(0)),
                           threads=policy["threads"], concurrency=1,
                           host_ram_bytes=int(ram.group(1)) * 1024 if ram else None), ensure_ascii=False)


def run(loader, *, mode, model, revision):
    env = os.environ
    identity = json.loads(env["CLASSIFICATION_IDENTITY"])
    if (env["CLASSIFICATION_CONTRACT_VERSION"] != VERSION or identity["mode"] != mode or
            identity["requested_model"] != model or identity.get("expected_returned_model") != model or
            identity.get("expected_weights_revision") != revision):
        raise ValueError("identidade do adaptador incompatível com a configuração")
    context = Context.load(env)
    if int(env["CLASSIFICATION_TIMEOUT_MS"]) != context.policy["case_timeout_ms"]:
        raise ValueError("prazo do avaliador difere da política")
    worker = Worker(loader, context)
    try:
        metadata = worker.receive(time.monotonic() + 110)
        if mode == "fixture":
            metadata = {"runtime": metadata["runtime"]}
        ready = dict(runtime=json.dumps(dict(metadata, python=platform.python_version()), ensure_ascii=False),
                     hardware=hardware(context.policy), seed=context.policy["seed"])
        atomic_json(Path(env["CLASSIFICATION_READY_FILE"]), ready)
        for line in sys.stdin.buffer:
            item = json.loads(line.decode("utf-8"))
            if not context.eligible(item):
                raise ValueError("C02 despachou entrada completa, inválida ou fora do catálogo")
            obs = observe(item, worker, context, identity, env["CLASSIFICATION_RUN_ID"], model, revision)
            print(json.dumps(obs, ensure_ascii=False, allow_nan=False), flush=True)
    finally:
        worker.close()
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    peak = usage.ru_maxrss * 1024 if mode == "real" and usage.ru_maxrss > 0 else None
    atomic_json(Path(env["CLASSIFICATION_FINAL_FILE"]), {"peak_memory_bytes": peak})
    if mode == "real":
        print(json.dumps(dict(worker_user_cpu_s=usage.ru_utime, worker_system_cpu_s=usage.ru_stime,
                              peak_memory_bytes=peak)), file=sys.stderr, flush=True)


if __name__ == "__main__":
    from model import load_pipeline

    try:
        run(load_pipeline, mode="real", model=MODEL, revision=REVISION)
    except (EOFError, OSError, ValueError, MemoryError, KeyError) as exc:
        sys.exit(f"C04 sem execução concluída: {type(exc).__name__}: {exc}")
