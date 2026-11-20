"""Runner no host. Cria uma pilha privada por rodada e preserva os artefatos."""
import argparse
import fcntl
import hashlib
import json
import os
import platform
import resource
import secrets
import subprocess
import threading
import time
from pathlib import Path

from protocol import DIRECTORY, append, now_ms, plan, utc, write_json
from report import publish, render_matrix


ROOT = DIRECTORY.parents[2]
PROJECT = "cloudwalk_f08_load"
BASE = "f23b21e53357f926e8ca1ba3c3a11da7242daf9a"
SERVICES = ("api", "worker", "outbox", "requests", "events", "mock", "observe")
PROJECT_FILTER = f"label=com.docker.compose.project={PROJECT}"
CREDENTIALS = ("POSTGRES_PASSWORD", "F08_RAILS_SECRET", "CLOUDWALK_CHANNEL_SECRET",
               "CLOUDWALK_AGENT_REQUESTS_SECRET", "CLOUDWALK_AGENT_EVENTS_SECRET")
ROLES = ("alex", "bia", "cris", "supervisor")


class Blocked(RuntimeError):
    pass


def safe_env(output):
    env = {key: value for key, value in os.environ.items()
           if key in {"PATH", "HOME", "USER", "XDG_RUNTIME_DIR", "XDG_CONFIG_HOME", "SSH_AUTH_SOCK"}
           or key.startswith("DOCKER_")}
    env.update({key: secrets.token_hex(32) for key in CREDENTIALS})
    env.update(POSTGRES_USER="cloudwalk", F08_UID=str(os.getuid()), F08_GID=str(os.getgid()),
               F08_OUTPUT=str(output), CLOUDWALK_DEMO_PASSWORDS=json.dumps({
                   f"{name}@example.test": secrets.token_hex(16) for name in ROLES}))
    return env


