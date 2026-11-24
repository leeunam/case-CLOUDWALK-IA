# C05-R2 · Task 1 — Instruções candidatas do Qwen

- Base `c00ac5431630c92d30349c13529d5071ad9879b4`
- Branch `feat/r2-instrucoes-qwen`
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-qwen`
- Commit `262d51cc85e377a6a7649d906ae6a8ac8c704c0a`
- Estado final da worktree limpo. O commit acrescenta três arquivos em `script/classification_comparison/adapters/qwen/r2/`.

## Mudanças

- `prompt.txt` orienta a avaliação de evidência de cada campo ausente. Para categoria, pede que o modelo identifique o objeto do pedido. Para prioridade, pede que considere funcionamento, impacto, alternativas e prazo conforme a rubrica. A resposta registra abstenção por campo quando faltam fatos para decidir. O texto instrui a interpretar equivalências e o contexto, preserva os campos recebidos e limita a resposta a um objeto JSON.
- `politica.txt` registra a chamada única por caso elegível, a abstenção por campo, a preservação dos valores recebidos e a aplicação conjunta pelo avaliador.
- `candidate.json` referencia os dois textos com caminhos relativos à raiz, versão 1.1.0 e SHA-256. Identifica Qwen/Feita como candidata real, com IPC 1.1.0 e adaptador 1.2.0. O executor concatena prompt e rubrica no sistema e usa a política como artefato de referência.

## Autoverificação

Revisei o diff dos três arquivos. O prompt contém zero exemplos e orienta a aplicação da rubrica comum sem copiar suas definições. Conferi que as decisões independentes por campo no JSON são compatíveis com a aplicação conjunta pelo avaliador. O manifesto contém somente os quatro campos previstos e mantém os códigos e versões acordados.

| Artefato | SHA-256 |
| --- | --- |
| `candidate.json` | `db8005776018a1c94abaffe4ea0f5d6cdcf5a67836e19931bac747e68e1628f3` |
| `prompt.txt` | `c03848e1f9266ae2aadb5d28d8f82265034c0312067a5e3204aea723437cfa75` |
| `politica.txt` | `6893a119e6dc90aef81e10cc803dba8d66e3cf4c04cc4f3f2d333515c4b2a039` |

Executei o trecho abaixo na worktree. Ele validou o JSON, a identidade, as versões, os caminhos, os dois hashes e a construção de requisições para as três combinações de campos ausentes. Os três casos eram sintéticos e passaram. Reexecutei o trecho a partir deste relatório com os mesmos resultados. O audit hook bloqueia qualquer tentativa de rede no processo de verificação.

```sh
rtk proxy python3 -B - <<'PY'
import hashlib
import json
import sys
from pathlib import Path

def deny_network(event, args):
    if event.startswith("socket."):
        raise AssertionError(f"Tentativa de rede: {event}")

sys.addaudithook(deny_network)
folder = Path("script/classification_comparison/adapters/qwen/r2")
candidate_path = folder / "candidate.json"
candidate = json.loads(candidate_path.read_bytes())
assert set(candidate) == {"contract_version", "identity", "prompt", "policy"}
assert candidate["contract_version"] == "1.1.0"
assert candidate["identity"] == {
    "mode": "real", "provider": "feita", "requested_model": "qwen/qwen3.8-27b",
    "expected_returned_model": "qwen/qwen3.8-27b", "adapter_version": "1.2.0",
    "policy_version": "1.1.0",
}
for key, filename in [("prompt", "prompt.txt"), ("policy", "politica.txt")]:
    reference = candidate[key]
    path = folder / filename
    assert set(reference) == {"path", "version", "sha256"}
    assert reference["path"] == path.as_posix()
    assert reference["version"] == "1.1.0"
    assert reference["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
print("OK: JSON, identidade/versões, caminhos e 2 hashes SHA-256")

sys.path.insert(0, str(folder.parent))
from adapter import request_body

rubric = Path("docs/planejamento/classificacao-comparativa/rubrica-comum.md")
instructions = "\n\n".join(p.read_text(encoding="utf-8") for p in (folder / "prompt.txt", rubric))
catalog = {
    "version": "1.0.0", "category": ["pix", "payouts", "terminal"],
    "priority": ["basic", "intermediate", "advanced", "urgent"],
}
for missing, received in [
    (["category"], {"priority": "urgent"}),
    (["priority"], {"category": "pix"}),
    (["category", "priority"], {}),
]:
    item = {"id": "synthetic-not-sent", "text": "Construção offline", "brand": "jim",
            "catalog": catalog, "missing": missing, "received": received}
    payload = json.loads(request_body(item, received, instructions, 64))
    assert payload["model"] == candidate["identity"]["requested_model"]
    assert payload["response_format"]["type"] == "json_schema"
    shape = payload["response_format"]["json_schema"]
    assert shape["strict"] is True
    assert shape["schema"] == {
        "type": "object", "required": missing, "additionalProperties": False,
        "properties": {field: {"type": "string", "enum": [*catalog[field], "informacao_insuficiente"]}
                       for field in missing},
    }
    system, user = payload["messages"]
    assert system == {"role": "system", "content": instructions}
    assert user["role"] == "user"
    assert json.loads(user["content"]) == {key: value for key, value in item.items() if key != "id"}
    assert all(field not in shape["schema"]["properties"] for field in received)
    print(f"OK: request_body sintético {','.join(missing)}, received={received}, sem transporte")
PY
```

- `rtk proxy sha256sum script/classification_comparison/adapters/qwen/r2/candidate.json script/classification_comparison/adapters/qwen/r2/prompt.txt script/classification_comparison/adapters/qwen/r2/politica.txt` retornou os valores da tabela.
- `rtk proxy git diff --cached --check` e `rtk proxy git diff HEAD^ HEAD --check` passaram. `rtk proxy git diff-tree --no-commit-id --name-status -r HEAD` confirmou apenas os três acréscimos. `rtk proxy git status --short --branch` retornou só a branch.
- A primeira tentativa de commit encontrou o diretório interno do Git em somente leitura. A repetição com a permissão necessária gravou o commit local. O pai confirmado por `rtk proxy git rev-parse HEAD HEAD^` é o commit-base informado.
- Exercício offline. No trecho Python, logo após montar o `payload`, imprima `shape["schema"]` e `json.loads(user["content"])["received"]` depois das respectivas atribuições. Compare o caso em que falta categoria com o caso em que falta prioridade para ver como um valor recebido chega ao modelo sem virar um campo a prever.

## Limites e revisão pendente

O comando `rtk proxy wc -c script/classification_comparison/adapters/qwen/prompt.txt script/classification_comparison/adapters/qwen/r2/prompt.txt` mediu 239 bytes no prompt legado e 1.658 bytes na candidata. O tamanho adicional pode influenciar custo e latência, e a conformidade do esquema admite respostas incorretas ou abstenções excessivas. As verificações estruturais não medem esses efeitos nem garantem a interpretação de relatos ambíguos. Zero chamadas ao fornecedor. Não usei datasets, saídas de modelo, credenciais ou dados financeiros para redigir e validar a candidata. A revisão independente e o registro do congelamento cabem ao integrador.
