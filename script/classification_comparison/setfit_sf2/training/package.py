"""Exporta e verifica o pacote local antes de recarregar a cabeça serializada."""

from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from ..contracts.artifacts import validate_manifest
from ..contracts.core import FIELDS, VERSION, decode, require, sha256, structure
from .environment import length, load_body

COMPONENTS = ("base_encoder", "encoder", "head", "tokenizer", "training_evidence")
TOKENIZER_FILES = {
    "sentencepiece.bpe.model", "special_tokens_map.json", "tokenizer.json",
    "tokenizer_config.json", "added_tokens.json", "vocab.txt", "vocab.json", "merges.txt",
}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def read_hashed(path, expected_digest, *, jsonl=False):
    encoded = path.read_bytes()
    require(hashlib.sha256(encoded).hexdigest() == expected_digest, f"SHA-256 não confere para {path.name}")
    decoded = encoded.decode("utf-8")
    return [decode(line) for line in io.StringIO(decoded, newline=None)] if jsonl else decode(decoded)


def write_json(path, value):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(json_bytes(value))
            stream.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def package_paths(root, manifest):
    files = manifest["files"]
    paths = {"training_freeze": root / "training-freeze.json", "arguments": root / "arguments.json"}
    for field in FIELDS:
        directory = root / field
        paths[field + ".manifest"] = directory / "manifest.json"
        for component in COMPONENTS:
            role = field + "." + component
            prefix = role + "/"
            paths[role] = directory / (component + ".json")
            members = {key.removeprefix(prefix) for key in files if key.startswith(prefix)}
            base = "body" if component in ("encoder", "tokenizer") else component
            for name in members:
                member = PurePosixPath(name)
                require(member.parts and not member.is_absolute() and ".." not in member.parts and
                        str(member) == name and "\\" not in name, "nome de membro inválido")
                paths[prefix + name] = directory / base / name
    require(paths.keys() == files.keys(), "papéis desconhecidos no pacote")
    return paths


def export_specialist(root, field, model, snapshot, evidence):
    import joblib

    directory = root / field
    directory.mkdir()
    body_dir = directory / "body"
    model.model_body.save(str(body_dir), create_model_card=False, safe_serialization=True)
    for component in ("base_encoder", "head", "training_evidence"):
        (directory / component).mkdir()
    write_json(directory / "base_encoder/snapshot.json", snapshot)
    write_json(directory / "training_evidence/run.json", evidence)
    joblib.dump(model.model_head, directory / "head/logistic.joblib", compress=3)
    members = {
        "base_encoder": [directory / "base_encoder/snapshot.json"],
        "head": [directory / "head/logistic.joblib"],
        "training_evidence": [directory / "training_evidence/run.json"],
        "encoder": [],
        "tokenizer": [],
    }
    for path in sorted(body_dir.rglob("*")):
        if path.is_file():
            component = "tokenizer" if path.name in TOKENIZER_FILES else "encoder"
            members[component].append(path)

    components, files = {}, {}
    for component, paths in members.items():
        role = field + "." + component
        base = body_dir if component in ("encoder", "tokenizer") else directory / component
        entries = {p.relative_to(base).as_posix(): sha256(p) for p in paths}
        require(entries, f"componente vazio: {role}")
        index = directory / (component + ".json")
        write_json(index, {"files": entries})
        components[component] = files[role] = sha256(index)
        files.update({role + "/" + name: digest for name, digest in entries.items()})
    desc = directory / "manifest.json"
    write_json(desc, components)
    files[field + ".manifest"] = sha256(desc)
    return components, files, head_classes(model.model_head)


def seal_package(root, training_freeze, arguments, exports, versions):
    shutil.copyfile(training_freeze, root / "training-freeze.json")
    shutil.copyfile(arguments, root / "arguments.json")
    train_digest = sha256(root / "training-freeze.json")
    args_digest = sha256(root / "arguments.json")
    files = {"training_freeze": train_digest, "arguments": args_digest}
    models, class_order = {}, {}
    for field, (components, specialist_files, classes) in exports.items():
        models[field] = components
        class_order[field] = classes
        files.update(specialist_files)
    manifest = {
        "contract_version": VERSION,
        "training_freeze_sha256": train_digest,
        "arguments_sha256": args_digest,
        "model_sha256": {field: files[field + ".manifest"] for field in FIELDS},
        "models": models,
        "class_order": class_order,
        "versions": versions,
        "files": files,
    }
    path = root / "manifest.json"
    write_json(path, manifest)
    return sha256(path)


def read_verified_package(root, trusted_digest):
    require(re.fullmatch(r"[0-9a-f]{64}", trusted_digest) is not None, "SHA-256 confiável ausente ou inválido")
    manifest_path = root / "manifest.json"
    require(not manifest_path.is_symlink(), "manifesto contém link simbólico")
    encoded = manifest_path.read_bytes()
    require(hashlib.sha256(encoded).hexdigest() == trusted_digest, "SHA-256 confiável do pacote diverge")
    manifest = decode(encoded.decode("utf-8"))
    structure("modelManifest", manifest)
    paths = package_paths(root, manifest)
    actual = set()
    for entry in root.rglob("*"):
        require(not entry.is_symlink(), "link simbólico no pacote")
        if entry.is_file():
            actual.add(entry)
        else:
            require(entry.is_dir(), "entrada não regular no pacote")
    require(actual == set(paths.values()) | {manifest_path}, "arquivos locais fora do inventário do pacote")
    require(len(set(paths.values())) == len(paths), "papéis diferentes apontam ao mesmo arquivo")
    validate_manifest("modelManifest", manifest, paths)
    for field in FIELDS:
        require(f"{field}.encoder/model.safetensors" in paths and f"{field}.head/logistic.joblib" in paths and
                f"{field}.tokenizer/tokenizer.json" in paths, "peso Safetensors, cabeça ou tokenizer ausente")
    return manifest, paths


def head_classes(head):
    return head.classes_.tolist()


def score_vector(model, text):
    scores = model.predict_proba(text, as_numpy=True, show_progress_bar=False)
    return {"classes": head_classes(model.model_head), "scores": scores.tolist()}


@dataclass
class LoadedPackage:
    digest: str
    manifest: dict
    models: dict

    @property
    def class_order(self):
        return self.manifest["class_order"]

    @property
    def model_sha256(self):
        return self.manifest["model_sha256"]

    def token_length(self, text, fields):
        return max(length(self.models[field].model_body.tokenizer, text) for field in fields)

    def score(self, field, text):
        return score_vector(self.models[field], text)


def load_package(root, trusted_digest, versions):
    import joblib
    from setfit import SetFitModel
    from sklearn.linear_model import LogisticRegression
    from sklearn.utils.validation import check_is_fitted

    manifest, paths = read_verified_package(root, trusted_digest)
    require(manifest["versions"] == versions, "versões locais divergem das versões do pacote")
    models = {}
    for field in FIELDS:
        role = f"{field}.head/logistic.joblib"
        encoded = paths[role].read_bytes()
        require(hashlib.sha256(encoded).hexdigest() == manifest["files"][role], "hash da cabeça diverge")
        head = joblib.load(io.BytesIO(encoded))
        require(type(head) is LogisticRegression, "tipo inesperado de cabeça local")
        check_is_fitted(head)
        require(head_classes(head) == manifest["class_order"][field], "ordem de classes diverge")
        body = load_body(root / field / "body")
        require(head.n_features_in_ == body.get_embedding_dimension(), "dimensões de cabeça/encoder divergem")
        models[field] = SetFitModel(model_body=body, model_head=head)
    return LoadedPackage(trusted_digest, manifest, models)
