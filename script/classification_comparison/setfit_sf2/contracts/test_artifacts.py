"""Cadeia de arquivos de controle; nenhum registro de cliente, modelo ou treino."""
import json
import tempfile
import unittest
from collections import Counter
from copy import deepcopy
from pathlib import Path
from statistics import NormalDist

from .artifacts import validate_manifest, validate_report
from .core import (FIELDS, LABELS, PLAN, PROTOCOL, ROOT, SCHEMA_PATH, VERSION, ContractError,
                   read, read_lines, sha256, text_hash)
from .test_contracts import fixture, quota_rows


def write(path, obj):
    path.write_text(json.dumps(obj) + "\n", encoding="utf-8")


def write_rows(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def hashes(paths):
    return {k: sha256(v) for k, v in paths.items()}


def prop(n, d):
    interval = None
    if d:
        z = NormalDist().inv_cdf(0.975)
        p = n / d
        center = (p + z*z/(2*d)) / (1 + z*z/d)
        radius = z * ((p*(1-p) + z*z/(4*d))/d)**.5 / (1 + z*z/d)
        interval = [max(0, center-radius), min(1, center+radius)]
    return {"numerator": n, "denominator": d, "wilson95": interval}


def sample_report(part):
    q = PROTOCOL["data"][part]
    total, clear, urgent = q["total"], q["classifiable_cases"], q["urgent_target_cases"]
    metrics = dict(preservation=prop(total - q["per_mask"], total - q["per_mask"]),
                   control_calls=0, partial_applications=0, wrong_expected_review=prop(0, total-clear),
                   nonurgent_on_urgent=0, automatic_coverage=prop(clear, clear), correct_coverage=prop(clear, clear),
                   raw_urgent=prop(urgent, urgent), applied_urgent=prop(urgent-1, urgent),
                   review_by_case=prop(total-clear, total), by_class={}, confusion={}, applied_accuracy={}, review_by_field={})
    for f in FIELDS:
        support = Counter(row["gold"][f] for row in quota_rows(part) if f in row["missing_fields"])
        metrics["by_class"][f] = {k: dict(precision=prop(n,n), recall=prop(n,n), f1=1, support=n) for k,n in support.items()}
        metrics["confusion"][f] = {k: {v: n if v == k else 0 for v in [*LABELS[f], "error"]} for k,n in support.items()}
        metrics["applied_accuracy"][f] = prop(q["classifiable_per_mask"]*2, q["classifiable_per_mask"]*2)
        metrics["review_by_field"][f] = prop(support["informacao_insuficiente"], q["target_fields"][f])
    return dict(contract_version=VERSION, partition=part, status="eligible", counts=dict(planned=total, observed=total),
                policy_sha256="0"*64, score_package_sha256="1"*64, predictions_sha256="2"*64, unexecuted_ids=[],
                metrics=metrics, latency_ms=dict(n=total, p50=1, p95=10, maximum=10), reason="controle",
                resources=dict(startup_ms=1, download_ms=0, training_ms=2, peak_ram_bytes=3, peak_cpu_percent=4,
                               classifier_api_calls=0))


class ArtifactTest(unittest.TestCase):
    def test_report_required_metrics_and_failures(self):
        for partition in ("validation", "final"):
            report = sample_report(partition)
            validate_report(report)
            for change in (lambda r: r["metrics"].pop("raw_urgent"),
                           lambda r: r["metrics"]["raw_urgent"].update(denominator=0),
                           lambda r: r["metrics"]["raw_urgent"].update(numerator=0),
                           lambda r: r["metrics"]["automatic_coverage"].update(numerator=0),
                           lambda r: r["metrics"]["applied_accuracy"]["priority"].update(numerator=0),
                           lambda r: r["metrics"].update(nonurgent_on_urgent=1),
                           lambda r: r["metrics"].update(partial_applications=1),
                           lambda r: r["metrics"].update(control_calls=1),
                           lambda r: r.update(metrics=None),
                           lambda r: r.update(predictions_sha256=None)):
                bad = deepcopy(report)
                change(bad)
                with self.assertRaises(ContractError):
                    validate_report(bad)
            report["latency_ms"].update(p95=3001, maximum=3001)
            if partition == "final":
                with self.assertRaises(ContractError):
                    validate_report(report)
                report["status"] = "failed"
            validate_report(report)
            report.update(status="inconclusive", metrics=None, unexecuted_ids=["controle"])
            report["counts"]["observed"] -= 1
            report["latency_ms"]["n"] -= 1
            validate_report(report)

    def _public_files(self, folder, stage):
        # Textos são somente identificadores numéricos de controle; nenhuma narrativa de pesquisa.
        annotations, paths, lengths = [], {}, {}
        for part in ("train", "validation"):
            rows = []
            for i, counter in enumerate(quota_rows(part)):
                key = part + "-" + str(i)
                row = dict(id=key, family_id=key, partition=part, text=key, gold=counter["gold"], author="A")
                if part != "train":
                    mask = counter["missing_fields"]
                    row.update(missing_fields=mask, received={k: v for k,v in row["gold"].items() if k not in mask})
                rows.append(row)
                ann = fixture("annotation-accepted" if stage == "accepted" else "annotation-draft")
                ann.update(id=key, text_sha256=text_hash(key))
                for j, a in enumerate(ann["annotations"]):
                    a.update(annotator="AB"[j], evidence={f: [key] for f in FIELDS}, labels=row["gold"])
                if ann["reconciliation"]:
                    ann["reconciliation"]["labels"] = row["gold"]
                annotations.append(ann)
                lengths[key] = 5
            paths[part] = folder / (part + ".jsonl")
            write_rows(paths[part], rows)
        paths["annotations"] = folder / "annotations-public.jsonl"
        write_rows(paths["annotations"], annotations)
        files = {k: {"path": p.name, "sha256": sha256(p)} for k,p in paths.items()}
        m = dict(contract_version=VERSION, stage=stage, files=files, counts=dict(train=150, validation=90),
                 review_receipt_sha256=None, token_lengths_sha256=None, limitations="Controle numérico.")
        if stage == "accepted":
            for role, doc in (("review_receipt", dict(reviewer="controle", unresolved_disagreements=0,
                                  semantic_review_completed=True, limitations="Fixture",
                                  files={k:v["sha256"] for k,v in files.items()})),
                              ("token_lengths", dict(revision=PROTOCOL["training"]["revision"], lengths=lengths,
                                   files={k:files[k]["sha256"] for k in ("train", "validation")}))):
                paths[role] = folder / (role + ".json")
                write(paths[role], doc)
                m[role + "_sha256"] = sha256(paths[role])
        return m, paths

    def test_public_manifest_with_real_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for stage in ("draft", "accepted"):
                manifest, paths = self._public_files(folder, stage)
                result = validate_manifest("publicManifest", manifest, paths)
                self.assertEqual(result["accepted"], stage == "accepted")
            with self.assertRaises(ContractError):
                validate_manifest("publicManifest", manifest, {k:v for k,v in paths.items() if k != "review_receipt"})
            receipt = read(paths["token_lengths"])
            for mutate in (lambda doc: doc["files"].update(train="b"*64),
                           lambda doc: doc["lengths"].pop("train-0"),
                           lambda doc: doc["lengths"].update({"train-0": 129})):
                bad = deepcopy(receipt)
                mutate(bad)
                write(paths["token_lengths"], bad)
                manifest["token_lengths_sha256"] = sha256(paths["token_lengths"])
                with self.assertRaises(ContractError):
                    validate_manifest("publicManifest", manifest, paths)
            paths["train"].write_bytes(b"alterado")
            with self.assertRaisesRegex(ContractError, "SHA-256"):
                validate_manifest("publicManifest", manifest, paths)

    def _file(self, folder, role, obj):
        path = folder / (role + ".json")
        write(path, obj)
        return path

    def _training_case(self, folder):
        public, data_paths = self._public_files(folder, "accepted")
        paths = dict(data_paths)
        paths.update({k: ROOT / v["path"] for k,v in PROTOCOL["sources"].items()})
        paths.update(protocol=PLAN/"protocolo.json", contracts=SCHEMA_PATH, training_code=self._file(folder, "code","fixture"),
                     arguments=self._file(folder, "arguments",PROTOCOL["training"]), public_manifest=self._file(folder, "public",public))
        seal = dict(contract_version=VERSION, stage="accepted",
                    files={k:dict(path=name,sha256="c"*64) for k,name in
                           (("final","final.jsonl"),("annotations","annotations-final.jsonl"))},
                    counts=dict(total=120,classifiable=96,expected_review=24,urgent_targets=17),
                    review_receipt_sha256="d"*64,token_lengths_sha256="e"*64)
        training = dict(contract_version=VERSION,files=hashes(paths))
        paths["final_seal"] = self._file(folder, "seal",seal)
        training["final_seal_sha256"] = sha256(paths["final_seal"])
        return training, paths, seal

    def test_training_freeze_requires_accepted_annotations_and_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            training, paths, _ = self._training_case(folder)
            validate_manifest("trainingFreeze", training, paths)
            for role in ("token_lengths", "review_receipt"):
                with self.subTest(role=role), self.assertRaises(ContractError):
                    validate_manifest("trainingFreeze", training, {k: v for k, v in paths.items() if k != role})
            # Recalcula os hashes, inclusive o do recibo, para uma versão só com A.
            rows = read_lines(paths["annotations"])
            for entry in rows:
                entry["annotations"] = entry["annotations"][:1]
                entry["reconciliation"] = None
            write_rows(paths["annotations"], rows)
            digest = sha256(paths["annotations"])
            public = read(paths["public_manifest"])
            receipt = read(paths["review_receipt"])
            public["files"]["annotations"]["sha256"] = receipt["files"]["annotations"] = digest
            write(paths["review_receipt"], receipt)
            public["review_receipt_sha256"] = sha256(paths["review_receipt"])
            write(paths["public_manifest"], public)
            for role in ("public_manifest", "review_receipt", "annotations"):
                training["files"][role] = sha256(paths[role])
            with self.assertRaisesRegex(ContractError, "anotação autoral"):
                validate_manifest("trainingFreeze", training, paths)

    def test_training_freeze_rejects_changed_seed_with_correct_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            training, paths, _ = self._training_case(Path(tmp))
            write(paths["arguments"], {**PROTOCOL["training"], "seed": 7})
            training["files"]["arguments"] = sha256(paths["arguments"])
            with self.assertRaisesRegex(ContractError, "receita"):
                validate_manifest("trainingFreeze", training, paths)

    def test_report_preservation_counts_all_provided_fields(self):
        for partition in ("validation", "final"):
            for status in ("eligible", "failed"):
                report = sample_report(partition)
                report.update(status=status)
                report["metrics"]["preservation"] = prop(1, 1)
                if status == "failed":
                    report["metrics"]["partial_applications"] = 1
                with self.subTest(partition=partition, status=status), self.assertRaisesRegex(ContractError, "preservation"):
                    validate_report(report)

    def _model_case(self, folder, training, paths):
        model_paths = dict(training_freeze=self._file(folder, "training", training), arguments=paths["arguments"])
        models, orders = {}, fixture("both")["class_order"]
        for field in FIELDS:
            components = {}
            for component in ("base_encoder", "encoder", "head", "tokenizer", "training_evidence"):
                role = field + "." + component
                members = ["tokenizer.json", "vocab.txt"] if component == "tokenizer" else ["single.bin"]
                index = {}
                for name in members:
                    payload = self._file(folder, role + "-" + name, "controle de bytes")
                    model_paths[role + "/" + name] = payload
                    index[name] = sha256(payload)
                model_paths[role] = self._file(folder, role, {"files": index})
                components[component] = sha256(model_paths[role])
            model_paths[field + ".manifest"] = self._file(folder, field + ".manifest", components)
            models[field] = components
        model = dict(contract_version=VERSION, training_freeze_sha256=sha256(model_paths["training_freeze"]),
                     model_sha256={f: sha256(model_paths[f + ".manifest"]) for f in FIELDS}, class_order=orders,
                     versions={"python": "fixture"}, arguments_sha256=sha256(paths["arguments"]),
                     models=models, files=hashes(model_paths))
        return model, model_paths

    def test_model_requires_component_members_and_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            training, paths, _ = self._training_case(folder)
            model, model_paths = self._model_case(folder, training, paths)
            validate_manifest("modelManifest", model, model_paths)
            role = "category.tokenizer/tokenizer.json"
            without_member = deepcopy(model)
            del without_member["files"][role]
            with self.assertRaisesRegex(ContractError, "membro"):
                validate_manifest("modelManifest", without_member, {k:v for k,v in model_paths.items() if k != role})
            write(model_paths[role], "bytes divergentes")
            with self.assertRaisesRegex(ContractError, "SHA-256"):
                validate_manifest("modelManifest", model, model_paths)
            model["files"][role] = sha256(model_paths[role])
            with self.assertRaisesRegex(ContractError, "membro"):
                validate_manifest("modelManifest", model, model_paths)

    def test_freezes_and_model_with_fixture_bytes_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            def file(role, obj):
                return self._file(folder, role, obj)
            training, paths, seal = self._training_case(folder)
            validate_manifest("trainingFreeze", training, paths)
            model, model_paths = self._model_case(folder, training, paths)
            validate_manifest("modelManifest", model, model_paths)
            orders, model_hashes = model["class_order"], model["model_sha256"]
            records = read_lines(paths["validation"])
            fx = {k:paths[k] for k in ("train","validation","final_seal")}
            fx.update(training_freeze=model_paths["training_freeze"],model_manifest=file("model",model),
                      policy=file("policy",fixture("both")["policy"]),adapter=file("adapter","fixture"),
                      command=file("command","fixture"),versions=file("versions",model["versions"]))
            scores = dict(contract_version=VERSION, partition="validation",dataset_sha256=sha256(fx["validation"]),
                          package_sha256=sha256(fx["model_manifest"]),model_sha256=model_hashes,class_order=orders,
                          rows=[dict(id=r["id"],errors={},heads={
                              f:dict(classes=orders[f],scores=[int(x == r["gold"][f]) for x in orders[f]])
                              for f in r["missing_fields"]}) for r in records])
            fx["validation_scores"] = file("scores",scores)
            fx["validation_predictions"] = folder / "decisions.jsonl"
            decisions = []
            templates = {name: fixture(name)["decision"] for name in ("category-only", "priority-only", "both")}
            for record, scored in zip(records, scores["rows"], strict=True):
                missing = record["missing_fields"]
                decision = deepcopy(templates["both" if len(missing) == 2 else missing[0] + "-only"])
                decision.update(id=record["id"], received=record["received"], package_sha256=scores["package_sha256"],
                                policy_sha256=sha256(fx["policy"]), model_sha256=model_hashes)
                applied = {}
                for field, vector in scored["heads"].items():
                    raw = record["gold"][field]
                    result = decision["fields"][field]
                    result.update(raw=raw, vector=vector)
                    if raw == "informacao_insuficiente":
                        result.update(decision="review", reason="raw_review")
                    else:
                        applied[field] = raw
                complete = set(applied) == set(missing)
                decision.update(outcome="complete" if complete else "review", applied=applied if complete else {})
                decisions.append(decision)
            write_rows(fx["validation_predictions"], decisions)
            report = sample_report("validation")
            report.update(predictions_sha256=sha256(fx["validation_predictions"]), policy_sha256=sha256(fx["policy"]),
                          score_package_sha256=sha256(fx["validation_scores"]))
            fx["validation_report"] = file("report",report)
            freeze = dict(contract_version=VERSION, files={**hashes(fx), "final":seal["files"]["final"]["sha256"]},
                          model_sha256=model_hashes,class_order=orders,validation_eligible=True)
            validate_manifest("freeze",freeze,fx)  # sem caminho do final reservado
            missing = {k: v for k, v in fx.items() if k != "validation_predictions"}
            with self.assertRaisesRegex(ContractError, "inventário"):
                validate_manifest("freeze", freeze, missing)
            data = fx["validation_predictions"].read_bytes()
            fx["validation_predictions"].write_bytes(data + b" ")
            with self.assertRaisesRegex(ContractError, "SHA-256"):
                validate_manifest("freeze", freeze, fx)
            wrong_predictions = deepcopy(freeze)
            wrong_predictions["files"]["validation_predictions"] = sha256(fx["validation_predictions"])
            with self.assertRaisesRegex(ContractError, "previsões"):
                validate_manifest("freeze", wrong_predictions, fx)
            fx["validation_predictions"].write_bytes(b"")
            absent_report = {**report, "predictions_sha256": sha256(fx["validation_predictions"])}
            absent_paths = {**fx, "validation_report": file("empty-report", absent_report)}
            absent_freeze = {**freeze, "files": {**freeze["files"], **hashes(absent_paths)}}
            with self.assertRaisesRegex(ContractError, "inventário das decisões"):
                validate_manifest("freeze", absent_freeze, absent_paths)
            fx["validation_predictions"].write_bytes(data)
            bad_scores = deepcopy(scores)
            first = bad_scores["rows"][0]
            first["heads"].pop("category")
            first["errors"]["category"] = "timeout"
            bad_paths = {**fx, "validation_scores": file("bad_scores",bad_scores)}
            bad_report = {**report, "score_package_sha256": sha256(bad_paths["validation_scores"])}
            bad_paths["validation_report"] = file("bad_report",bad_report)
            bad_freeze = {**freeze, "files": {**freeze["files"], **hashes(bad_paths)}}
            with self.assertRaisesRegex(ContractError, "matriz bruta"):
                validate_manifest("freeze",bad_freeze,bad_paths)
            for key in ("policy","final","validation_scores"):
                bad = deepcopy(freeze)
                bad["files"][key] = "9"*64
                with self.assertRaises(ContractError):
                    validate_manifest("freeze",bad,fx)
