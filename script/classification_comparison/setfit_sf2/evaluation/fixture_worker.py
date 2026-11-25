"""Worker numérico de teste. Não carrega SetFit nem qualquer dado da pesquisa."""
import json
import sys
import time
from pathlib import Path


def main(args):
    mapping, identity, policy_file, mode = args
    templates = json.loads(Path(mapping).read_text())
    ids = json.loads(Path(identity).read_text())
    policy_bytes = Path(policy_file).read_bytes()
    policy = json.loads(policy_bytes)
    import hashlib
    ids["policy_sha256"] = hashlib.sha256(policy_bytes).hexdigest()
    frames = [json.dumps({**d, **ids}) + "\n" for d in templates.values()]
    def premature(stage, index):
        if mode == stage + "-frame":
            return frames[index]
        if mode == stage + "-prefix":
            return frames[index][:19]
        return ""

    ready = {"type": "ready", **({"extra": True} if mode == "bad-ready" else {})}
    sys.stdout.write(json.dumps(ready) + "\n" + premature("after-ready", 0))
    sys.stdout.flush()
    print("Fixture SF2", file=sys.stderr)
    for line in sys.stdin:
        item = json.loads(line)
        if set(item) != {"id", "received", "text", "missing_fields", "catalog", "contract_version"}:
            raise ValueError("fixture recebeu dados fora da projeção")
        if mode == "hang":
            time.sleep(20)
        if mode == "die":
            return 2
        answer = templates[item["id"]]
        assert answer["received"] == item["received"]
        accepted = {}
        for f, field in answer["fields"].items():
            if field["cut"] is not None:
                field["cut"] = policy[f]
            if field["vector"] and field["raw"] != "informacao_insuficiente":
                if max(field["vector"]["scores"]) < policy[f]["tau"]:
                    field.update(decision="review", reason="below_tau")
                elif field["margin"] <= policy[f]["delta"]:
                    field.update(decision="review", reason="low_margin")
                else:
                    accepted[f] = field["raw"]
        if len(accepted) < len(item["missing_fields"]) and answer["outcome"] == "complete":
            answer["outcome"] = "review"
        answer["applied"] = accepted if answer["outcome"] == "complete" else {}
        answer.update(ids)
        if mode == "partial" and answer["outcome"] == "review" and len(item["missing_fields"]) == 2:
            answer["applied"].update(accepted)
        if mode == "invalid-score":
            answer["fields"]["category"]["vector"]["scores"][0] = -1
        if mode == "other-package":
            answer["package_sha256"] = "0"*64
        sys.stdout.write(json.dumps(answer) + "\n" + premature("after-decision", 1))
        sys.stdout.flush()
    if mode == "extra":
        print("{}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
