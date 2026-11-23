"""Runtime CPU para a revisão pública fixada no C04."""
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MODEL = "knowledgator/gliclass-multilang-mini"
REVISION = "0bd888b6c3ef9fca5f0a9d407bddfbbc7623486b"
WEIGHTS_SHA256 = "440d8f17603d3e6f7d13a4fe7ffa7e9ef2c5a2581cceccb2f643334b92c8aea8"
SNAPSHOT = HERE / ".cache" / "weights" / REVISION
MANIFEST = HERE / "snapshot-manifest.json"
FILES = ("model.safetensors", "config.json", "tokenizer.json", "tokenizer_config.json",
         "special_tokens_map.json", "spm.model", "added_tokens.json")
PINS = {"gliclass": "0.1.22", "torch": "2.12.0+cpu", "transformers": "5.8.1"}


class ContextOverflow(ValueError):
    pass


class FullTokenizer:
    """Inspeciona a sequência montada pela biblioteca, com todo o conteúdo."""

    def __init__(self, tokenizer, limit):
        self.tokenizer = tokenizer
        self.limit = limit

    def __getattr__(self, name):
        return getattr(self.tokenizer, name)

    def __call__(self, *args, **kwargs):
        kwargs["truncation"] = False
        kwargs.pop("max_length", None)
        inputs = self.tokenizer(*args, **kwargs)
        size = inputs["input_ids"].shape[-1]
        if size > self.limit:
            raise ContextOverflow(f"contexto={size} tokens, limite={self.limit}")
        print(f"C04 tokens do contexto: {size}/{self.limit}", file=sys.stderr, flush=True)
        return inputs


def snapshot_manifest():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = manifest["files"]
    if (manifest["manifest_version"] != "1.0.0" or manifest["model"] != MODEL or
            manifest["revision"] != REVISION or set(files) != set(FILES) or
            files["model.safetensors"]["lfs_sha256"] != WEIGHTS_SHA256):
        raise ValueError("manifesto versionado diverge da revisão fixada")
    return files


def verify_snapshot(path=SNAPSHOT):
    files = snapshot_manifest()
    for name, expected in files.items():
        with (path / name).open("rb") as file:
            size = os.fstat(file.fileno()).st_size
            if size != expected["size"]:
                raise ValueError(f"tamanho local divergente: {name}")
            if "lfs_sha256" in expected:
                digest = hashlib.file_digest(file, "sha256").hexdigest()
                pinned = expected["lfs_sha256"]
            else:
                digest = hashlib.sha1(f"blob {size}\0".encode("ascii"))
                digest = hashlib.file_digest(file, lambda: digest).hexdigest()
                pinned = expected["git_blob_sha1"]
            if digest != pinned:
                raise ValueError(f"hash local divergente: {name}")
    return files["model.safetensors"]["lfs_sha256"]


def manifest_sha256():
    return hashlib.sha256(MANIFEST.read_bytes()).hexdigest()


def load_pipeline(policy):
    os.environ.update(HF_HOME=str(HERE / ".cache" / "hf"), HF_HUB_OFFLINE="1",
                      TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
                      TOKENIZERS_PARALLELISM="false", CUDA_VISIBLE_DEVICES="",
                      OMP_NUM_THREADS=str(policy["threads"]), MKL_NUM_THREADS=str(policy["threads"]),
                      OPENBLAS_NUM_THREADS=str(policy["threads"]))
    installed = {name: metadata.version(name) for name in PINS}
    if installed != PINS:
        raise ValueError(f"runtime diverge das versões fixadas: {installed}")
    digest = verify_snapshot()
    import torch
    from gliclass import GLiClassModel, ZeroShotClassificationPipeline
    from transformers import AutoTokenizer

    torch.set_num_threads(policy["threads"])
    torch.set_num_interop_threads(1)
    torch.manual_seed(policy["seed"])
    model, info = GLiClassModel.from_pretrained(
        str(SNAPSHOT), local_files_only=True, use_safetensors=True, dtype=torch.float32,
        output_loading_info=True,
    )
    if any(info.get(key) for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")):
        raise RuntimeError("carregamento dos pesos não foi estrito")
    if model.config.architecture_type != "uni-encoder":
        raise ValueError("arquitetura do snapshot diverge")
    tokenizer = AutoTokenizer.from_pretrained(str(SNAPSHOT), local_files_only=True, trust_remote_code=False)
    limit = policy["max_tokens"]
    if type(limit) is not int or not 1 <= limit <= 2048:
        raise ValueError("limite de contexto fora das políticas da C04")
    pipeline = ZeroShotClassificationPipeline(
        model, FullTokenizer(tokenizer, limit), classification_type="multi-label",
        device="cpu", progress_bar=False, max_length=limit,
    )
    return pipeline, {
        "runtime": installed, "weights_sha256": digest, "snapshot_manifest_sha256": manifest_sha256(),
        "context_profile": policy["context_profile"], "configured_context_tokens": limit,
        "encoder_max_position_embeddings": model.config.encoder_config.max_position_embeddings,
        "tokenizer_declared_model_max_length": tokenizer.model_max_length, "dtype": "float32",
    }


if __name__ == "__main__":
    print(json.dumps({"model": MODEL, "revision": REVISION, "weights_sha256": verify_snapshot(),
                      "snapshot_manifest_sha256": manifest_sha256()}))
