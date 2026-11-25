"""Fluxo completo apenas com quotas numéricas, bytes de fixture e diretórios temporários."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ..contracts import test_artifacts as helpers
from ..contracts.core import FIELDS, VERSION, ContractError, read, read_lines, sha256, text_hash
from ..contracts.test_contracts import fixture
from . import workflow
from .runner import save
from .test_evaluation import POLICY, WORKER, records, templates


def numeric_package(root, validation):
    helper = helpers.ArtifactTest()
    training, public, seal = helper._training_case(root)
    finaldir = root/"numeric-final"
    finaldir.mkdir()
    final = records("final")
    annotations = []
    for row in final:
        ann = fixture("annotation-accepted")
        ann.update(id=row["id"], text_sha256=text_hash(row["text"]))
        for j, a in enumerate(ann["annotations"]):
            a.update(annotator="AB"[j], labels=row["gold"], evidence={f: [row["text"]] for f in FIELDS})
        ann["reconciliation"]["labels"] = row["gold"]
        annotations.append(ann)
    private = dict(final=finaldir/"final.jsonl", annotations=finaldir/"annotations-final.jsonl")
    helpers.write_rows(private["final"], final)
    helpers.write_rows(private["annotations"], annotations)
    for role,path in private.items():
        seal["files"][role]["sha256"] = sha256(path)
    receipt = read(public["review_receipt"])
    receipt["files"] = helpers.hashes(private)
    lengths = read(public["token_lengths"])
    lengths.update(files={"final":sha256(private["final"])}, lengths={r["id"]:5 for r in final})
    for name, obj in (("review_receipt", receipt), ("token_lengths", lengths)):
        private[name] = finaldir/name
        save(private[name], obj)
        seal[name+"_sha256"] = sha256(private[name])
    private_inventory = root/"private-inventory.json"
    save(private_inventory, {k: str(v) for k,v in private.items()})
    helpers.write(public["final_seal"], seal)
    training["final_seal_sha256"] = sha256(public["final_seal"])
    model, model_files = helper._model_case(root, training, public)
    manifest = root/"model.json"
    save(manifest,model)
    identities = dict(package_sha256=sha256(manifest), model_sha256=model["model_sha256"])
    save(root/"identity.json", identities)
    save(root/"capture-policy.json", POLICY)
    save(root/"versions.json", model["versions"])
    save(root/"costs.json", dict(training_ms=1, download_ms=0, classifier_api_calls=0))
    for part, rows, policy in (("capture", read_lines(public["validation"]), root/"capture-policy.json"),
                               ("final", final, validation/"policy.json")):
        choices = root/(part+"-choices.json")
        save(choices, templates(rows, weak=True))
        save(root/(part+"-cmd.json"), [sys.executable, str(WORKER), str(choices), str(root/"identity.json"), str(policy), "ok"])
    config = root/"config.json"
    save(config, dict(training_files={k: str(v) for k,v in public.items()},
                      model_files={k: str(v) for k,v in model_files.items()}, model_manifest=str(manifest),
                      adapter=str(WORKER), versions=str(root/"versions.json"), capture_policy=str(root/"capture-policy.json"),
                      capture_command=str(root/"capture-cmd.json"), final_command=str(root/"final-cmd.json"),
                      costs=str(root/"costs.json"), startup_seconds=5))
    return config, private_inventory


class WorkflowTest(unittest.TestCase):
    def test_catalog_bytes_and_loaded_contract_catalog_block_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            validation, release = root/"validation-out", root/"release"
            config, _ = numeric_package(root, validation)
            cfg = read(config)
            copy = root/"frozen-catalog.json"
            raw = Path(cfg["training_files"]["catalog"]).read_bytes()
            copy.write_bytes(raw)
            cfg["training_files"]["catalog"] = str(copy)
            helpers.write(config, cfg)
            local_root = root/"contract-source"
            local = local_root/workflow.PROTOCOL["sources"]["catalog"]["path"]
            local.parent.mkdir(parents=True)
            local.write_bytes(raw)
            with patch.object(workflow, "ROOT", local_root):
                with patch.dict(workflow.CATALOG["category"], {"pix": "Descrição divergente."}), \
                     patch.object(workflow, "supervise", side_effect=AssertionError("worker iniciou")):
                    with self.assertRaisesRegex(ContractError, "catálogo"):
                        workflow.validate(config, root/"blocked")
                self.assertEqual(workflow.validate(config, validation), "eligible")
                capture = read(validation/"capture.json")
                self.assertEqual(capture["catalog"], capture["contract_catalog"])
                self.assertEqual(capture["catalog"], sha256(copy))
                # Mesma semântica JSON e outra sequência de bytes: digest da cópia selada continua idêntico.
                local.write_bytes(raw + b" ")
                with self.assertRaisesRegex(ContractError, "catálogo"):
                    workflow.freeze(config, validation, release)
                self.assertFalse(release.exists())
                local.write_bytes(raw)
                expected = workflow.freeze(config, validation, release)
                with patch.dict(workflow.CATALOG["category"], {"pix": "Outra descrição."}), \
                     patch.object(workflow, "final_files", side_effect=AssertionError("final aberto")):
                    with self.assertRaisesRegex(ContractError, "catálogo"):
                        workflow.execute(config, validation, release, expected, root/"private-inventory.json", root/"dest")
                self.assertFalse((release/"exposure.json").exists())

    def test_numeric_release_exposure_and_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            val, release, dest = (root/k for k in ("validation-out", "release", "final-out"))
            cfg, private = numeric_package(root, val)
            cli = subprocess.run([sys.executable, "-B", "-m", "script.classification_comparison.setfit_sf2.evaluation",
                                  "validate", str(cfg), str(val)], capture_output=True, text=True)
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertEqual(cli.stdout.strip(), "eligible")
            chosen = read(val/"policy.json")
            self.assertEqual(chosen["category"]["tau"], .6)
            self.assertNotEqual(sha256(val/"policy.json"), read_lines(val/"run/predictions.jsonl")[0]["policy_sha256"])
            report = read(val/"report.json")
            self.assertEqual(report["metrics"]["wrong_expected_review"]["numerator"], 0)
            # Rejeitar manipulação anterior ao freeze mesmo quando os dois relatórios parecem plausíveis.
            original = (val/"report.json").read_bytes()
            report["metrics"].pop("raw_urgent")
            helpers.write(val/"report.json",report)
            with self.assertRaises(ContractError):
                workflow.freeze(cfg, val, release)
            (val/"report.json").write_bytes(original)
            expected = workflow.freeze(cfg,val,release)
            with patch.object(workflow, "final_files", side_effect=AssertionError("acesso reservado prematuro")):
                with self.assertRaises(ContractError):
                    workflow.execute(cfg,val,release,"0"*64,private,dest)
                timings = val/"run/timings.jsonl"
                saved = timings.read_bytes()
                timings.write_bytes(saved + b" ")
                with self.assertRaises(ContractError):
                    workflow.execute(cfg,val,release,expected,private,dest)
                timings.write_bytes(saved)
            self.assertFalse((release/"exposure.json").exists())
            with patch.object(workflow, "products", wraps=workflow.products) as reports:
                receipt = workflow.execute(cfg,val,release,expected,private,dest)
                self.assertEqual([call.args[2] for call in reports.call_args_list], [read(cfg)["training_files"]["validation"]])
                self.assertFalse((dest/"report.json").exists())
            self.assertEqual(workflow.audit(cfg,val,release,expected,private,dest,receipt), "eligible")
            final = read(dest/"report.json")
            self.assertEqual(final["metrics"]["raw_urgent"]["numerator"], 17)
            self.assertEqual(final["metrics"]["applied_urgent"]["numerator"], 16)
            self.assertEqual(final["latency_ms"]["n"], 120)
            self.assertEqual(final["predictions_sha256"], sha256(dest/"run/predictions.jsonl"))
            with self.assertRaises(FileExistsError):
                workflow.execute(cfg,val,release,expected,private,root/"another-final")
            with (dest/"run/predictions.jsonl").open("ab") as stream:
                stream.write(b" ")
            with self.assertRaises(ContractError):
                workflow.audit(cfg,val,release,expected,private,dest,receipt)
