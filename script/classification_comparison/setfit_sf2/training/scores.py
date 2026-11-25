"""Extrai scores brutos da coleta original de validação, sem novo forward."""

import hashlib
import os
from pathlib import Path
import tempfile

from ..contracts.core import FIELDS, PROTOCOL, VERSION, decode, require
from ..contracts.ipc import project, validate_decision, validate_scores
from .package import json_bytes, read_hashed, read_verified_package

COLLECTION_CUT = {
    "tau": min(PROTOCOL["review_policy"]["tau_grid"]),
    "delta": min(PROTOCOL["review_policy"]["delta_grid"]),
}
COLLECTION_POLICY = {"contract_version": VERSION, **dict.fromkeys(FIELDS, COLLECTION_CUT)}


def extract(records, decisions, policy, class_order, identities, dataset_sha256):
    require(policy == COLLECTION_POLICY, "a coleta de validação exige a política fixa definida para coleta")
    require(len(decisions) == len(records), "cada entrada deve ter exatamente uma decisão original")
    rows = []
    for record, decision in zip(records, decisions, strict=True):
        item = project(record)
        missing = item["missing_fields"]
        validate_decision(item, decision, policy, class_order, identities)
        vectors, errors = {}, {}
        for field in missing:
            result = decision["fields"][field]
            if result["vector"] is None:
                errors[field] = result["reason"]
            else:
                vectors[field] = result["vector"]
        rows.append({"id": item["id"], "heads": vectors, "errors": errors})

    bundle = {
        "contract_version": VERSION, "partition": "validation", "dataset_sha256": dataset_sha256,
        "package_sha256": identities["package_sha256"], "model_sha256": identities["model_sha256"],
        "class_order": class_order, "rows": rows,
    }
    validate_scores(bundle, records, dataset_sha256=dataset_sha256, class_order=class_order,
                    package_sha256=identities["package_sha256"], model_sha256=identities["model_sha256"])
    return bundle


def publish_new(path, bundle):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(json_bytes(bundle))
            stream.close()
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def run(args):
    require(not args.output.exists(), "arquivo de scores já existe")
    manifest, paths = read_verified_package(args.package, args.package_sha256)
    freeze = read_hashed(paths["training_freeze"], manifest["training_freeze_sha256"])
    dataset_sha256 = freeze["files"]["validation"]
    records = read_hashed(args.validation, dataset_sha256, jsonl=True)
    require(len(records) == PROTOCOL["data"]["validation"]["total"], "quantidade de registros diferente da validação")
    decisions = read_hashed(args.predictions, args.predictions_sha256, jsonl=True)
    encoded = args.policy.read_bytes()
    policy = decode(encoded.decode("utf-8"))
    identities = {
        "package_sha256": args.package_sha256,
        "model_sha256": manifest["model_sha256"],
        "policy_sha256": hashlib.sha256(encoded).hexdigest(),
    }
    publish_new(args.output, extract(records, decisions, policy, manifest["class_order"], identities, dataset_sha256))
