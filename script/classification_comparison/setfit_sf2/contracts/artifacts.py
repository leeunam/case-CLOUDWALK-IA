"""Integridade das referências e condições mínimas para publicar um resultado."""
from collections import Counter
from pathlib import Path

from .data import validate_dataset
from .ipc import validate_scores, validate_vector
from .core import (FIELDS, LABELS, PLAN, PROTOCOL, SCHEMA_PATH, decimal, read, read_lines, require,
                   sha256, structure, verify_files)


def _data_manifest(manifest, paths):
    expected = {role: file["sha256"] for role, file in manifest["files"].items()}
    require(all(role in paths and Path(paths[role]).name == file["path"]
                for role, file in manifest["files"].items()), "nome de arquivo incompatível com o manifesto")
    data_hashes = dict(expected)
    receipt_roles = ("review_receipt", "token_lengths")
    for role in receipt_roles:
        digest = manifest[role + "_sha256"]
        if manifest["stage"] == "accepted":
            require(digest is not None, "aceite sem recibo: " + role)
        if digest is not None:
            expected[role] = digest
    verify_files(expected, paths)
    partitions = {role: read_lines(paths[role]) for role in manifest["files"] if role != "annotations"}
    result = validate_dataset(partitions, read_lines(paths["annotations"]), manifest["stage"])
    if "review_receipt" in paths:
        receipt = read(paths["review_receipt"])
        structure("reviewReceipt", receipt)
        require(receipt["files"] == data_hashes, "recibo de revisão de outro conjunto")
    if "token_lengths" in paths:
        lengths = read(paths["token_lengths"])
        structure("tokenLengths", lengths)
        require(lengths["files"] == {k: data_hashes[k] for k in partitions},
                "tokenização de outra versão de dados")
        require(set(lengths["lengths"]) == {r["id"] for rows in partitions.values() for r in rows},
                "inventário de textos tokenizados divergente")
    if manifest["stage"] == "draft":
        result["pending"] = ["independent_annotation", "reconciliation", "accepted_manifest"]
        result["pending"].extend(role for role in receipt_roles if role not in paths)
    return result


def _training_freeze(manifest, paths):
    expected = {**manifest["files"], "final_seal": manifest["final_seal_sha256"]}
    verify_files(expected, paths)
    for role, src in PROTOCOL["sources"].items():
        require(expected[role] == src["sha256"], "fonte aprovada divergente")
    require(expected["protocol"] == sha256(PLAN / "protocolo.json") and
            expected["contracts"] == sha256(SCHEMA_PATH), "protocolo ou contrato divergente")
    structure("finalSeal", read(paths["final_seal"]))
    public = read(paths["public_manifest"])
    structure("publicManifest", public)
    require(public["stage"] == "accepted" and public["review_receipt_sha256"] and public["token_lengths_sha256"] and
            all(public["files"][k]["sha256"] == expected[k] for k in ("train", "validation", "annotations")),
            "dados públicos não vinculados a manifesto aceito")


def _model_manifest(manifest, paths):
    # Os papéis de cada arquivo vêm do chamador; não resolvemos caminhos lidos do pacote.
    expected = dict(manifest["files"])
    bindings = {"training_freeze": manifest["training_freeze_sha256"], "arguments": manifest["arguments_sha256"]}
    for field in FIELDS:
        bindings[field + ".manifest"] = manifest["model_sha256"][field]
        bindings.update({field + "." + role: digest for role, digest in manifest["models"][field].items()})
    require(all(expected.get(role) == digest for role, digest in bindings.items()),
            "manifesto de pesos não vincula arquivos obrigatórios")
    verify_files(expected, paths)
    for field in FIELDS:
        require(read(paths[field + ".manifest"]) == manifest["models"][field], "descritor de modelo divergente")
    training = read(paths["training_freeze"])
    structure("trainingFreeze", training)
    require(training["files"]["arguments"] == expected["arguments"], "argumentos não congelados")


def _freeze(manifest, paths):
    # O final ainda está fechado. Seu digest é conferido contra o selo público, sem abrir o arquivo.
    verify_files({k: v for k, v in manifest["files"].items() if k != "final"}, paths)
    policy, report = read(paths["policy"]), read(paths["validation_report"])
    model, seal = read(paths["model_manifest"]), read(paths["final_seal"])
    training, scores = read(paths["training_freeze"]), read(paths["validation_scores"])
    for schema, value in (("policy", policy), ("modelManifest", model), ("finalSeal", seal),
                          ("trainingFreeze", training), ("scorePackage", scores)):
        structure(schema, value)
    validate_report(report)
    require(report["partition"] == "validation" and report["status"] == "eligible", "validação inelegível")
    files = manifest["files"]
    require(model["training_freeze_sha256"] == files["training_freeze"] and
            training["final_seal_sha256"] == files["final_seal"] and seal["files"]["final"]["sha256"] == files["final"] and
            all(files[k] == training["files"][k] for k in ("train", "validation")), "dados ou pacote divergentes")
    require(scores["partition"] == "validation" and scores["dataset_sha256"] == files["validation"] and
            scores["package_sha256"] == files["model_manifest"] and
            manifest["class_order"] == model["class_order"] == scores["class_order"] and
            manifest["model_sha256"] == model["model_sha256"] == scores["model_sha256"], "classes/pesos/scores incompatíveis")
    records = read_lines(paths["validation"])
    validate_scores(scores, records, dataset_sha256=files["validation"],
                    package_sha256=files["model_manifest"], model_sha256=model["model_sha256"],
                    class_order=model["class_order"])
    expected = {r["id"]: r["gold"] for r in records}
    raw_counts = {f: Counter() for f in FIELDS}
    for row in scores["rows"]:
        for f in row["heads"].keys() | row["errors"].keys():
            label = (validate_vector(row["heads"][f], model["class_order"][f])[0]
                     if f in row["heads"] else "error")
            raw_counts[f][expected[row["id"]][f], label] += 1
    for f in FIELDS:
        matrix = report["metrics"]["confusion"][f]
        require(all(n == raw_counts[f][gold, raw] for gold, columns in matrix.items() for raw, n in columns.items()),
                "matriz bruta não corresponde aos scores de validação")
    require(report["policy_sha256"] == files["policy"] and report["score_package_sha256"] == files["validation_scores"],
            "cortes ou scores diferentes da seleção aprovada")


