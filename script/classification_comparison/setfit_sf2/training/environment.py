"""Pins, uso local do snapshot e configuração CPU da SF2."""

from importlib.metadata import distribution, version
import os
from pathlib import Path
import sys
from urllib.parse import unquote

from ...setfit_pilot.provision import file_hash
from ..contracts.core import PROTOCOL, ROOT, decode, read, require, verify_sources

HERE = Path(__file__).resolve().parent
CACHE = HERE.parent / ".cache"
REQUIREMENTS = HERE / "requirements.txt"
RECIPE = PROTOCOL["training"]


def resolved_requirements(path=REQUIREMENTS):
    path = path.resolve()
    pins, files = {}, {path}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            included_pins, included_files = resolved_requirements(path.parent / line.removeprefix("-r "))
            pins.update(included_pins)
            files.update(included_files)
        elif line.startswith("torch @ "):
            # O lock do SF1 fixa a URL e o hash do wheel; normalize a versão local do CPU.
            filename = unquote(line.split("/")[-1])
            pins["torch"] = filename.split("-")[1]
        else:
            name, expected = line.split("==")
            pins[name] = expected
    return pins, files


def check_pins():
    require(sys.version_info[:2] == (3, 11), "SF2 exige Python 3.11")
    verify_sources()
    pins, _ = resolved_requirements()
    installed = {name: version(name) for name in pins}
    for name, expected in pins.items():
        require(installed[name] == expected, f"Pin divergente para {name}: {installed[name]} != {expected}")
    upstream = ROOT / PROTOCOL["sources"]["requirements"]["path"]
    torch_pin = next(line.removeprefix("torch @ ") for line in upstream.read_text().splitlines()
                     if line.startswith("torch @ "))
    url, digest = torch_pin.split("#sha256=")
    origin = decode(distribution("torch").read_text("direct_url.json") or "{}")
    require(origin.get("url") == url and origin.get("archive_info", {}).get("hashes", {}).get("sha256") == digest,
            "origem ou SHA-256 declarado do wheel Torch diverge do lock")
    return {"python": sys.version.split()[0], **installed}


def configure_cpu():
    os.environ.update(
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        HF_DATASETS_OFFLINE="1",
        HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
        HF_HUB_DISABLE_TELEMETRY="1",
        TOKENIZERS_PARALLELISM="false",
        CUDA_VISIBLE_DEVICES="",
        OMP_NUM_THREADS=str(RECIPE["torch_intraop_threads"]),
        OPENBLAS_NUM_THREADS=str(RECIPE["torch_intraop_threads"]),
        MKL_NUM_THREADS=str(RECIPE["torch_intraop_threads"]),
    )
    import torch

    require(torch.version.cuda is None and torch.version.hip is None, "SF2 exige wheel PyTorch CPU")
    torch.set_num_threads(RECIPE["torch_intraop_threads"])
    torch.set_num_interop_threads(RECIPE["torch_interop_threads"])


def snapshot_receipt(directory):
    verify_sources()
    lock = read(ROOT / PROTOCOL["sources"]["model_lock"]["path"])
    require((lock["model"], lock["revision"]) == (RECIPE["model"], RECIPE["revision"]),
            "snapshot diferente da receita aprovada")
    entries = list(directory.rglob("*"))
    require(not any(p.is_symlink() for p in entries), "snapshot contém link simbólico")
    require({p.relative_to(directory).as_posix() for p in entries if p.is_file()} == lock["files"].keys(),
            "arquivos do snapshot divergem do inventário")
    return {
        "model": lock["model"],
        "revision": lock["revision"],
        "files": {name: file_hash(directory / name, expected) for name, expected in lock["files"].items()},
    }


def load_body(path):
    from sentence_transformers import SentenceTransformer

    body = SentenceTransformer(
        str(path), device="cpu", cache_folder=str(CACHE / "transformers"),
        trust_remote_code=False, local_files_only=True, model_kwargs={"use_safetensors": True},
    )
    max_length = body.max_seq_length
    require(max_length == RECIPE["max_sequence_length"], "limite de sequência divergente")
    return body


def length(tokenizer, text):
    return len(tokenizer(text, add_special_tokens=True, truncation=False, verbose=False)["input_ids"])
