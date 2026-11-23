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

from model import LABEL_SEPARATOR, MODEL, REVISION, ContextOverflow

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
class Request:
    text: str
    labels_by_field: dict
    prompt: str


@dataclass(frozen=True)
class Context:
    catalog: dict
    prompts: dict
    rubric: str
    policy: dict
    abstention_descriptions: dict

    @classmethod
    def load(cls, env):
        rubric = Path(env["CLASSIFICATION_RUBRIC"]).read_text(encoding="utf-8")
        catalog = read_json(ROOT / "script/f08/jev/catalog.json")
        prompts = read_json(env["CLASSIFICATION_PROMPT"])
        policy = read_json(env["CLASSIFICATION_POLICY"])
        if policy["examples"]:
            raise ValueError("baseline exige zero exemplos")
        representation = policy.get("label_representation", "codes")
        layout = policy.get("forward_layout", "separate")
        if representation not in ("codes", "descriptive") or layout not in ("separate", "grouped"):
            raise ValueError("representação ou estratégia de forward inválida")
        descriptions = {}
        if representation == "descriptive":
            for field, heading in zip(FIELDS, ("Categoria", "Prioridade"), strict=True):
                section = rubric.partition(f"\n## {heading}\n")[2].partition("\n## ")[0]
                definition = re.search(rf"(?m)^- `{ABSTENTION}`: (.*(?:\n[ ]+[^\n]+)*)", section)
                if not definition:
                    raise ValueError(f"rubrica sem descrição de abstenção para {field}")
                descriptions[field] = " ".join(definition.group(1).split())
        return cls(catalog, prompts, rubric, policy, descriptions)

    def groups(self, missing):
        if self.policy.get("forward_layout") == "grouped" and len(missing) == 2:
            return [tuple(missing)]
        return [(field,) for field in missing]

    def request(self, item, fields):
        labels_by_field = {}
        for field in fields:
            if self.abstention_descriptions:
                descriptions = {**self.catalog[field], ABSTENTION: self.abstention_descriptions[field]}
                labels_by_field[field] = {f"{code}: {description}": code for code, description in descriptions.items()}
            else:
                labels_by_field[field] = {code: code for code in (*self.catalog[field], ABSTENTION)}
        received = {
            key: {"valor": value, "significado": self.catalog[key][value]}
            if key not in item["missing"] else {"valor": value, "significado": "campo ausente"}
            for key, value in item["received"].items()
        }
        context = {
            "marca": item["brand"], "mascara_de_omissao": item["missing"],
            "campos_recebidos": received, "catalogo": self.catalog,
        }
        context_json = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
        task, instructions = (fields[0], "context") if len(fields) == 1 else ("both", "both_context")
        prompt = (
            f"{self.prompts[task]}\n{self.prompts[instructions]}\n"
            f"Contexto do atendimento (JSON):\n{context_json}\n"
            f"Rubrica comum (integral):\n{self.rubric}\nRelato:\n"
        )
        return Request(item["text"], labels_by_field, prompt)

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


def invalid_output(output, labels):
    # A saída esperada usa JSON. Valores não finitos em qualquer nível viram nulos.
    try:
        raw = json.loads(json.dumps(output), parse_constant=lambda _constant: None)
    except (TypeError, ValueError, RecursionError):
        raw = {"tipo_python": type(output).__name__}
    if raw is None or (isinstance(raw, str) and raw in (*labels.values(), ABSTENTION)):
        # Um valor presente mas inválido não pode parecer um código válido ou uma omissão no IPC.
        raw = {"valor": raw}
    return dict(status="invalid", raw=raw, reason="invalid_output", score=None)


