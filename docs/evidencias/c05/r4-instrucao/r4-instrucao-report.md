# Task3-D1 · Instrução Luna 1.2.0

Branch `feat/luna-instrucao-r4`, worktree `.worktrees/r4-luna-instrucao`. Base `3e59f4ad80536b5586e91c89a2ea157bebbcb442`, commit `2f6698495577ec9064f7020d2e0f0825bcc3a74f`. A worktree está limpa. O commit acrescenta exclusivamente o prompt, o manifesto R4 e a nota em `docs/evidencias/c05/r4-instrucao/nota.md`.

O texto pede que a Luna determine o que o cliente quer fazer, entender ou corrigir. Distingue uma operação identificada cujo resultado é desconhecido de uma possibilidade apenas cogitada e de uma operação descartada. Se duas categorias explicam a demanda e diferenciá-las exige presumir um fato, o modelo recebe instrução para se abster naquele campo. Isso permite consultas claras em linguagem natural e preserva o tratamento de falhas de operações identificadas. O prompt usa zero exemplos. A prioridade, a interpretação geral dos campos e a saída JSON foram preservadas byte a byte no arquivo a partir de `Para priority,`.

| Arquivo | SHA-256 |
| --- | --- |
| Manifesto Luna R4 | `ba0701bd3b003cb146f8212bef1753d45c9a2ef8d548472ffe3d04d83cced888` |
| Prompt 1.2.0 | `026c70c89da05102f9c6b84c87ba8e2c522d8d77cd2405403849d6823b7e2741` |
| Manifesto Luna R3 | `1daac4749be2e8ac07989780ce5b4aae58f3f7f2bbbf460fdfb904a98295caf5` |
| Prompt 1.1.0 | `c03848e1f9266ae2aadb5d28d8f82265034c0312067a5e3204aea723437cfa75` |
| Política 1.1.0 | `6893a119e6dc90aef81e10cc803dba8d66e3cf4c04cc4f3f2d333515c4b2a039` |
| Rubrica 1.0.0 | `ac497f8d36af1aceb4eac39648ca7fe2c1e291d16cf512f27894b40e113ed4ac` |
| Luna operational.json | `0666cdd1c99f58c52512681563b72ddcaf4f97593071a1797104526d062678da` |
| Luna adapter.py | `cf221d6d1f39f27bbc3d4388d6c14091fe869e0351ca8564c713284eca4b3845` |
| Luna transport.py | `60673dff9db3f3dd8e16db409843ec6d073397053a66e664a5b65e2b98d03ea0` |

## Verificações

`rtk git diff --cached --check` saiu com código zero antes do commit. `rtk git diff --exit-code 3e59f4a -- script/classification_comparison/adapters/luna/adapter.py script/classification_comparison/adapters/luna/transport.py script/classification_comparison/adapters/luna/operational.json script/classification_comparison/adapters/luna/candidate.json script/classification_comparison/adapters/qwen/r2 docs/planejamento/classificacao-comparativa/rubrica-comum.md` também saiu com código zero.

A partir da worktree de instrução, este comando executado passou nas três máscaras. A função que o adaptador usa para montar o corpo recebeu relato artificial e o catálogo lido exclusivamente da primeira linha do desenvolvimento R3. O gancho de auditoria proíbe eventos de socket durante essa execução.

```sh
rtk proxy python3 -B - <<'PY'
import json
import sys
from hashlib import sha256
from pathlib import Path

def offline(event, args):
    if event.startswith("socket."):
        raise RuntimeError("uso de rede proibido neste ensaio")

sys.addaudithook(offline)
adapters = Path("script/classification_comparison/adapters")
sys.path[:0] = [str(adapters.parent), str(adapters / "qwen")]
from adapters.luna.adapter import request_body

luna = adapters / "luna"
old, new = [json.loads((luna / file).read_text()) for file in
            ("candidate.json", "r4/candidate.json")]
assert old.keys() == new.keys() == {"contract_version", "identity", "prompt", "policy", "rubric"}
assert all(old[key] == new[key] for key in old if key != "prompt")
assert new["prompt"]["version"] == "1.2.0"
assert new["prompt"]["sha256"] != old["prompt"]["sha256"]
for manifest in (old, new):
    for key in ("prompt", "policy", "rubric"):
        entry = manifest[key]
        assert sha256(Path(entry["path"]).read_bytes()).hexdigest() == entry["sha256"]

operational = (luna / "operational.json").read_bytes()
assert sha256(operational).hexdigest() == "0666cdd1c99f58c52512681563b72ddcaf4f97593071a1797104526d062678da"
parameters = json.loads(operational)["request"]["parameters"]
old_prompt, new_prompt = (Path(m["prompt"]["path"]).read_text() for m in (old, new))
assert old_prompt.partition("Para category,")[0] == new_prompt.partition("Para category,")[0]
assert old_prompt.split("Para priority,", 1)[1] == new_prompt.split("Para priority,", 1)[1]
rubric = Path(new["rubric"]["path"]).read_text()
catalog_source = Path("docs/evidencias/c05/luna-ensaio-real-01/development/inputs.jsonl")
with catalog_source.open() as development:
    catalog = json.loads(next(development))["catalog"]

for missing in (["category"], ["priority"], ["category", "priority"]):
    received = {key: val for key, val in {"category": "pix", "priority": "basic"}.items() if key not in missing}
    context = dict(text="Mensagem artificial.", brand="marca-sintetica", catalog=catalog,
                   missing=missing, received=received)
    item = dict(context, id="teste-local", contract_version="1.1.0")
    bodies = []
    for prompt in (old_prompt, new_prompt):
        instructions = prompt + "\n\n" + rubric
        body = json.loads(request_body(item, received, instructions, 128, "none"))
        messages = body.pop("messages")
        assert messages[0] == {"role": "system", "content": instructions}
        assert len(messages) == 2 and messages[1]["role"] == "user"
        assert json.loads(messages[1]["content"]) == context
        schema = body.pop("response_format")
        assert schema["type"] == "json_schema" and schema["json_schema"]["strict"] is True
        shape = schema["json_schema"]["schema"]
        assert shape["required"] == missing and shape["additionalProperties"] is False
        assert shape["properties"] == {key: {"type": "string", "enum": [*catalog[key], "informacao_insuficiente"]}
                                       for key in missing}
        assert body == parameters
        bodies.append((messages[1], schema, body))
    assert bodies[0] == bodies[1]
print("Pins, escopo da edição e três máscaras de campos ausentes conferidos offline.")
PY
```

Nenhuma chamada a modelo ou fornecedor. Os testes verificam instrução, parâmetros, projeção e formato do corpo. A classificação efetiva, latência e custo R4 ainda não foram medidos. O executor R4 permanece fora desta entrega. A revisão e o congelamento independentes cabem ao integrador antes de reunir a instrução e os diagnósticos.

Para explorar a mudança, marque em uma consulta cotidiana qual trecho identifica o que o cliente quer entender e qual trecho apenas sugere uma causa. Depois remova a descrição do objeto e veja quais categorias ainda seriam plausíveis.