class Stack:
    def __init__(self, output):
        self.output = output
        self.env = safe_env(output)
        self.compose = ["compose", "-p", PROJECT, "--env-file", str(DIRECTORY / "stack.env"),
                        "-f", "compose.yml", "-f", str(DIRECTORY / "compose.yml")]

    def operation(self, args):
        command = list(args)
        if command[:len(self.compose)] == self.compose:
            command = command[len(self.compose):]
            while command[:1] == ["--profile"]:
                command = command[2:]
            return "compose " + (command[0] if command else "indisponível")
        return " ".join(command[:2])

    def diagnostic(self, stderr):
        # Somente causas conhecidas. O stderr do build pode conter comandos, credenciais ou configuração.
        causes = {"permission denied": "permissão negada", "cannot connect to the docker daemon": "daemon indisponível",
                  "unauthorized": "autenticação recusada", "pull access denied": "acesso à imagem recusado",
                  "manifest unknown": "manifesto da imagem ausente", "no space left": "espaço em disco insuficiente",
                  "no such host": "DNS não resolveu o endereço", "i/o timeout": "timeout de rede",
                  "connection refused": "conexão recusada", "unhealthy": "verificação de saúde falhou",
                  "failed to solve": "falha no build", "failed to complete successfully": "serviço de preparação falhou",
                  "context deadline exceeded": "prazo da operação excedido"}
        text = stderr.lower()
        hints = [description for fragment, description in causes.items() if fragment in text]
        affected = [service for service in (*SERVICES, "generator", "db_setup", "kafka_setup", "db", "kafka")
                    if f"{PROJECT}-{service}-" in text]
        if affected:
            hints.append("serviços citados: " + ", ".join(affected))
        return "; ".join(hints) or "sem causa reconhecida no diagnóstico"

    def command(self, *args, timeout=30, check=True):
        try:
            result = subprocess.run(["docker", *args], cwd=ROOT, env=self.env, capture_output=True,
                                    text=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Blocked(f"Docker {self.operation(args)}: {type(error).__name__}") from error
        if check and result.returncode:
            raise Blocked(f"Docker {self.operation(args)} devolveu código {result.returncode}: "
                          f"{self.diagnostic(result.stderr)}")
        return result

    def call(self, *args, **kwargs):
        return self.command(*self.compose, *args, **kwargs)

    def preflight(self):
        host = self.env.get("DOCKER_HOST")
        if not host or self.env.get("DOCKER_CONTEXT"):
            context = self.command("context", "show").stdout.strip()
            host = self.command("context", "inspect", context,
                                "--format", "{{.Endpoints.docker.Host}}").stdout.strip()
        if not host.startswith("unix://"):
            raise Blocked("O ensaio requer daemon Docker local via socket Unix para comparar recursos do host")
        daemon = json.loads(self.command("info", "--format", "{{json .}}").stdout)
        for kind, arguments in (("contêiner", ("ps", "-aq")), ("rede", ("network", "ls", "-q")),
                                ("volume", ("volume", "ls", "-q"))):
            if self.command(*arguments, "--filter", PROJECT_FILTER).stdout.strip():
                raise Blocked(f"{kind} preexistente do projeto {PROJECT}; preservado")
        # Um recurso criado fora do Compose pode ter o nome esperado e nenhuma label.
        for kind, args, names in (
            ("rede", ("network", "ls", "--format", "{{.Name}}"), {f"{PROJECT}_default"}),
            ("volume", ("volume", "ls", "--format", "{{.Name}}"),
             {f"{PROJECT}_postgres_data", f"{PROJECT}_kafka_data"}),
        ):
            if names.intersection(self.command(*args).stdout.split()):
                raise Blocked(f"{kind} preexistente com nome reservado ao ensaio; preservado")
        return {key: daemon.get(key) for key in ("ServerVersion", "OperatingSystem", "OSType", "Architecture",
                                                 "NCPU", "MemTotal", "CgroupDriver", "CgroupVersion")}

    def configuration(self):
        config = json.loads(self.call("--profile", "load", "--profile", "unused", "config", "--format", "json").stdout)
        if config["name"] != PROJECT or not config["networks"]["default"]["internal"]:
            raise Blocked("Compose não isolou o projeto/rede")
        if config["networks"]["default"]["name"] != f"{PROJECT}_default":
            raise Blocked("Rede fora do projeto")
        for key, resource in config["volumes"].items():
            if resource["name"] != f"{PROJECT}_{key}" or resource.get("external"):
                raise Blocked("Volume fora do projeto")
        fields = ("image", "cpus", "cpuset", "mem_limit", "mem_reservation", "pids_limit", "ulimits", "deploy", "scale")
        result = {}
        for name, service in config["services"].items():
            if service.get("ports") or service.get("container_name") or service.get("privileged"):
                raise Blocked(f"Serviço {name} viola isolamento de portas ou contêiner")
            result[name] = {key: service.get(key) for key in fields}
        return result

    def state(self, service):
        identifier = self.call("ps", "-aq", service).stdout.strip()
        if not identifier or "\n" in identifier:
            raise Blocked(f"Serviço {service} sem contêiner único")
        state = json.loads(self.command("inspect", "--format", "{{json .State}}", identifier).stdout)
        return {key: state[key] for key in ("Status", "StartedAt", "FinishedAt")}

    def images(self):
        ids = self.command("ps", "-aq", "--filter", PROJECT_FILTER).stdout.split()
        if not ids:
            return []
        fmt = "{{index .Config.Labels \"com.docker.compose.service\"}}\t{{.Image}}\t{{.Config.Image}}"
        return [dict(zip(("service", "image_id", "image"), line.split("\t")))
                for line in self.command("inspect", "--format", fmt, *ids).stdout.splitlines()]

    def resources(self, stop):
        previous_cpu = None
        while not stop.is_set():
            start = now_ms()
            try:
                ids = self.command("ps", "-q", "--filter", PROJECT_FILTER, timeout=4).stdout.split()
                fmt = '{{.ID}}\t{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.PIDs}}'
                lines = (self.command("stats", "--no-stream", "--no-trunc", "--format", fmt, *ids,
                                      timeout=8).stdout.splitlines() if ids else [])
                processes = [dict(zip(("id", "container", "cpu_percent", "ram_used_limit", "ram_percent", "pids"),
                                      line.split("\t"))) for line in lines]
                row = {"containers": processes, "load_average": list(os.getloadavg())}
                proc_stat = Path("/proc/stat")
                if proc_stat.exists():
                    with proc_stat.open() as file:
                        values = [int(value) for value in file.readline().split()[1:9]]
                    counters = (sum(values), sum(values[3:5]))
                    if previous_cpu and counters[0] > previous_cpu[0]:
                        row["host_cpu_busy_percent"] = 100 * (1 - (counters[1] - previous_cpu[1]) /
                                                             (counters[0] - previous_cpu[0]))
                    previous_cpu = counters
                mem = Path("/proc/meminfo")
                if mem.exists():
                    row["host_memory_kib"] = {key: int(value.split()[0])
                                              for key, _, value in (line.partition(":") for line in mem.read_text().splitlines())
                                              if key in {"MemTotal", "MemAvailable"}}
            except (Blocked, OSError, ValueError) as error:
                row = {"error": type(error).__name__}
            append(self.output / "resources.jsonl", {"sample_ms": start, "cost_ms": now_ms() - start, **row})
            stop.wait(max(0, 5 - (now_ms() - start) / 1000))

    def fault(self, stop, window, config, result):
        wait_ms = window["start_ms"] + config["fault_after_seconds"] * 1000 - now_ms()
        if stop.wait(max(0, wait_ms / 1000)):
            return
        try:
            result["stop_requested_ms"] = now_ms()
            self.call("stop", "-t", "10", "kafka")
            result.update(stopped_observed_ms=now_ms(), stopped_state=self.state("kafka"))
            write_json(self.output / "fault.json", result)
            if stop.wait(config["fault_seconds"]):
                return
            result["start_requested_ms"] = now_ms()
            self.call("start", "kafka")
            result.update(start_returned_ms=now_ms(), started_state=self.state("kafka"))
        except Blocked as error:
            result["error"] = str(error)
        finally:
            write_json(self.output / "fault.json", result)

    def generator(self, js):
        (self.output / "k6-console.jsonl").touch()
        return subprocess.Popen(["docker", *self.compose, "run", "--rm", "--no-deps", "-T", "generator",
                                 "run", "--log-format", "raw", "--no-color", "--no-usage-report",
                                 "--address", "", "--console-output", "/results/k6-console.jsonl", f"/load/{js}"],
                                cwd=ROOT, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def console(path):
    if path.exists():
        with path.open() as file:
            for line in file:
                if line.endswith("\n"):
                    try:
                        yield json.loads(line[line.index("{"):])
                    except (ValueError, json.JSONDecodeError):
                        continue


def wait_file(path, seconds, *, failure=None):
    limit = time.monotonic() + seconds
    while time.monotonic() < limit:
        if path.exists():
            return read(path)
        if failure and failure.exists():
            raise Blocked(f"Observador: {read(failure)['reason']}")
        time.sleep(0.15)
    raise Blocked(f"Artefato {path.name} ausente após {seconds} s")


def wait_setup(output, generator):
    limit = time.monotonic() + 45
    while time.monotonic() < limit:
        for event in console(output / "k6-console.jsonl"):
            if event["type"] == "setup":
                return event["at_ms"]
        if generator.poll() is not None:
            raise Blocked(f"k6 encerrou antes do início (código {generator.returncode})")
        time.sleep(0.05)
    raise Blocked("k6 sem início observado em 45 s")


def revision():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def source_hashes():
    files = sorted(path for path in DIRECTORY.iterdir() if path.is_file())
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}


def round_run(output, config):
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    stack = Stack(output)
    stop = threading.Event()
    resource_job = fault_job = generator = None
    started_stack = False
    fault = {}
    manifest = {
        "schema_version": 1, "run_id": config["run_id"], "scenario": config["scenario"],
        "revision": revision(), "base": BASE, "source_sha256": source_hashes(),
        "started_ms": now_ms(), "parameters": config, "compose_project": PROJECT,
        "mock": {"implementation": "integration/agent_flow.py", "artificial_delay": False},
        "jev": {"configured_mode": "disabled", "credential_present": False},
        "topology": {"puma_threads": 5, "solid_queue_processes": 1, "solid_queue_threads_per_process": 3,
                     "outbox_processes": 1, "replicas_per_service": 1, "kafka_partitions_per_topic": 3},
        "runner_host": {"python": platform.python_version(), "kernel": platform.release(),
                        "cpu_logical": os.cpu_count(), "architecture": platform.machine(),
                        "rlimit_nofile": list(resource.getrlimit(resource.RLIMIT_NOFILE))},
        "observer": {"sql_period_ms": 2000, "eligibility_period_ms": 250, "kafka_period_ms": 5000,
                     "resources_period_ms": 5000, "followup_workers": 32},
    }
    manifest["started_at_utc"] = utc(manifest["started_ms"])
    entries = plan(config["run_id"], config["seed"], config["stages"], human=config["scenario"] == "human")
    write_json(output / "plan.json", entries)
    write_json(output / "config.json", config)
    try:
        manifest["compose_version"] = stack.command("compose", "version", "--short").stdout.strip()
        manifest["configured_limits"] = stack.configuration()
        manifest["docker_host"] = stack.preflight()
        started_stack = True
        manifest["stack_start_requested_ms"] = now_ms()
        stack.call("--profile", "load", "pull", "generator", timeout=300)
        stack.call("up", "-d", "--build", "--wait", "--wait-timeout", "150", *SERVICES, timeout=900)
        manifest["stack_started_ms"] = now_ms()
        manifest["images"] = stack.images()
        manifest["generator_image_id"] = stack.command(
            "image", "inspect", "--format", "{{.Id}}", "grafana/k6:2.3.0").stdout.strip()
        manifest["k6_version"] = stack.call("run", "--rm", "--no-deps", "-T", "generator", "version").stdout.strip()
        ready = wait_file(output / "ready.json", 150, failure=output / "observer-failure.json")
        manifest["readiness"] = ready
        write_json(output / "config.json", {**config, "channels": ready["channels"]})
        chat = config["chat"]
        generator = stack.generator("chat.js" if chat else "generate.js")
        started = wait_setup(output, generator)
        resource_job = threading.Thread(target=stack.resources, args=(stop,))
        resource_job.start()
        arrival_seconds = chat["ramp_seconds"] + chat["hold_seconds"] if chat else sum(s for _, s in config["stages"])
        window = {"start_ms": started, "arrivals_end_ms": started + arrival_seconds * 1000,
                  "end_ms": started + (arrival_seconds + config["observe_seconds"]) * 1000}
        manifest["window"] = window
        write_json(output / "window.json", window)
        if config["fault_after_seconds"] is not None:
            fault_job = threading.Thread(target=stack.fault, args=(stop, window, config, fault))
            fault_job.start()
        while now_ms() < window["end_ms"]:
            failure = read(output / "observer-failure.json")
            if failure:
                raise Blocked(f"Observador: {failure['reason']}")
            time.sleep(min(0.25, max(0, (window["end_ms"] - now_ms()) / 1000)))
        manifest["cutoff_observed_ms"] = now_ms()
        manifest["k6_exit"] = generator.wait(timeout=35)
        write_json(output / "finish.json", {"at_ms": now_ms()})
        manifest["observation"] = wait_file(output / "observed.json", 65, failure=output / "observer-failure.json")
        if fault_job:
            fault_job.join(timeout=35)
            manifest["fault"] = fault
        write_json(output / "manifest.json", manifest)
    except (Blocked, OSError, subprocess.SubprocessError, ValueError) as error:
        manifest["blocked"] = str(error) if isinstance(error, Blocked) else type(error).__name__
    finally:
        stop.set()
        if generator and generator.poll() is None:
            generator.terminate()
            try:
                generator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                generator.kill()
                generator.wait()
        for job in (fault_job, resource_job):
            if job:
                job.join()
        if started_stack:
            try:
                stack.call("down", "-v", "--remove-orphans", "--timeout", "5", timeout=45)
                manifest["cleanup"] = "concluída"
            except Blocked as error:
                manifest["cleanup"] = str(error)
        manifest["finished_ms"] = now_ms()
        manifest["finished_at_utc"] = utc(manifest["finished_ms"])
        manifest["artifacts"] = sorted({path.name for path in output.iterdir()} |
                                       {"manifest.json", "report.json", "report.md", "reconciliation.jsonl"})
        write_json(output / "manifest.json", manifest)
    return publish(output, manifest, entries, list(console(output / "k6-console.jsonl")))


def pair(value):
    try:
        rate, seconds = map(int, value.split(":"))
        if min(rate, seconds) > 0:
            return rate, seconds
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("use TAXA:SEGUNDOS, ambos inteiros positivos")


def arguments(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=["config", "smoke", "reference", "ramp", "human", "chat"])
    cli.add_argument("--seed", type=int, default=8026)
    cli.add_argument("--rate", type=int)
    cli.add_argument("--seconds", type=int)
    cli.add_argument("--observe-seconds", type=int)
    cli.add_argument("--vus", type=int, default=50)
    cli.add_argument("--rounds", type=int, default=3, help="rodadas por condição da referência")
    cli.add_argument("--fault-after", type=int)
    cli.add_argument("--fault-seconds", type=int)
    cli.add_argument("--stage", type=pair, action="append")
    cli.add_argument("--chat-target", type=int, action="append")
    cli.add_argument("--chat-ramp-seconds", type=int, default=120)
    cli.add_argument("--chat-hold-seconds", type=int, default=300)
    cli.add_argument("--period-seconds", type=int, default=100)
    cli.add_argument("--output", type=Path, default=DIRECTORY / "results")
    args = cli.parse_args(argv)
    optional = (args.rate, args.seconds, args.observe_seconds, args.fault_after, args.fault_seconds)
    required = (args.vus, args.rounds, args.chat_ramp_seconds, args.chat_hold_seconds, args.period_seconds)
    if any(value <= 0 for value in (*required, *(args.chat_target or [])) if value is not None):
        cli.error("parâmetros devem ser positivos")
    if any(value <= 0 for value in optional if value is not None) or args.seed < 0:
        cli.error("parâmetros de tempo e taxa devem ser positivos; a semente pode ser zero")
    for flags, allowed in ((args.stage, {"ramp"}), (args.chat_target, {"chat"}),
                           (args.fault_after or args.fault_seconds, {"smoke", "reference"}),
                           (args.rate or args.seconds, {"smoke", "reference", "human"})):
        if flags and args.mode not in allowed:
            cli.error(f"parâmetro incompatível com {args.mode}")
    if args.mode == "smoke" and args.fault_seconds and not args.fault_after:
        cli.error("--fault-seconds no smoke requer --fault-after")
    for config in configurations(args):
        length = sum(seconds for _, seconds in config["stages"])
        if config["fault_after_seconds"] is not None and config["fault_after_seconds"] >= length:
            cli.error("a parada deve ser solicitada antes do fim da carga")
        if config["observe_seconds"] > 120:
            cli.error("janela posterior máxima de 120 segundos")
    return args


def configurations(args):
    defaults = {"reference": (5, 300, 120), "smoke": (5, 3, 20),
                "ramp": (5, 60, 120), "human": (2, 10, 120), "chat": (1, 1, 20)}
    if args.mode == "config":
        return
    rate, seconds, observe = defaults[args.mode]
    stages = [(args.rate or rate, args.seconds or seconds)]
    subjects = [False]
    if args.mode == "reference":
        subjects = [condition for _ in range(args.rounds) for condition in (False, True)]
    if args.mode == "smoke":
        subjects = [args.fault_after is not None]
    if args.mode == "ramp":
        stages = args.stage or [(5, 60), (10, 60), (20, 60), (40, 60)]
    if args.mode == "chat":
        stages = []
        subjects = args.chat_target or [100, 1000, 10000]
    for number, subject in enumerate(subjects, start=1):
        chat = None
        if args.mode == "chat":
            chat = {"target": subject, "ramp_seconds": args.chat_ramp_seconds,
                    "hold_seconds": args.chat_hold_seconds, "period_seconds": args.period_seconds}
        yield {"scenario": args.mode, "ordinal": number, "seed": args.seed, "stages": stages,
               "observe_seconds": args.observe_seconds or observe, "vus": args.vus,
               "fault_after_seconds": (args.fault_after or 60) if subject is True else None,
               "fault_seconds": (args.fault_seconds or 30) if subject is True else None, "chat": chat}


def main(argv=None):
    args = arguments(argv)
    if args.mode == "config":
        config = Stack(args.output.resolve()).configuration()
        print(f"{PROJECT}: rede interna, volumes próprios, sem portas publicadas ({len(config)} serviços).")
        return 0
    output = args.output.resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    batch_id = f"f08-{args.mode}-{now_ms()}-{secrets.token_hex(3)}"
    folder = output / batch_id
    folder.mkdir(mode=0o700)
    lock_path = Path(f"/tmp/{PROJECT}-{os.getuid()}.lock")
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Blocked(f"Já existe um runner {PROJECT} ativo para este usuário") from None
        summaries = []
        planned = list(configurations(args))
        for index, config in enumerate(planned):
            config["run_id"] = f"{batch_id}-{config['ordinal']:02}"
            result = round_run(folder / config["run_id"], config)
            if result.get("cleanup") not in (None, "concluída") and result["state"] != "bloqueado":
                result.update(state="bloqueado", reason="limpeza interrompida: " + result["cleanup"])
            summaries.append(result)
            if result["state"] == "bloqueado":
                for pending in planned[index + 1:]:
                    summaries.append({"run_id": f"{batch_id}-{pending['ordinal']:02}", "parameters": pending,
                                      "state": "não executada", "executed": False,
                                      "reason": f"Interrompida após {config['run_id']}: {result['reason']}"})
            print(f"{config['run_id']} {result['state']} — {folder / config['run_id'] / 'report.md'}", flush=True)
            write_json(folder / "matrix.json", summaries)
            (folder / "matrix.md").write_text(render_matrix(summaries))
            if result["state"] == "bloqueado" or result.get("cleanup") not in (None, "concluída"):
                break
    return 0 if all(row["state"] == "aprovado" for row in summaries) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Blocked as error:
        raise SystemExit(str(error)) from None