def choice_from_output(output, labels, score_kind):
    if output is None or (isinstance(output, list) and output in ([], [[]])):
        return dict(status="invalid", raw=None, reason="missing_output", score=None)
    if not isinstance(output, list) or len(output) != 1 or not isinstance(output[0], list):
        return invalid_output(output, labels)

    scores = {}
    for row in output[0]:
        if not isinstance(row, dict):
            return invalid_output(output, labels)
        label, score = row.get("label"), row.get("score")
        if (not isinstance(label, str) or label not in labels or label in scores or
                type(score) not in (int, float) or not 0 <= score <= 1):
            return invalid_output(output, labels)
        scores[label] = score
    if scores.keys() != labels.keys():
        return invalid_output(output, labels)

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
    by_field = request.labels_by_field
    options = dict(prompt=request.prompt, examples=None, batch_size=1, threshold=policy["pipeline_threshold"])
    if len(by_field) == 1:
        field, labels = next(iter(by_field.items()))
        result = pipeline(request.text, list(labels), **options)
        return {field: choice_from_output(result, labels, policy["score_kind"])}

    hierarchy = {field: list(labels) for field, labels in by_field.items()}
    result = pipeline(request.text, hierarchy, classification_type="multi-label",
                      return_hierarchical=False, **options)
    flat = {field: {f"{field}{LABEL_SEPARATOR}{label}": code for label, code in labels.items()}
            for field, labels in by_field.items()}
    if result is None or (isinstance(result, list) and result in ([], [[]])):
        return {field: choice_from_output(result, labels, policy["score_kind"]) for field, labels in flat.items()}

    # A forma plana preserva nomes originais e evita o zero implícito do retorno hierárquico.
    owners = {label: field for field, labels in flat.items() for label in labels}
    rows = {field: [] for field in by_field}
    if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], list):
        return {field: invalid_output(result, labels) for field, labels in flat.items()}
    for row in result[0]:
        label = row.get("label") if isinstance(row, dict) else None
        if not isinstance(label, str) or label not in owners:
            return {field: invalid_output(result, labels) for field, labels in flat.items()}
        rows[owners[label]].append(row)
    return {field: choice_from_output([rows[field]], labels, policy["score_kind"])
            for field, labels in flat.items()}


def worker_main(parent, request_pipe, result_pipe, unused_request, unused_result, loader, context):
    unused_request.close()
    unused_result.close()
    # O avaliador pode encerrar o adaptador por SIGKILL em caso de interrupção.
    if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
        return
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    warming = True

    def on_forward():
        if not warming:
            result_pipe.send(("forward", None))

    try:
        started = time.monotonic()
        pipeline, metadata = loader(context.policy, on_forward)
        loaded = time.monotonic()
        sample = dict(brand="marca-sintetica", text="Mensagem sintética usada para aquecer o runtime.",
                      received={}, missing=list(FIELDS))
        for fields in context.groups(FIELDS):
            observed = infer(pipeline, context.request(sample, fields), context.policy)
            if any(choice["status"] == "invalid" for choice in observed.values()):
                raise RuntimeError("saída do aquecimento fora da interface")
        warming = False
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
            choices = infer(pipeline, request, context.policy)
        except ContextOverflow as exc:
            print(f"C04 limite de representação: {exc}", file=sys.stderr, flush=True)
            choices = {field: error("adapter_error") for field in request.labels_by_field}
        except Exception as exc:
            print(f"C04 erro na inferência: {type(exc).__name__}", file=sys.stderr, flush=True)
            choices = {field: error("adapter_error") for field in request.labels_by_field}
        result_pipe.send(("result", (choices, (time.monotonic() - started) * 1000)))


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
    requests = questions = 0
    started_groups = 0
    durations = []
    unavailable = None
    for fields in context.groups(item["missing"]):
        if unavailable is None:
            if worker.stopped or not worker.process.is_alive():
                unavailable = "adapter_error"
            elif time.monotonic() >= deadline:
                unavailable = "timeout"
        if unavailable:
            choices.update({field: error(unavailable) for field in fields})
            continue

        forwarded = False
        try:
            worker.requests.send(context.request(item, fields))
            event, payload = worker.receive(deadline)
            while event == "forward":
                requests += 1
                if not forwarded:
                    questions += len(fields)
                    started_groups += 1
                    forwarded = True
                event, payload = worker.receive(deadline)
            if event != "result":
                raise ValueError("evento inesperado do worker")
            response, duration = payload
            if not forwarded and any(choice["status"] != "error" for choice in response.values()):
                raise ValueError("resultado do worker sem forward")
            choices.update(response)
            if forwarded:
                durations.append(duration)
        except TimeoutError:
            unavailable = "timeout"
        except (EOFError, OSError, MemoryError, ValueError):
            unavailable = "adapter_error"
        if unavailable:
            choices.update({field: error(unavailable) for field in fields})
    real = identity["mode"] == "real"
    inference_ms = sum(durations) if real and started_groups and len(durations) == started_groups else None
    return dict(contract_version=VERSION, id=item["id"], run_id=run_id, attempt=1, origin="candidate",
                identity=identity, returned_model=model, weights_revision=revision, choices=choices,
                temperature_state="warm" if real and requests else "unknown",
                elapsed_ms=(time.monotonic() - started) * 1000 if real else None,
                load_ms=None, inference_ms=inference_ms, requests=requests, questions=questions,
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
            print(json.dumps(obs, ensure_ascii=True, allow_nan=False), flush=True)
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
