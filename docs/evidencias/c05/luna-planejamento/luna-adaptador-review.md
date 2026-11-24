# C05-R3 · Task 3-A · Revisão independente do adaptador Luna

**Resultado do SPEC e QUALITY em `dc74cd3`: corrigir antes de congelar.**

- Base `eaca1c6b64f407e628929023145d5cf1479973d2`.
- Candidata revisada `dc74cd321f769db49123b018c9e5c8e1ca264c83`.
- Branch `feat/luna-feita`, worktree `.worktrees/r3-luna-adaptador`.
- Evidência de escopo em `review-eaca1c6..dc74cd3.diff`, no diff Git correspondente e em `luna-adaptador-report.md`. Esta revisão cobre a candidata e o transporte antes do congelamento.

## SPEC

**Bloqueante — validar orçamento e tarifa da Luna antes do despacho.** Em `script/classification_comparison/adapters/luna/adapter.py:29`, o modo real só rejeita `budget is None`. O código compartilhado usa a veracidade do objeto em `script/classification_comparison/adapters/qwen/adapter.py:167–173,197–206`. Com `budget=False`, a identidade real chega ao único POST sem chamar `reserve` e atribui à Luna a tarifa pública do Qwen. Com o orçamento sintético usual e `tariff=None`, o POST ocorre e só depois `rates` levanta `Blocked`. Os dois resultados foram reproduzidos com o gateway do teste e envelope artificial. Em cada execução o duplo recebeu um corpo. A configuração esperada da Task 3-B fornece um orçamento válido, mas a interface direta da candidata permite essas entradas. Validar o orçamento presente e sua tarifa antes que a candidata possa despachar, preservando a fixture isolada com `None` e os defaults históricos do Qwen.

Os demais pontos de SPEC revisados estão conformes com o brief.

- `candidate.json` tem cinco chaves, incluindo `rubric` com `path`, `version` e `sha256`, além da identidade fixa Feita/Luna. As referências de prompt, política e rubrica conferem com os arquivos originais. O manifesto histórico Qwen de quatro chaves e suas fontes estão byte a byte iguais à base. `operational.json` é separado e os SHA-256 do relatório da implementação conferem.
- O corpo fixa `openai/gpt-5.6-luna`, `reasoning_effort=none`, `max_completion_tokens=128` e `stream=false`. Restringe o schema estrito aos campos ausentes e usa o prompt e a rubrica na ordem documentada. A política R2 preservada fica como referência. A identidade valida os providers real e fixture, modelos e versões.
- Os envelopes sintéticos exercitam rejeição de entrada inapta antes do transporte, uma chamada para dois campos, preservação do campo fornecido, aplicação integral ou revisão, score ausente, abstenção e recusa sem encerrar sessão, e interrupção após falha técnica ou incompatibilidade de procedência.

## QUALITY

- `transport.py:50–80,115–139` abre a conexão no primeiro caso, confirma despacho no pai antes do POST e reaproveita a conexão após resposta completa. Fechamento indicado pelo servidor permite uma nova conexão no caso seguinte. Erro HTTP, EOF, socket obsoleto e prazo vencido encerram a sessão sem repetição.
- O prazo absoluto acompanha a primeira chamada desde o início do processo. O pai usa o tempo restante no canal local, inclusive enquanto o filho está no connect DNS/TLS ou em leitura bloqueante com conexão reutilizada. O tempo de criação do processo e o callback executam de forma síncrona no pai. Ao retomarem, há nova verificação de prazo antes da próxima operação. Isso limita o I/O HTTPS e impede POST após um ACK vencido, sem garantir interrupção arbitrária de uma inicialização ou callback local bloqueado. O teste do prazo frio bloqueia o duplo no connect.
- `transport.py:42–51,141–159` monitora o canal de vida do pai e o fechamento explícito recolhe o processo. A suíte simulou o EOF desse canal durante leitura bloqueada. Na Task 3-B, a entrada IPC precisa chamar `close()` em `finally` e fechar também o gateway se a função que captura os bytes não propagar `close()`.
- Erros HTTP 307, 429 e 503 preservaram integralmente os bytes sintéticos, inclusive o custo, sem novo POST. A Task 3-B ainda precisa encadear a persistência da evidência antes do ACK e conciliar os bytes no executor. A comprovação financeira integrada fica para a fase correspondente.
- A alteração comum extrai o schema e adiciona o construtor de corpo opcional com default Qwen. Ordem e bytes foram conferidos em envelope sintético com o parâmetro histórico `reasoning`.

## Verificações executadas

```sh
rtk proxy env PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen \
  python3 -B -m unittest -v adapters.luna.test_adapter adapters.luna.test_transport
rtk proxy git diff --check eaca1c6..dc74cd3
```

A suíte passou com 19 testes em 4,776 s. O diff passou na verificação de espaços. Conferi os SHA-256 da candidata, da operação, do runtime e das fontes com os valores do relatório. Também executei dois envelopes de prioridade fornecida e categoria ausente com o gateway sintético, variando o orçamento real para `False` e `SyntheticBudget.tariff=None`, que reproduziram o achado acima.

O aceite desta revisão é pré-freeze. Casos finais, gabaritos, saídas históricas, preflight e suítes que carregam o pacote final ficaram fora da verificação. Compatibilidade com a Feita, latência real e integração do executor permanecem pendentes. A revisão usou credencial artificial e conexões duplas, sem rede e sem acesso a credenciais ou conta reais.
