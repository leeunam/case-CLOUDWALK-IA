"""Compara os sete históricos F08 em diretório temporário e imprime JSON."""
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

from protocol import rows
from report import evidence, summarize
from run import console


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


PUBLISH_METADATA = {"parameters", "revision", "run_id", "scenario", "schema_version", "units", "window_utc"}


def compare_fields(original, updated):
    changed, added = [], []

    def inspect(before, after, path):
        if isinstance(before, dict) and isinstance(after, dict):
            for key in sorted(set(before) | set(after)):
                child = f"{path}.{key}" if path else key
                if key not in before:
                    added.append(child)
                elif key not in after:
                    changed.append(child)
                else:
                    inspect(before[key], after[key], child)
        elif before != after:
            changed.append(path)

    inspect({k: value for k, value in original.items() if k not in PUBLISH_METADATA}, json.loads(json.dumps(updated)), "")
    return changed, added


def compare(directory):
    read = lambda name: json.loads((directory / name).read_bytes())
    original, manifest, plan = read("report.json"), read("manifest.json"), read("plan.json")
    events = list(console(directory / "k6-console.jsonl"))
    turns, kafka, cases = evidence(directory, manifest, plan, events)
    updated = summarize(directory, manifest, plan, events, turns, kafka, cases)
    changed, added = compare_fields(original, updated)
    original_turns = list(rows(directory / "reconciliation.jsonl"))
    different = sum(a != b for a, b in zip(original_turns, turns)) + abs(len(original_turns) - len(turns))
    return {"run_id": manifest["run_id"], "original": original["state"], "reanalisado": updated["state"],
            "iniciais_202": updated["initial"]["http_202"], "continuacoes_202": updated["followups"]["http_202"],
            "turnos_concluidos": updated["completions"]["ai_turns_in_window"],
            "p95_aceite_inicial_ms": updated["initial"]["latency_accept"]["p95"],
            "p95_resposta_inicial_ms": updated["initial"]["latency_persisted"]["p95"],
            "linhas_de_reconciliacao": len(turns), "linhas_divergentes": different,
            "campos_divergentes": changed, "campos_adicionados": added,
            "entradas_sem_plano": len(updated["integrity"]["unplanned_entries"]),
            "mensagens_sem_atribuicao": updated["integrity"]["unattributed_message_count"]}


def main():
    source = Path(__file__).resolve().parents[3] / "docs/evidencias/f08"
    result = {"sha256_report_py": digest(Path(__file__).with_name("report.py").read_bytes()), "lotes": {}}
    for name in ("referencia-inicial", "referencia-complemento"):
        folder = source / name
        archive = folder / "dados-brutos.tar.gz"
        checksum = digest(archive.read_bytes())
        if checksum != (folder / "SHA256SUMS").read_text().split()[0]:
            raise ValueError(f"SHA-256 inválido em {name}")
        inventory = {row["path"]: row for row in json.loads((folder / "inventario.json").read_bytes())}
        with tempfile.TemporaryDirectory() as temp, tarfile.open(archive) as tar:
            root = Path(temp)
            for member in tar:
                item = inventory.pop(member.name)
                destination = (root / member.name).resolve()
                if not member.isfile() or not destination.is_relative_to(root):
                    raise ValueError(member.name)
                data = tar.extractfile(member).read()
                if len(data) != item["bytes"] or digest(data) != item["sha256"]:
                    raise ValueError(member.name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
            if inventory:
                raise ValueError(f"Membros ausentes: {list(inventory)}")
            result["lotes"][name] = {"sha256": checksum, "arquivos_verificados": len(tar.getmembers()),
                                     "rodadas": [compare(d) for d in sorted(root.iterdir()) if d.is_dir()]}
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