def validate_manifest(kind, manifest, paths):
    checks = {"publicManifest": _data_manifest, "finalSeal": _data_manifest, "trainingFreeze": _training_freeze,
              "modelManifest": _model_manifest, "freeze": _freeze}
    require(kind in checks, "tipo de manifesto desconhecido")
    structure(kind, manifest)
    return checks[kind](manifest, paths)


def _ratios(node):
    if isinstance(node, dict):
        if {"numerator", "denominator", "wilson95"} <= node.keys():
            yield node
        else:
            for value in node.values():
                yield from _ratios(value)


def _meets(ratio, limit):
    return ratio["denominator"] > 0 and ratio["numerator"] >= decimal(limit) * ratio["denominator"]


def validate_report(report):
    structure("report", report)
    part = report["partition"]
    quota = PROTOCOL["data"][part]
    observed = report["counts"]["observed"]
    total = quota["total"]
    require(report["counts"]["planned"] == total and total - observed == len(report["unexecuted_ids"]),
            "contagem de observações inconsistente")
    latency = report["latency_ms"]
    if latency:
        require(0 < latency["n"] <= observed and latency["p50"] <= latency["p95"] <= latency["maximum"],
                "resumo de durações inválido")
    metrics = report["metrics"]
    if report["status"] != "inconclusive":
        require(observed == total and metrics and latency and latency["n"] == total and
                report["predictions_sha256"] and all(v is not None for v in report["resources"].values()),
                "relatório conclusivo incompleto")
    if metrics is None:
        return
    for r in _ratios(metrics):
        require(r["numerator"] <= r["denominator"], "numerador maior que denominador")
        interval = r["wilson95"]
        require((interval is None) == (r["denominator"] == 0), "intervalo de Wilson ausente ou indevido")
        if interval:
            require(interval[0] <= interval[1], "limites de Wilson invertidos")
    if report["status"] == "inconclusive":
        return
    for name, denominator in (("wrong_expected_review", quota["expected_review_cases"]),
                              ("raw_urgent", quota["urgent_target_cases"]), ("applied_urgent", quota["urgent_target_cases"]),
                              ("automatic_coverage", quota["classifiable_cases"]),
                              ("correct_coverage", quota["classifiable_cases"]), ("review_by_case", total)):
        require(metrics[name]["denominator"] == denominator, "denominador incorreto: " + name)
    for field in FIELDS:
        require(metrics["review_by_field"][field]["denominator"] == quota["target_fields"][field] and
                metrics["applied_accuracy"][field]["denominator"] <= quota["target_fields"][field],
                "suporte de alvos divergente")
        classes = metrics["by_class"][field]
        require(sum(v["support"] for v in classes.values()) == quota["target_fields"][field],
                "suporte por classe divergente")
        matrix = metrics["confusion"][field]
        for label, stats in classes.items():
            require(stats["support"] == sum(metrics["confusion"][field][label].values()) == stats["recall"]["denominator"],
                    "matriz de confusão incompatível com suporte/recall")
            tp = matrix[label][label]
            predicted = sum(matrix[k][label] for k in LABELS[field])
            require(tp == stats["recall"]["numerator"] == stats["precision"]["numerator"] and
                    predicted == stats["precision"]["denominator"], "precisão/recall incompatível com matriz bruta")
    urgent_row = metrics["confusion"]["priority"]["urgent"]
    require(sum(urgent_row.values()) == metrics["raw_urgent"]["denominator"] and
            urgent_row["urgent"] == metrics["raw_urgent"]["numerator"], "urgentes brutos divergentes da matriz")
    require(metrics["correct_coverage"]["numerator"] <= metrics["automatic_coverage"]["numerator"] and
            metrics["applied_urgent"]["numerator"] <= metrics["raw_urgent"]["numerator"],
            "contagens aplicadas incompatíveis")
    gates = PROTOCOL["gates"]
    eligible = all((
        _meets(metrics["preservation"], gates["channel_field_preservation_ratio"]),
        metrics["control_calls"] == 0, metrics["partial_applications"] == 0,
        metrics["wrong_expected_review"]["numerator"] == 0, metrics["nonurgent_on_urgent"] == 0,
        all(_meets(r, gates["applied_accuracy_per_field_min"]) for r in metrics["applied_accuracy"].values()),
        _meets(metrics["automatic_coverage"], gates["automatic_coverage_on_fully_classifiable_cases_min"]),
        _meets(metrics["raw_urgent"], gates["raw_urgent_recognition_min"]),
        part != "final" or latency["p95"] <= gates["final_observed_total_latency_p95_ms_max"]))
    require((report["status"] == "eligible") == eligible, "declaração de elegibilidade contradiz os gates")
