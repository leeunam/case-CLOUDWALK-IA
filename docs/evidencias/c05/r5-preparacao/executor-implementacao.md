# C05-R5-B · Executor com auditoria da Luna

**Entrega para revisão**. Commit `0161b962b298720d39823b45c76ef45a1af679a0`, branch `feat/luna-executor-r5`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r5-luna-executor`. Base final `433c442d135925098f4d724ed6688b80bf43bf1b`. A integração e a decisão sobre consumo ficam com o integrador.

A base inicial era `5dc40309389a62e367f229c63cde68bed4a7327a`. A política 2.0.0 foi congelada antes do meu acesso ao pacote final. Encontrei quatro campos positivos de desenvolvimento para os quais nenhuma citação era aceita. Documentei apenas os relatos de desenvolvimento em `r5-b-development-blocker.md`. A política revisada 2.1.0 foi produzida por outros autores e congelada em `docs/evidencias/c05/r5-candidata-v2/`, depois desse acesso de B. O pacote final permaneceu intacto. O commit B não edita A ou os congelamentos anteriores.

## Entrega

- Perfil dedicado `observed-total-luna-r5`, escopo `c05-feita-luna-r5`, protocolo 1.5.0, relatório 1.6.0. A candidata congelada do commit `38ac4cb81abe9f84469e379cee30e6bb976e25dd` emite envelope 1.0.0 com observação 1.1.0. Não houve mudança em API, backend de produto, transporte histórico, ledger ou política de classificação.
- O filho injeta o custo obtido em decimal da resposta original e envia um único envelope. O pai verifica schema, origem, insumo e decisão pelo replay, escreve o envelope integral no diário da etapa e mede o tempo total no modo real. O relatório 1.6 requer a referência da auditoria em todos os modos.
- Uma interrupção conserva a evidência recebida e separa o prefixo confirmado de eventual observação pendente, inclusive com zero POST. O fechamento verifica ordem, bijeção, hash, contagem, LF e versão antes de emitir a prova. O selo compromete os hashes dos artefatos originais. O comando dedicado `verify-final` confere recibo, conta, manifesto, saldo das reservas, prova de desenvolvimento e ambos os selos. O checker público verifica coerência dos artefatos publicados; a verificação com a conta/selo independentes fornece a âncora contra substituição conjunta da publicação.
- Limite solicitado de 384 tokens, uma tentativa. A reserva usa o maior custo conservador configurado nas tarifas e nos limites faturáveis. Exemplos real e manifesto desabilitados. Nenhuma consulta a fornecedor, chave, .env ou conta SQLite real em B. Os custos abaixo são sintéticos.

## Reprodução no commit fechado

Pelo CLI completo, com conta SQLite temporária de fixture criada do zero, o desenvolvimento produziu 6 envelopes, 8/8 alvos corretos, 4/4 campos recebidos preservados, 3 conclusões, 3 revisões, 1 urgência e zero erros. Gate `fixture_ready`. O final processou 36 relatos e 13 controles. Os 44 despachos elegíveis tiveram 44 envelopes, com abstenção explícita de cada campo solicitado no simulador. O controle injetado manteve sua origem independente. Ambos os relatórios registraram `inconclusive`, p95 sem medição. Os dois runs terminaram `finished`, com 50 reservas liquidadas. A soma sintética foi USD 0.003282 + USD 0.024068 = USD 0.027350. A classificação e a latência reais da Luna continuam sem medição.

Sequência executada em cada etapa: `init-account --mode fixture` uma vez, `run --dry-run`, habilitação de cópia do manifesto da conta sintética, `run --confirm-execution` e `check_classification_contracts.py --report`. A etapa final forneceu o gate original e passou adicionalmente em `verify-final`. O teste `test_cli_development_final_and_original_receipts` reproduz a sequência completa em diretórios novos. A conta e as saídas temporárias dessa reprodução foram removidas pelo encerramento normal do teste. Cada reprodução possui ID e horário próprios.

| Etapa | Arquivo | SHA-256 dos bytes conferidos |
|---|---|---|
| development | `plan.json` | `adbbc7a50dbc5318bb433b756e4c4832622b776f0edff1b4b3b94487827cfc41` |
| development | `report.json` | `1dee8736668800e7d31044759aae6022e1e1e4cb6b596ace2302e52474298748` |
| development | `luna-evidence.jsonl` | `049944ec4dc2ca5bbd0eebd537a5110cd09df18a6c4483b0be2f929b82c0542f` |
| development | `development-gate.json` | `0bd333079e8658957fe2a064d04103cf0e7c63e627eb8b11cf705a45023768eb` |
| final | `plan.json` | `600501f1abcd5bb4b70d3b2603ca012d412beaea1e195b71d8c06000f9662137` |
| final | `report.json` | `9aca5ef5fc40d6e7cb7674bd33c4382ed8ef4243f5486422b0548c6c11999c54` |
| final | `luna-evidence.jsonl` | `1a9ea946b1eb1958b4ef5b60911f7c59bca98b484a20c3f5d87e5ebc8559e1ee` |
| final | `final-receipt.json` | `72de5a264b42f042ee0da46c279348701dae9876277830b01b2fdf60e8908802` |

## Verificações executadas

- `rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-r5`: 5 schemas, 13 entradas, 9 observações, 13 decisões e 9 mutações rejeitadas. A fixture estática foi gerada a partir de controles com a candidata ativa.
- `rtk proxy env -u FEITA_API_KEY PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna_r5.test_round`: 7 testes, todos aprovados em 20,109 s. Abrangem as duas etapas de CLI, selação, reescrita de recibo, hash/contagem/schema, linha ausente/duplicada/extra/invertida/incompleta, quote/insumo/modelo/escolha/provider, relógio do pai, erro de perfil, gate reprovado/alterado, conta/modo incompatíveis e tentativa única em seis falhas. As falhas incluem antes do POST (zero requisições, uma observação e um envelope), posterior ao despacho, HTTP 429, resposta inválida, procedência divergente e custo desconhecido.
- `rtk proxy env -u FEITA_API_KEY PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen python3 -B -m unittest adapters.luna.r5.test_evidence`: 33 métodos, todos aprovados na base final. Conferi os 17 arquivos completos e os 7 ASTs do freeze ativo por SHA-256.
- Regressões feitas durante a implementação: 39 testes de `test_interruption test_evaluator test_observed_latency`, 37 do executor Qwen `c05/test_qwen_final.py`, 14 de `r2/test_r2.py` e 17 de `luna.test_round luna_r4.test_round` passaram. Uma tentativa agregada importou R2 sem seu diretório no caminho de módulos. Corrigi o comando com `PYTHONPATH=script/classification_comparison/r2:script/classification_comparison python3 -B -m unittest discover -s script/classification_comparison/r2 -p test_r2.py`. Os 17 testes Luna passaram na invocação agregada. Após compartilhar o fechamento do selo entre etapas, os dois testes R2 dirigidos de prova/selo e a CLI completa R4 passaram novamente.
- `docs/evidencias/c05/r4-instrucao/conferir_historico.py` conferiu 25 relatórios, o protótipo 1.0 e os 12 + 7 hashes das candidatas históricas. O checker 1.5 passou em 13 controles e nos 12 negativos da R4. Na auditoria independente do resultado R4, 23 hashes de execução corresponderam aos blobs Git de `1c89c264ca7cba4e8cde72ec9098181435def74d`. O manifesto preserva o binding original, os sete artefatos do gate conferem e o checker reconhece o relatório R4. O gate anterior continua `failed`.
- Conferidos sintaxe Python, diff efetivamente selecionado, `git diff --cached --check` e `git diff HEAD^ HEAD --check`. O commit contém 26 arquivos. Não foram integradas nem publicadas branches.

## Assinaturas

O binding de cada execução contém os 37 hashes abaixo; o manifesto contém o hash da configuração e a referência ao lock de fontes/contratos. Esses hashes são da **implementação B completa** no commit acima. A freeze de A conservou apenas as fontes semânticas e auxiliares estáveis, além das sete funções compartilhadas por AST.

- `docs/evidencias/c05/r5-candidata-v2/candidate-freeze.json` · `4a9776c632664a104bdf7b7f9350b6bde0d9334a52f8c25155840358a3b1f9d5`
- `docs/planejamento/classificacao-comparativa/r5/binding.json` · `1b01be1e87c0f090329b9dbfad8431d2ac7bcb82be89ff9e991fe46cc79f0d8f`
- `docs/planejamento/classificacao-comparativa/r5/protocol.json` · `343bf7e3a0377a0fc129fb98282662cbbae034604d62cee0d33c3480649cde3c`
- `docs/planejamento/classificacao-comparativa/contratos/relatorio-1.6/sources.lock.json` · `5e3c8afa8ef0e8e3e48b02a4ec8e17e6e7c7b3a2026eeb8c97370a087c3bcd84`
- `script/classification_comparison/luna_r5/config-fixture.json` · `1505fb8e90a0d12c720102326a6ac72e4dab49e2bc8a6a7b1f28105e279bad4e`
- `script/classification_comparison/luna_r5/config-real-exemplo.json` · `a847f65462a1156e2880c17c2c5f84ee776f8a258431df55243b4b1d87fbdc31`

```json
{
  "docs/planejamento/classificacao-comparativa/contratos/common.schema.json": "bc242132690bfef7504e0124a1758b56c9a336359ab9ffde038f8645a8cef0c3",
  "docs/planejamento/classificacao-comparativa/contratos/input.schema.json": "2e943f5b228181366da189b9b51b463ffb1ea8140aabf01e701ad9e4232339fa",
  "docs/planejamento/classificacao-comparativa/contratos/observation.schema.json": "0df9647efe7e57768904cdecf24c1e42a3ce2ce6e977a73a073b0b5169bc3d38",
  "docs/planejamento/classificacao-comparativa/rubrica-comum.md": "ac497f8d36af1aceb4eac39648ca7fe2c1e291d16cf512f27894b40e113ed4ac",
  "script/check_classification_contracts.py": "38e17edce7f92c519c1e9e378d8e06883c80bbe4708ade926c2310656f286278",
  "script/classification_comparison/adapters/luna/adapter.py": "cf221d6d1f39f27bbc3d4388d6c14091fe869e0351ca8564c713284eca4b3845",
  "script/classification_comparison/adapters/luna/r5/adapter.py": "8ac5c50ace54a58293bd63c4147a262a6dfbfcb566a2f5be2aac3f3eb5dfeecf",
  "script/classification_comparison/adapters/luna/r5/candidate.json": "d95c4691cbd4babeb000be285b4bdbca632bf4d8ea4ffe3b83d818579ac9df99",
  "script/classification_comparison/adapters/luna/r5/evidence-envelope.schema.json": "c788f313a1c002f4c6e78b400a91120a2373d744184006b50725f91f7239f579",
  "script/classification_comparison/adapters/luna/r5/evidence.py": "42dcd4fd4806a485606d359eb64b86bcb59e4e299892288ce4e3624cde971557",
  "script/classification_comparison/adapters/luna/r5/operational.json": "745fbc7eeef9abf17c7fb2e3a8a28619a40941362ea4a8e8c01e75b20b28f1f3",
  "script/classification_comparison/adapters/luna/r5/prompt.txt": "fb4437c677a6b6eea2fb55d6fdebd7143b22c9738f273a561f4601cac38e1610",
  "script/classification_comparison/adapters/luna/transport.py": "60673dff9db3f3dd8e16db409843ec6d073397053a66e664a5b65e2b98d03ea0",
  "script/classification_comparison/adapters/qwen/adapter.py": "fefe1b4458d667bf9701e59ce2071d368a92169848ba14e6ccd516ab7d74c90f",
  "script/classification_comparison/adapters/qwen/fixture.py": "7d0d2d3a86971481664652488afb4eb83bcd961be693b03dfdc1c1904b1a5dbf",
  "script/classification_comparison/adapters/qwen/pilot.py": "5605c8cfc06af9acea2319aad2c9284c46ab381e3262362fbeda99e5e866c79b",
  "script/classification_comparison/adapters/qwen/tarifas-publicas.json": "4494fc5d7d0f970521560697ae3facc16773fed8c38d7ef28df9b78686bf27cf",
  "script/classification_comparison/adapters/qwen/transport.py": "a93f322b347efe69096aa4fa1483ae003b2ef06a2e1e1077ed09cbcab4f030f2",
  "script/classification_comparison/c05/budget.py": "d9a81084546db988ef8afc6f33732120749c749a9415bebae07f3402dbbef44e",
  "script/classification_comparison/c05/execute.py": "cc488cf9110b2b80c67551a6ff912cd598d3f90981f20edc181aaef4697387ef",
  "script/classification_comparison/c05/final_adapter.py": "63e60d90ed34f7177a149cb2760101209e647434ef9cb9c3a0099f4829eef7c2",
  "script/classification_comparison/c05/settings.py": "b4454da14661fcd86df77492fc68e67c5109de6b5da277d00730354fbab13792",
  "script/classification_comparison/common.py": "5429d8ca197516e03d01f97fa132c07e4fab0bc39f17cd425a025bed786fc547",
  "script/classification_comparison/journal.py": "ca1025272462cfd40e0df523967c6607741ab646339a642dd751d5c1ce7f0771",
  "script/classification_comparison/luna/execute.py": "4ba3c07367d706be15e11f6e03797b702e3fe2889fc01f6bad22aabad3b49da1",
  "script/classification_comparison/luna/round_spec.py": "cf7406176031219c55c44eb0f20e2b9f216b0024f5938d690844ec23c57e2d8d",
  "script/classification_comparison/luna_r5/audit.py": "211ed8b2662024905685ab94f40128e47e389c2da3ce8b349280d0750413ec14",
  "script/classification_comparison/luna_r5/execute.py": "b45bfbfe4015519c04ccc11fdbb52a6e81b57d6e17a1ebc741d0f084af0eb604",
  "script/classification_comparison/luna_r5/fixture_gateway.py": "0d6f146f051b6cf0bbb95f0849760d255a2316ef846099fce7970d274328f3f0",
  "script/classification_comparison/luna_r5/round_spec.py": "fc6816f2b6b7b56d20771cb9b31e88f450218cd94cf0351614620c44ca7f609a",
  "script/classification_comparison/metrics.py": "a025054e9e3eecfb377020e95e8ac43f6b3cb671aedd295afcf59443a4a1474a",
  "script/classification_comparison/r2/execute.py": "91a780f7d7da9e3ba3df0c19118037e951f9b65510cc7b204dc51a384261085f",
  "script/classification_comparison/r2/gate.py": "608aaa597e9fcfcafad26c65ef6d701f6c9be013a9d6ff584ea2043e8d83ee8e",
  "script/classification_comparison/r2/plan.py": "100c33a1bc8475ff93fbe50a8ea31fb2a51d2a0e0f18c1de84175c6e884b1931",
  "script/classification_comparison/r2/seal.py": "2dfebb17c8e59307295f45cdc85b4911e75df447b52d9df811adaceabe28e9da",
  "script/classification_comparison/run.py": "5d8f2872b4d821b8373c8d7fb6ace4bc67a619e7f74564eda0385054ba62a9d9",
  "script/f08/jev/catalog.json": "14bbf6298ee8c6d5c9002128cd596e5250e71cbb0077e49a18fde49c265d2271"
}
```

Exercício local: siga um campo fornecido pelo canal e um campo ausente nos streams de entrada, auditoria e decisão. No teste de adulteração, altere apenas a citação e confira o erro de replay mesmo com o SHA público recalculado. O guia operacional fica em `docs/c05-luna-r5.md`. Ainda estão pendentes a revisão independente de B, a revisão ampla A+B, a integração e a decisão sobre operação real.

## Apêndice · Reparo dirigido dos dois achados P2

A entrega ativa de B passa a ser `999e0cf22e284c3a7356da0a4107bb6bfc9f0557`, sobre `0161b962b298720d39823b45c76ef45a1af679a0`, na mesma branch e worktree. O registro anterior documenta o snapshot efetivamente revisado. Este reparo mantém a candidata 2.1.0, as sete funções congeladas por AST, os schemas, o lock, as tarifas, os contratos históricos e o ledger.

O checker do prefixo agora verifica hashes e localização dos originais, a projeção completa do plano, os registros do diário, ordem e estado do despacho, o prefixo persistido e a eventual tentativa pendente. O evento de interrupção R5 vincula a observação que já atravessou a validação, ou registra nulo se a interrupção ocorreu antes. Assim, um envelope válido recebido antes de validar a observação pode aparecer no original sem ser contado no prefixo. Os usos da tentativa e do prefixo são conferidos separadamente.

No desenvolvimento, o checker público usa `r2.gate.assess` com os insumos, observações, decisões, limiares congelados e o inventário público de custos por caso. Compara o status e todos os contadores reproduzíveis, inclusive latência e número de chamados conciliados declarados. O checker final exige a mesma elegibilidade do relatório. Estado real das liquidações e autenticidade do recibo continuam exigindo a conta e seus selos.

**Provas na correção.** Oito testes R5 passaram na própria cabeça em 29,485 s. Dois cenários interrompem a segunda tentativa depois de um caso concluído, antes e depois da validação da segunda observação. O checker recusa ausência ou reescrita do diário, divergência no inventário e nos IDs, remoção da observação já validada, status omitido ou contraditório (dev e final), e contagens adulteradas. Um desenvolvimento realmente `failed` ainda passa como registro público reprovado. Os checkers R5/R4 aceitaram as fixtures e rejeitaram, respectivamente, 9 e 12 mutações. Passaram 26 testes de interrupção e CLI R4 e um teste de CLI R2. Em uma execução intermediária da suite, editei o diário enquanto uma fixture ainda verificava o selo. A verificação recusou o binding antigo, e o teste que esperava atingir o selo falhou. A suite inteira passou em árvore estável e novamente no commit fechado. `git diff --cached --check` e `git diff HEAD^ HEAD --check` passaram.

**Reprodução adicional em HEAD.** A partir de outra conta fixture temporária, ambas as etapas rodaram pela CLI e ambos os relatórios passaram no checker público. O `verify-final` confirmou o gate e o selo originais da mesma conta. Foram 6 envelopes em desenvolvimento (`fixture_ready`), 44 no final (`inconclusive`), 50 reservas sintéticas liquidadas e USD 0,027350 sintéticos. Nenhuma conta real, chave, rede ou chamada de modelo.

development

- `plan.json` · `b0062ca3a3504764f2cf41331eb6e6dba6151c74b6df7f9266e03e52a510013d`
- `luna-evidence.jsonl` · `89074a3cc994719f76485818da00e8bdc92e0c8449244d7a04a4487d89c06df9`
- `report.json` · `652d067d908a77ec91849531a1dad85a4c8a733b9d4d7b138068d795321b11b6`
- `development-gate.json` · `5b765a13d76d31def666c2901ba6e51249e0cd9854ff6e3f5ccdc018712f66dd`

final

- `plan.json` · `904c4cf241018c880331fb87919eb662e237c452138c7302e2a0f85b8075165b`
- `luna-evidence.jsonl` · `969ae8afbd5173bf43985e6ea29bb4eba2da65b2b4679cdee6ebd4bf8b362f6f`
- `report.json` · `ef74a7dfdb7487352aba296cf9ec2802b74ec9b479829cfc6f6956197ac7b0ba`
- `final-receipt.json` · `ce0b0204244e6a060621b8b71b73d7fc0b2da768dc9a90597bce286fa9224d2d`

O binding voltou a conferir os 37 hashes no disco. As quatro fontes executáveis com bytes novos nesta passagem são:

- `script/classification_comparison/journal.py` · `59aa4ddc1806db848237326da1690090a6bda6034345b2d3a39150aa9d16ff1f`
- `script/check_classification_contracts.py` · `24424268e03ac26ab99a517458791afaa7077b1b9e42f3b5b272ebf3526b7ccc`
- `script/classification_comparison/r2/gate.py` · `f1a015cdb5df47987b44fbc36ca139a1ad085497b96f0b742674f7b2740f6f24`
- `script/classification_comparison/luna_r5/audit.py` · `adad9e272db363e330228a3aa26501263f629641d241f3cf3ab0dde192d539f4`

A revisão dirigida e a revisão ampla ficam com o integrador. A referência financeira conferida na cabeça anterior precisa de nova vinculação antes de qualquer uso real.

## Apêndice · Reparo focal 2 dos tipos JSON

Commit ativo `dd604455facffa2cf6a62d0fd8358ab2ca5b43eb` sobre `999e0cf22e284c3a7356da0a4107bb6bfc9f0557`. Só mudaram `luna_r5/audit.py` e `luna_r5/test_round.py`. O verificador usa a comparação JSON estrita existente nas duas alternativas de encerramento do diário, nas referências de evidência e nos agregados de uso. A expressão de igualdade do Python aceitava `true` no lugar de `1`. O verificador agora distingue os dois tipos, inclusive em dicionários ou listas aninhados.

Nos testes dos dois estados legítimos da segunda observação, o checker aceita o prefixo íntegro com um caso concluído e uma tentativa pendente. Rejeita `verified_luna_evidence.count=true`, `interrupted_usage.requests=true` quando o uso esperado é 1 e `dispatched.attempt=true` mesmo com o novo hash do diário inventariado. Há ainda provas diretas de que `finished.decisions=1` sem pendência e `dispatch_started.attempt=1` com pendência são aceitos e suas versões booleanas são recusadas.

Com os arquivos já estabilizados, `rtk proxy env -u FEITA_API_KEY PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna_r5.test_round` passou nos nove testes em 28,329 s, incluindo as duas etapas 6 + 44 com conta temporária, recibos e selos. O checker R5 passou nas 13 entradas de controle e nas nove mutações previstas. `git diff --cached --check` e `git diff HEAD^ HEAD --check` passaram. A worktree está limpa. Não houve inferência de fornecedor, uso de rede, acesso a segredo ou conta real.

Conferência pós-commit: o binding da nova revisão corresponde aos 37 arquivos em disco. Somente o hash de `script/classification_comparison/luna_r5/audit.py` mudou no runtime, para `422e9b2b795ceb261db1d2b67109985d593074be59c544ef12db20587c7eb482`. O lock estático continua em `5e3c8afa8ef0e8e3e48b02a4ec8e17e6e7c7b3a2026eeb8c97370a087c3bcd84`. Nenhum artefato ou recibo anterior foi refeito. A conferência independente dos tipos e a revisão ampla ficam com o integrador.

## Correção dirigida após a revisão ampla A+B

Na branch `feat/luna-executor-r5`, worktree `.worktrees/r5-luna-executor`, o commit `a949f52019c20ba9afccc6854ba42734cf03ba04` sucede `dd604455facffa2cf6a62d0fd8358ab2ca5b43eb`. O diff contém o verificador público R5, o teste do executor e o guia de conferência de um lote salvo.

O verificador das duas etapas confere as quatro versões declaradas no recibo, plano, vínculo e invocação, reproduz o SHA-256 canônico do vínculo e confere o SHA-256 do manifesto contra a invocação. Para cada observação da candidata, ele exige uma chamada com valor original conhecido e um comprovante individual com referência normalizada e exclusiva no lote. O valor liquidado deve caber na reserva e alcançar ao menos o custo original na precisão preservada pelo IPC. A soma usa a aritmética decimal do ledger. Essa conferência pública permite correções para cima. A existência da correção e a autenticidade do recibo continuam sujeitas à conferência dos originais contra o selo e a conta.

O teste do CLI exerceu 25 mutações isoladas por etapa, entre elas o mapa ausente, custo individual nulo, comprovante repetido, total zero diante de custos não nulos, valor negativo, `NaN`, valor JSON numérico, versão ausente e hashes ausentes ou divergentes. Com o total recalculado, rejeitou os dois valores fora dos limites e aceitou duas correções consistentes, inclusive um acréscimo de USD 1e-30 no custo de uma chamada. Os testes restauraram os bytes originais antes de autorizar o final e antes de repetir a verificação privada. O desenvolvimento continuou `fixture_ready`, com seis chamadas, e o final `inconclusive`, com 44 chamadas, 50 reservas sintéticas liquidadas e USD 0,02735 somados nas duas etapas.

Com as fontes estáveis, a suíte `luna_r5.test_round` passou nos nove testes em 57,348 s. O checker `--profile observed-total-luna-r5` confirmou cinco schemas, 13 entradas, nove observações, 13 decisões, um relatório de fixture e nove rejeições previstas. O diff passou em `git diff --check`. No commit final, o plano confirmou as 37 fontes do executor. O novo SHA-256 de `audit.py` é `28644b016f53b3844a31bf7b1345ada5b38430743dbdb244ab65b89ccc5722cc` e o lock semântico mantém `5e3c8afa8ef0e8e3e48b02a4ec8e17e6e7c7b3a2026eeb8c97370a087c3bcd84`. A execução usou exclusivamente transporte simulado e conta temporária.

Para reproduzir, execute os dois comandos da seção “Reprodução com transporte simulado” de `docs/c05-luna-r5.md`. Para acompanhar a regra decimal, veja o subcaso `0.000547000000000000000000000001` de `check_receipt_finances` e compare o custo original projetado no IPC com a soma publicada no recibo.

Reexecutei o teste de CLI 6+44 já em `a949f52`. As duas etapas, as mutações do recibo e a conferência dos originais passaram novamente em 25,970 s.
