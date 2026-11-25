"""Baixa e verifica a lista fechada de arquivos públicos do encoder."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
LOCK = HERE / "model-lock.json"
MODEL_DIR = CACHE / "model"

SECRETS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "FEITA_API_KEY", "TYPESAFE_API_KEY")


def write_json(destination, value):
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(destination)


def safe_environment():
    return {
        **{key: os.environ[key] for key in set(os.environ) - set(SECRETS)},
        "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
    }


def file_hash(path, expected):
    if path.stat().st_size != expected["size"]:
        raise ValueError(f"Tamanho divergente em {path.name}")
    blob = hashlib.sha1(f"blob {expected['size']}\0".encode())
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            if "sha256" not in expected:
                blob.update(chunk)
    if "sha256" in expected:
        valid = digest.hexdigest() == expected["sha256"]
    else:
        valid = blob.hexdigest() == expected["git_blob_sha1"]
    if not valid:
        raise ValueError(f"Hash divergente em {path.name}")
    return digest.hexdigest()


def verify_model():
    lock = json.loads(LOCK.read_text())
    actual = {str(path.relative_to(MODEL_DIR)) for path in MODEL_DIR.rglob("*") if path.is_file()}
    if actual != set(lock["files"]):
        raise ValueError("Arquivos locais do modelo divergem da lista congelada")
    return {
        **lock,
        "files": {
            name: {"size": expected["size"], "sha256": file_hash(MODEL_DIR / name, expected)}
            for name, expected in lock["files"].items()
        },
    }


def download_model(progress_path=None):
    def record(phase, name=None):
        if progress_path is not None:
            write_json(progress_path, {"phase": phase, "model_file": name})

    start = time.perf_counter()
    record("verify_model")
    lock = json.loads(LOCK.read_text())
    downloads = {}
    for name, expected in lock["files"].items():
        destination = MODEL_DIR / name
        if destination.is_file():
            record("verify_model", name)
            file_hash(destination, expected)
            continue
        record("download_model", name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = CACHE / "download.part"
        url = f"https://huggingface.co/{lock['model']}/resolve/{lock['revision']}/{name}"
        before = time.perf_counter()
        subprocess.run(
            [
                "curl", "-q", "--fail", "--silent", "--show-error", "--location",
                "--proto", "=https", "--proto-redir", "=https", "--connect-timeout", "30",
                "--output", str(temporary), url,
            ],
            env=safe_environment(),
            check=True,
        )
        downloads[name] = time.perf_counter() - before
        record("verify_model", name)
        file_hash(temporary, expected)
        temporary.replace(destination)
    record("verify_model")
    manifest = verify_model()
    manifest["downloads_seconds"] = downloads
    manifest["provision_seconds"] = time.perf_counter() - start
    manifest_path = CACHE / "model-manifest.json"
    if downloads or not manifest_path.exists():
        write_json(manifest_path, manifest)
    print(f"Arquivos verificados: {len(manifest['files'])}, baixados: {len(downloads)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress", type=Path)
    arguments = parser.parse_args()
    try:
        download_model(arguments.progress)
    except subprocess.CalledProcessError as error:
        print(f"Download falhou com código {error.returncode}", file=sys.stderr)
        sys.exit(error.returncode if error.returncode > 0 else 128 - error.returncode)
