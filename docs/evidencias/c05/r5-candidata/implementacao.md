# R5-A · Implementação entregue para revisão

- Base `0b0223eb2fc8d258c7e0351212b0b22959c05697`.
- Branch `feat/luna-evidencias-r5`.
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r5-luna-evidencias`.
- Commit `065deee14b03e350a4d96a360cdca47b477519cd`. Worktree limpa.

## Entrega

Novo módulo `script/classification_comparison/adapters/luna/r5/` com uma
candidata, contrato privado, política, prompt, manifesto, perfil operacional,
schema de envelope e testes artificiais. O documento
`docs/c05-luna-r5-candidata.md` descreve a auditoria e a reprodução. O commit
contém somente esses oito arquivos. A R5-A não integrou nem publicou a branch.

O adaptador valida o formato dos campos ausentes antes da interpretação
semântica. Se houver saída privada malformada, o conjunto tem falha técnica
e as partes legíveis ficam na auditoria. Abstenções bem formadas mantêm a
sessão aberta. O envelope registra as escolhas de todos os campos ausentes
e deixa a aplicação integral sob a decisão comum. O teste cobre uma categoria
aceita ao lado de prioridade vetada, com revisão e aplicação parcial zero.
Um código recebido que está no catálogo é preservado. Novos códigos e novas
definições textuais em predições exigem política conhecida.

O entendimento da candidata se limita às relações e ao escopo explícito que
seus padrões reconhecem. As famílias de paráfrases artificiais de Pix por
chave, venda a débito e leitora de cartões tiveram suporte nos três exemplos
positivos do teste. A política não mede a veracidade do relato nem resolve
sarcasmo, elipses e referências implícitas. A adequação das expressões
semânticas, dos prazos reconhecidos e do limite real de 384 tokens fica para
avaliação. Nenhuma leitura de casos, rótulos ou resultados finais foi feita.
Só usei o catálogo comum, a rubrica e relatos artificiais. O export local de
metadados de desenvolvimento continha as mesmas definições do catálogo.
Não executei preflight, Plan, suites históricas com conjuntos finais, nem
ensaio externo. Não acessei conta, credencial ou SQLite real.

## Passagem exata para R5-B

Com `PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen`,
o módulo `adapters.luna.r5.adapter` exporta

- `R5Adapter(identity, run_id, instructions, transport, budget=None, timeout_ms=5000, *, clock=time.monotonic)`.
  `.classify(item)` retorna `{"profile_version": "1.0.0", "observation": ..., "audit": ...}`.
  `.close()` é idempotente. O chamador filtra entradas incompatíveis, completas
  e inválidas pelo fluxo comum. Controles injetados não passam pela candidata.
  Uma entrada completa ou inválida enviada ao IPC levanta erro sem despacho.
- `identity_for(mode)` retorna os pins para `"real"` ou `"fixture"`.
  `candidate.json` fixa a identidade real. As instruções são o prompt e a
  rubrica unidos por `"\n\n"`, nessa ordem. `operational.json` e
  `evidence-envelope.schema.json` são referenciados no manifesto.
- `validate_envelope(envelope)` retorna `None` ou levanta `ValueError` de
  schema. O registro local resolve a referência para o schema IPC 1.1.0.
- `replay_envelope(item, envelope, *, policy_sha256=None)` valida schema,
  identidade/contagem IPC, ID do item, hash do insumo, hash da política,
  auditoria e igualdade das escolhas. Retorna o dicionário de auditoria
  reconstruído ou levanta `ValueError`. Passe o SHA-256 congelado de
  `evidence.py`. O executor vincula externamente `observation.run_id`,
  identidade esperada para o lote, tentativa, inventário e recibo financeiro.

O módulo `adapters.luna.r5.evidence` exporta
`build_audit(item, raw_content, finish_reason, *, refusal=None, error=None)`,
`project_choices(audit)` e `input_sha256(item)`. O replay usa dados capturados.
Em falha técnica, usa o motivo disponível na observação IPC para reconstruir
a auditoria da falha. Prazo, HTTP, despacho e custo são fatos da execução
que precisam da verificação externa. O campo de auditoria `refusal`
(string ou nulo) preserva `message.refusal` mesmo quando `raw_content` é nulo.

Injete `LunaTransport` histórico ou o wrapper financeiro que o chama, com
assinatura `transport(body: bytes, deadline: float, dispatched)` e retorno
`(status, response_bytes)`. Preserve `dispatched()` no instante em que o
transporte registra a possibilidade do único POST. Para orçamento, a
candidata exige `max_tokens=384`, `cost_unit` igual a `"USD"` ou `None`,
tarifa válida e `reserve(case_id, body_size)` e `observe(usage)`. O orçamento
real é obrigatório. A falha de reserva pode levantar `Blocked` do auxiliar
importado em `adapters.qwen.adapter` para virar erro IPC `adapter_error`.
Se a camada financeira usar `BudgetError` como parada do executor, mantenha
seu tratamento externo. A reserva ocorre antes de entregar ao transporte e
a candidata registra um uso por despacho, inclusive em HTTP 429 e timeout.
Quando houver `cost_unit=None`, use a conciliação exata do executor a partir
do corpo original. O float do IPC atende ao uso observacional. A chamada
`reserve` não recalcula o teto faturável com base nos 384 tokens pedidos.

## Provas executadas

- `python -m unittest adapters.luna.r5.test_evidence -v` no caminho de
  importação acima. 17 métodos passaram em 0,244 s, com vários pares e
  cenários por método. O processo de prova usou um audit hook que barrava
  eventos `socket.*` e aberturas dos caminhos reservados verificados.
- A primeira rodada encontrou cinco divergências nos padrões/expectativa
  de offset. Corrigi flexões, escopo e a expectativa do prefixo Unicode. A
  última rodada terminou sem falha.
- Compilei os três módulos Python em memória, li os três JSONs e verifiquei
  as seis referências com SHA-256 de `candidate.json`.
- `git diff --cached --check` antes do commit e `git diff HEAD^ HEAD --check`
  depois do commit passaram. Os 12 hashes originais do manifesto de
  congelamento R3 e os sete do R4 coincidem com SHA-256 dos blobs
  `git show HEAD:<caminho>`. A conferência usou apenas o mapa de fontes de
  runtime/semântica de cada manifesto.
- Falta avaliação independente, congelamento formal, executor R5,
  reprodução CLI, ensaio real autorizado e validação das metas do protocolo.

## Fontes a congelar e dependências de execução

Pins mínimos da candidata e do contexto usado:

| Arquivo | SHA-256 neste commit |
| --- | --- |
| `script/classification_comparison/adapters/luna/r5/adapter.py` | `8ac5c50ace54a58293bd63c4147a262a6dfbfcb566a2f5be2aac3f3eb5dfeecf` |
| `script/classification_comparison/adapters/luna/r5/candidate.json` | `e121574906d571ccab90911b70743c8e7e113dbefd6687e28b292f6726b54eb3` |
| `script/classification_comparison/adapters/luna/r5/evidence.py` | `dd9ee1e2d32f7b535460986696cfbf214d7913e9d664dadb7a8d7a5ddcf3c210` |
| `script/classification_comparison/adapters/luna/r5/evidence-envelope.schema.json` | `0964bbb9b065e03549ccc7a0f109bd6034f44344846d9b4481eb570a64ace1be` |
| `script/classification_comparison/adapters/luna/r5/operational.json` | `e1272d763e140633ed7bc9670d4b31c3dd181d1cdf7d58deeda77409424a3d21` |
| `script/classification_comparison/adapters/luna/r5/prompt.txt` | `fb4437c677a6b6eea2fb55d6fdebd7143b22c9738f273a561f4601cac38e1610` |
| `docs/planejamento/classificacao-comparativa/rubrica-comum.md` | `ac497f8d36af1aceb4eac39648ca7fe2c1e291d16cf512f27894b40e113ed4ac` |
| `script/f08/jev/catalog.json` | `14bbf6298ee8c6d5c9002128cd596e5250e71cbb0077e49a18fde49c265d2271` |

Auxiliares históricos que suportam o runtime e devem integrar os pins:

- `script/classification_comparison/adapters/luna/transport.py`
- `script/classification_comparison/adapters/qwen/adapter.py`
- `script/classification_comparison/adapters/qwen/transport.py`
- `script/classification_comparison/adapters/qwen/pilot.py`
- `script/classification_comparison/adapters/qwen/fixture.py`
- `script/classification_comparison/adapters/qwen/tarifas-publicas.json`
- `script/classification_comparison/common.py`
- `script/check_classification_contracts.py`
- `script/classification_comparison/metrics.py`, importado por C01
- `docs/planejamento/classificacao-comparativa/contratos/common.schema.json`
- `docs/planejamento/classificacao-comparativa/contratos/input.schema.json`
- `docs/planejamento/classificacao-comparativa/contratos/observation.schema.json`

Adicione os arquivos próprios do executor R5 e os pins da avaliação no
fechamento da frente B. O teste versionado `test_evidence.py` fica fora do
runtime. O exercício do documento técnico reproduz o veto com a mesma
citação e só uma mudança no restante do relato.

## Rodada de correção após revisão independente

A revisão analisou `065deee14b03e350a4d96a360cdca47b477519cd`. A rodada
dirigida foi concluída no commit `01eddbebfb416231eed8f13661460b34e59dd8bf`,
na mesma branch e worktree limpas. Este commit altera cinco arquivos, todos na
candidata R5 ou em sua documentação técnica. O adaptador, as assinaturas
públicas da candidata, o prompt e as versões do perfil permanecem os mesmos.

| Achado | Correção verificada |
| --- | --- |
| P1 · Consequência negada, resolvida ou com atendimento alternativo | Urgência por prazo requer consequência concreta e pendente ligada a tempo imediato. Retirada de uma multa invalida o recorte anterior. A alternativa operacional atual veta urgência por paralisação. Perda em curso, interrupção total sem alternativa e prazo com consequência afirmada continuam aceitos. |
| P1 · Rotina apesar de débito em curso | O padrão reconhece débito ou cobrança repetida. Dano presente impede a rotina. Continuidade descrita na própria oração ou referida na seguinte pode sustentar urgência. Orientação sem prejuízo continua elegível. |
| P1 · Assunto negado, incidental ou trocado | As construções separam o objeto da ação do sujeito da falha. O trecho tem de conter a mesma ocorrência que fornece suporte na oração completa. A política detecta negação direta de pedido e mudança de foco mesmo sem “minha dúvida é”. |
| P2 · Metadados de resposta sem despacho | O schema R5 proíbe corpo, término, recusa, procedência e registros de uso quando `requests=0`. O replay rejeita a adulteração e aceita os caminhos genuínos de timeout pré-despacho e pós-despacho. |
| Integração com o gate | O veto projeta `status=abstained`, `raw=informacao_insuficiente` e `reason=policy` na observação. A proposta real continua em `audit.fields.value` e `audit.raw_content`. Uma saída malformada continua falha técnica. Nenhum ajuste de gate, limiar ou gabarito. |

O reparo reconheceu as famílias de troca de bobina, falha isolada entre
equipamentos com atendimento remanescente, retrabalho integral e débito
repetido em curso. São construções conhecidas pela política. Interpretação de
escopo em frases ambíguas, elipses e relações fora dos padrões continua sujeita
a veto conservador ou erro semântico.

### Verificações da correção

- Os métodos adicionados reproduziram as falhas da implementação anterior.
  Depois do reparo, os **24 métodos sintéticos passaram** em 0,372 s com
  gateway injetado e audit hook bloqueando sockets e caminhos reservados.
  Exemplos de Pix não recebido, repasse não creditado e falha de impressão
  continuaram aceitos. A suíte também preservou erros técnicos, reserva antes
  do despacho, 429, timeout, uso e procedência.
- Rodei separadamente os **12 cenários independentes, com 14 propostas**,
  por classificação, replay e decisão comum. Todas produziram o efeito
  esperado. A correção recuperou o terminal do cenário 3 e as prioridades
  dos cenários 7, 8 e 9. A severidade do cenário 5, com alternativa atual,
  continuou vetada e agora ficou identificada como conflito de contexto.
- Compilei os três módulos e conferi os seis pins do manifesto. O diff
  local, o staged e o do commit passaram em `git diff --check`. Os
  SHA-256 dos blobs do HEAD coincidem com **12/12 pins R3** e **7/7 R4**.
- Avaliação da política nos cenários independentes e reprodução dos
  achados usaram respostas artificiais. A revisão dirigida, o freeze,
  a integração R5-B e eventual medição real ficam com o integrador.

### Pins a substituir na tabela do commit inicial

| Arquivo | SHA-256 em `01eddbe` |
| --- | --- |
| `script/classification_comparison/adapters/luna/r5/candidate.json` | `e3454d22deda0a629f8d289e1c6174cee8a2204e87c33d13e268e850103ef709` |
| `script/classification_comparison/adapters/luna/r5/evidence.py` | `c101dd712267de46177e2ffbc84ef9cdf57e77b6959904a5d69c1998699b81c9` |
| `script/classification_comparison/adapters/luna/r5/evidence-envelope.schema.json` | `c788f313a1c002f4c6e78b400a91120a2373d744184006b50725f91f7239f579` |

**Exercício.** No teste `test_falha_da_operacao_exige_o_sujeito_correto`,
compare o que muda quando a mesma citação “Pix não chegou” começa num
enunciado sobre o próprio Pix ou dentro do enunciado sobre seu adesivo.

## Segunda correção dirigida de polaridade

O P1 residual do commit `01eddbebfb416231eed8f13661460b34e59dd8bf` foi
tratado no commit `c233f0edc4a0646419409b2471088a21c880b282`, na mesma
branch e worktree limpas. O delta contém política, manifesto, testes e
documentação técnica da R5-A.

Um verificador de afirmação aplica o mesmo tratamento a consequência com
prazo, perda em curso, cobrança repetida, paralisação e falta de alternativa.
Perguntas, hipóteses gerais e negações no escopo anterior ao efeito deixam o
relato sem suporte para aquele efeito. Negações internas de uma construção
de falha continuam válidas, por exemplo “nenhuma venda passa”. Uma condição
operacional pendente reconhecida pode sustentar prazo quando seu consequente
explicita uma consequência imediata afirmada. O prazo já atendido segue
tratado pelo contexto.

A relação afirmada usada como suporte de urgência precisa estar no recorte.
Uma citação de consequência negada não recebe suporte de outra perda
afirmada na mesma oração. O veto de rotina por dano financeiro usa a
mesma verificação, preservando a checagem de falhas operacionais já
existente. Foco de categoria, envelope e despacho permanecem como na
primeira correção.

Os novos métodos reproduziram 17 falhas de subcaso antes do reparo. Depois,
os **27 métodos sintéticos passaram** em 0,459 s, com gateway injetado e
bloqueio de sockets e dos caminhos reservados verificados. Também rodei as
**14 propostas dos 12 cenários independentes** por classificação, replay
e decisão, com os resultados esperados. Compilei os três módulos e
confirmei os seis hashes do manifesto. Os SHA-256 no HEAD continuam iguais
a **12/12 pins R3** e **7/7 pins R4**. O diff passa em `git diff --check`.

| Arquivo com pin atualizado | SHA-256 em `c233f0e` |
| --- | --- |
| `script/classification_comparison/adapters/luna/r5/candidate.json` | `14cf412a5f46a15ed9b41a1e8e72c9d1a82016b09dfb7829ebff3f040ce3db94` |
| `script/classification_comparison/adapters/luna/r5/evidence.py` | `87f48d87976e7d380dd9d55dabb89a601ce48c1a1dc19530e9fecce07835728d` |

**Exercício.** Execute `test_urgencia_exige_afirmacao_do_efeito_em_cada_ramo`
e compare “Serei multado hoje” e “Hoje não serei multado”. Observe o ponto
em que começa o efeito, mesmo com a expressão de tempo antes dele.

As regras são conservadoras em escopos ambíguos. A prova é sintética.
A rechecagem independente e o congelamento formal ficam com o integrador.

## Terceira correção dirigida de escopo da pergunta

O P1 da segunda rechecagem foi tratado em
`53b11319c5450b7ab01bca64d98fb499f5fe9412`, sobre `c233f0e`, na mesma
branch e worktree limpas. O delta contém política, manifesto, testes e
documentação técnica da R5-A.

Na análise de prioridade, vírgula e dois-pontos podem delimitar uma
pergunta de orientação reconhecível. A interrogação dessa proposição
deixa de se aplicar à declaração de dano anterior. Uma dúvida sobre a
ocorrência do próprio dano mantém o veto de urgência. Se houver uma
possível afirmação de dano e a política não conseguir estabelecer a
fronteira, o campo vai para revisão mesmo quando a proposta for `basic`.
O caso sem dano continua elegível para rotina. As assinaturas, as
categorias, o envelope e os caminhos de despacho são os mesmos.

Os novos métodos reproduziram 15 falhas de subcaso antes do reparo. A
matriz testa perda em curso, débito repetido e multa afirmada com e sem
orientação posterior. A orientação é ligada por ponto, dois-pontos,
vírgula e ponto e vírgula. A matriz complementar cobre negação,
consulta, hipótese, controle sem dano e fronteira incerta com ou sem
pontuação. Depois do reparo, os **29 métodos sintéticos passaram**
em 0,704 s com gateway injetado e bloqueio de sockets e dos caminhos
reservados verificados. Em ensaio separado, as **14 propostas dos
12 cenários independentes** produziram os efeitos esperados por
classificação, replay e decisão.

Os três módulos compilam. Os seis hashes do manifesto conferem. Os
SHA-256 dos blobs no HEAD continuam iguais a **12/12 pins R3** e
**7/7 pins R4**. O diff do commit passou em `git diff --check`.

| Arquivo com pin atualizado | SHA-256 em `53b1131` |
| --- | --- |
| `script/classification_comparison/adapters/luna/r5/candidate.json` | `f01fa3c2e4f566765e2e38ce9755eb6781ba32e420ccf1ad97d833df598f67d9` |
| `script/classification_comparison/adapters/luna/r5/evidence.py` | `0a2c09f7d5429c2f0a5d140330f70e75257a14b264cb02482bccca9789d1c4eb` |

**Exercício.** Execute
`test_pergunta_de_orientacao_preserva_dano_afirmado_entre_pontuacoes`.
Compare o mesmo relato de perda antes de uma pergunta de configuração
com as quatro pontuações. Veja o veto a rotina no teste complementar
quando a fronteira não for reconhecível.

Essas verificações são sintéticas. A rechecagem independente e o
congelamento formal ficam com o integrador.
