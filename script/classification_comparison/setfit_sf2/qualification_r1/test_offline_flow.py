from contextlib import ExitStack
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from ..contracts.core import PROTOCOL, VERSION, decode, text_hash
from ..contracts.test_contracts import fixture
from ..evaluation.test_evaluation import records
from . import execution, release
from .exposure import Guard
from .storage import digest, encoded, read
from .test_runner import dummy_derive, dummy_verify, worker


def fake_custody(folder, rows):
    paths = {role: folder / name for role, name in (
        ("final", "final.jsonl"), ("annotations", "annotations-final.jsonl"),
        ("review_receipt", "review.json"), ("token_lengths", "tokens.json"))}
    annotations = []
    for row in rows:
        ann = fixture("annotation-accepted")
        ann.update(id=row["id"], text_sha256=text_hash(row["text"]))
        for author, labels in zip("AB", ann["annotations"], strict=True):
            labels.update(annotator=author, evidence={f: [row["text"]] for f in row["gold"]}, labels=row["gold"])
        ann["reconciliation"]["labels"] = row["gold"]
        annotations.append(ann)
    paths["final"].write_bytes(b"".join(map(encoded, rows)))
    paths["annotations"].write_bytes(b"".join(map(encoded, annotations)))
    hashes = {k: digest(read(paths[k])) for k in ("final", "annotations")}
    paths["review_receipt"].write_bytes(encoded(dict(reviewer="controle", unresolved_disagreements=0,
                                                      semantic_review_completed=True, limitations="fixture", files=hashes)))
    paths["token_lengths"].write_bytes(encoded(dict(revision=PROTOCOL["training"]["revision"],
                                                    lengths={r["id"]: 5 for r in rows}, files={"final": hashes["final"]})))
    seal = dict(contract_version=VERSION, stage="accepted", files={k: {"path": paths[k].name, "sha256": v}
                for k, v in hashes.items()}, counts=dict(total=120, classifiable=96, expected_review=24, urgent_targets=17),
                review_receipt_sha256=digest(read(paths["review_receipt"])), token_lengths_sha256=digest(read(paths["token_lengths"])))
    inv = folder / "inventory"
    inv.write_bytes(encoded({role: str(path) for role, path in paths.items()}))
    return inv, seal


class EndToEnd(unittest.TestCase):
    def test_execute_and_audit_only_synthetic_custody(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            rows = records("final")
            custody = root / "fake"
            custody.mkdir()
            inventory, final_seal = fake_custody(custody, rows)
            seal_sha = digest(encoded(final_seal))
            dest, rel = root / "run", root / "release"
            argv, context = worker(root, rows)
            config = root / "config"
            config.write_bytes(encoded(dict(release=str(rel), run=str(dest), command=dict(argv=argv, cwd=str(root), environment={}))))
            def inspect(_):
                return {"final_seal_sha256": seal_sha}, context, final_seal
            guard = Guard(root/"shared", root/"legacy-validation", root/"old-release", root/"auth", custody)
            guard.authorizations.mkdir()
            def protected(func):
                def wrapped(path, *args, **kwargs):
                    if isinstance(path, (str, Path)):
                        self.assertFalse(Path(path).is_relative_to(custody), "operação de custódia antes da reserva")
                    return func(path, *args, **kwargs)
                return wrapped
            layout = dict(config=config, release=rel, run=dest)
            with ExitStack() as checks:
                for name in ("open", "stat", "lstat", "scandir", "listdir", "readlink"):
                    checks.enter_context(patch.object(os, name, protected(getattr(os, name))))
                checks.enter_context(patch.object(Path, "open", protected(Path.open)))
                expected = release.freeze(config, rel, inspect, layout=layout)
                checked = release.check(rel, expected, inspect, layout=layout)
                with self.assertRaises(FileNotFoundError):
                    execution.execute(checked, rel, expected, inventory, dest, guard,
                                      load_records=execution.records_from_custody, supervise=execution._supervise,
                                      derive=dummy_derive, verify=dummy_verify)
            (guard.authorizations / (expected + ".json")).write_bytes(encoded(
                dict(action="execute_once", release_sha256=expected, final_seal_sha256=seal_sha,
                     custody=dict(inventory=str(inventory), members=decode(read(inventory))))))
            calls = []
            def confirmed(path, spec, scope):
                guard.verify(rel, expected, seal_sha, dest, path)
                calls.append(path)
                return execution.records_from_custody(path, spec, scope)
            execution_sha = execution.execute(checked, rel, expected, inventory, dest, guard,
                                               load_records=confirmed, supervise=execution._supervise,
                                               derive=dummy_derive, verify=dummy_verify)
            receipt = decode(read(dest / "execution.json", execution_sha))
            self.assertIsNone(receipt["interruption"])
            self.assertEqual(calls, [inventory])
            with patch.object(execution, "_supervise", side_effect=AssertionError("audit iniciou worker")):
                report = execution.audit(checked, rel, expected, inventory, dest, execution_sha, guard,
                                         load_records=confirmed, verify=dummy_verify)
            self.assertEqual((report["status"], len(calls)), ("eligible", 2))
            with self.assertRaises(ValueError):
                execution.execute(checked, rel, expected, inventory, dest, guard, load_records=confirmed,
                                  supervise=execution._supervise, derive=dummy_derive, verify=dummy_verify)
            self.assertEqual(len(calls), 2)

