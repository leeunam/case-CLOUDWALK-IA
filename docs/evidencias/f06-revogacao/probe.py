"""Ensaio F06/F07. Recebe apenas as duas senhas sintéticas no stdin."""
import json
import sys
import uuid
from pathlib import Path

from http_client import Browser, Cable
from observe import Blocked, Failed, verify


def run(fixture, credentials, evidence):
    bia, supervisor = Browser(), Browser()
    for name, browser, role in (("bia", bia, "analyst"), ("supervisor", supervisor, "supervisor")):
        user = browser.login(name, credentials)["user"]
        verify((user["role"], user["id"]) == (role, fixture[name + "_id"]), "Identidade diferente da fixture")

    case_id = fixture["case_id"]
    brand_id = fixture["brand_id"]
    queue_id = fixture["queue_id"]
    grant, retained = fixture["team_bia"], fixture["team_retained"]
    path = f"/api/v1/cases/{case_id}"
    queue_path = f"/api/v1/brands/{brand_id}/queues/{queue_id}"
    case_list = f"/api/v1/cases?queue_id={queue_id}"

    def classify(category, label):
        before = supervisor.call(path)
        reason = f"{fixture['marker']} {label}"
        response = supervisor.call(path + "/classification", payload={
            "expected_version": before["version"], "category": category, "priority": "basic", "reason": reason,
        }, headers=supervisor.write_headers(str(uuid.uuid4())))
        saved = supervisor.call(path)
        verify(response["id"] == case_id and saved["version"] == response["version"] == before["version"] + 1
               and saved["classification"]["category"] == category and saved["queue_id"] == queue_id,
               "A leitura REST não confirmou a versão e categoria gravadas")
        audit = [item for item in supervisor.call(path + "/audit")["items"]
                 if item["case_id"] == case_id and item["type"] == "case.classification.corrected"
                 and item["reason"] == reason and item["actor"]["id"] == fixture["supervisor_id"]]
        verify(len(audit) == 1, "A escrita de controle não tem auditoria única")
        return {"version": saved["version"], "category": category, "audit_id": audit[0]["id"]}

    before = bia.call(path)
    verify(before["id"] == case_id and before["queue_id"] == queue_id and
           [item["id"] for item in bia.call(case_list)["items"]] == [case_id],
           "Faltou a leitura inicial do atendimento pela Bia")
    bia.call(path + "/messages")
    evidence["rest_before"] = {"case": 200, "messages": 200, "filtered_list": [case_id]}

    with Cable(bia.cookie()) as former, Cable(supervisor.cookie()) as control:
        former.welcome()
        control.welcome()
        former_id = former.subscribe(case_id, "staff", allowed=True)
        control_id = control.subscribe(case_id, "staff", allowed=True)
        warm = evidence["before_revocation"] = classify("payouts", "controle inicial")
        warm["bia_notice"] = former.update(former_id, case_id)
        warm["supervisor_notice"] = control.update(control_id, case_id)

        changed = supervisor.call(queue_path, method="PUT", payload={
            "expected_version": fixture["queue_version"], "active": True, "name": fixture["queue_name"],
            "team_ids": [retained],
        }, headers=supervisor.write_headers())
        verify(changed["id"] == queue_id and changed["brand_id"] == brand_id and changed["active"] and
               changed["team_ids"] == [retained] and changed["version"] == fixture["queue_version"] + 1,
               "PUT não confirmou remoção da equipe original")
        audit_path = f"/api/v1/brands/{brand_id}/configuration-audit?resource_type=queue&resource_id={queue_id}"
        matches = [item for item in supervisor.call(audit_path)["items"] if item["version"] == changed["version"]
                   and item["actor"]["id"] == fixture["supervisor_id"] and item["resource_id"] == queue_id]
        verify(len(matches) == 1 and set(matches[0]["before"]["team_ids"]) == {grant, retained}
               and matches[0]["after"]["team_ids"] == [retained], "Auditoria de revogação divergente")
        evidence["revoke_queue"] = {"http": 200, "version": changed["version"], "audit_id": matches[0]["id"],
                                    "before": matches[0]["before"]["team_ids"], "after": changed["team_ids"]}

        rejected = {}
        for key, route in (("case", path), ("messages", path + "/messages")):
            body = bia.call(route, expected=404)
            rejected[key] = {"status": 404, "code": body["error"]["code"]}
        verify(not bia.call(case_list)["items"], "Atendimento revogado ainda está na lista filtrada")
        verify(bia.session()["user"]["id"] == fixture["bia_id"], "A sessão da analista não está mais autenticada")
        evidence["rest_after"] = {**rejected, "filtered_list": [], "session_still_authenticated": True}
        with Cable(bia.cookie()) as new:
            new.welcome()
            new.subscribe(case_id, "staff", allowed=False)
        evidence["new_subscription"] = "rejected"

        observations = evidence["after_revocation_controls"] = []
        for index, category in enumerate(("pix", "payouts", "pix"), 1):
            item = classify(category, f"controle posterior {index}")
            item["supervisor_notice"] = control.update(control_id, case_id)
            observations.append(item)
        evidence["previous_subscription"] = former.revoked_stream_observation(former_id, seconds=6)


def main():
    fixture = json.loads(Path(sys.argv[1]).read_text())
    report = {"task": "F06/F07 revogação de equipe da fila", "fixture": fixture, "evidence": {}}
    try:
        run(fixture, json.load(sys.stdin), report["evidence"])
    except Failed as error:
        report.update(status="reprovado", reason=str(error))
        status = 1
    except Blocked as error:
        report.update(status="bloqueado", reason=str(error))
        status = 2
    except Exception as error:
        report.update(status="bloqueado", reason=f"Erro no ensaio: {type(error).__name__}")
        status = 2
    else:
        report.update(status="aprovado")
        status = 0
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
