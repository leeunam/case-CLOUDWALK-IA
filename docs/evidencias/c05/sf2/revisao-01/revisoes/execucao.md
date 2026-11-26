# SF2-R1 Task 2 · execução e parecer

**Elegível somente na validação.** A execução autorizada de 45 políticas
adicionais terminou com código 0 e estado `eligible_validation_only`.
Nove políticas adicionais passaram pelos critérios de validação. A grade
histórica preservou 0/225 elegíveis e a união ficou com 9/270. A selecionada
pertence a `sf2-r1-offline/1.0`, com categoria tau 0,95 e delta 0 e
prioridade tau 0,70 e delta 0. O final e C06/C07 seguem bloqueados.

## Revisão e entrega

| Campo | Valor |
| --- | --- |
| Tarefa | SF2-R1 Task 2 |
| Base aprovada | `99cf2f33e1803838e33813d5c4ff46971181ce4e` |
| Referência histórica | `4eb86a3282f94f32119042a0f6aa075e9f72960a` |
| Branch | `feat/sf2-replay-r1` |
| Worktree | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-replay-r1` |
| HEAD | `53e3e87acfcf356c4a176b18d7763ed40d424d88` |
| Conteúdo do commit | Seis arquivos públicos em `docs/evidencias/c05/sf2/revisao-01/` |
| Estado após o commit | Worktree limpa |

O commit contém o relatório público, o recibo de pré-voo, o recibo
da execução com comando e timestamps, a tabela completa de 270 políticas
compactada, a política selecionada e o inventário de hashes. A saída
original ficou na pasta ignorada
`script/classification_comparison/setfit_sf2/.cache/revisao-01/result.json`
da worktree. O commit não inclui cache, modelos, pesos, arquivos do
aplicativo ou alteração da captura pública.

## Pré-voo, execução e conferências reais

1. Conferi a branch, a base, a referência histórica e a ausência do destino.
   Atestei os bytes do checkout e dos dois commits. As 30 fontes atuais e
   os 28 insumos conferiram com o Git aprovado. Conferi os 19 vínculos da
   captura histórica, as 17 fontes do adaptador e as 36 entradas de
   proveniência no manifesto público do pacote. O catálogo, o protocolo,
   o schema e o core históricos conferiram. A fonte histórica
   `evaluation/selection.py` foi atestada separadamente da refatoração
   aceita para o replay. Os modelos e o adaptador usados na SF2 mantêm a
   proveniência original.
2. A auditoria do selo validou 90 decisões, 5 controles e 95 registros de
   tempo. Os scores 03 e 04 coincidiram por objeto com os vetores
   reconstruídos dos frames, com 60 alvos por campo. Antes de lançar a CLI,
   reconstruí as 225 políticas com os mesmos objetos e os mesmos bytes da
   grade descomprimida, incluindo a baseline argmax e a seleção vazia.
   Até esse ponto, havia zero políticas adicionais avaliadas.
3. Na única rodada, usei o Python fixado 3.11.13 com `-I -B` e
   ambiente mínimo via `env -i`. Início
   `2026-11-26T01:15:58.665466871Z` e fim
   `2026-11-26T01:15:59.869860876Z`, em 25/11 no horário de São Paulo.
   A CLI retornou código 0, sem saída em stderr. O cálculo da extensão
   mediu 0,146553 s.
4. Conferi a saída preservada por leitura. Removido o campo derivado
   `failed_gates` para comparação, as 225 linhas e a baseline ficaram
   idênticas aos originais. As 45 políticas novas conferiram com o
   subcontrato offline e a união tem 270 combinações distintas. Recalculei
   os nove critérios e as razões de veto em todas as linhas, os
   denominadores, intervalos de Wilson e aritmética das estatísticas por
   classe. Reapliquei o desempate sobre as métricas. Conferi o SHA-256
   dos arquivos, a identidade dos bytes após descompressão, os links do
   README e `git diff --cached --check`.
5. As verificações acima usaram a captura pública e a saída preservada.
   Nenhuma suíte adicional de produto foi executada nesta task de
   avaliação. A revisão independente da entrega e a eventual integração
   das evidências pertencem ao integrador.

O primeiro utilitário de pré-voo parou antes de ler os insumos, pois o
`PATH` mínimo omitira o RTK. Usei o caminho absoluto do RTK para concluir o
pré-voo, antes da única execução da CLI. Durante a leitura inicial das
decisões do projeto, o intervalo consultado incluiu um resumo público de
outro fornecedor. Os insumos e cálculos da SF2-R1 usaram exclusivamente
os arquivos públicos previstos na emenda.

| SHA-256 | Digest |
| --- | --- |
| Emenda aprovada | `c3a6db8134f71491c1e743ddf6d57a400bba6449017b336e0a311c02f4eb07b3` |
| Inventário de fontes aceito | `f9199e3535f5504df2a1c9f11b317b526920d643a2653328fd5012f61eb8739e` |
| Grade original descomprimida | `d5315f425ed9e94e1680b99619a45ae7894c45c358fb819d0bc7bf2a3742c537` |
| Grade adicional | `dabccef501352f71bd7c6a9fa1ab085310191168f3f8704a4a10f00b0ac9bdd8` |
| União | `fcadb383aa2518639a266d291eb3874cadfbbd4744fa10fc1a8cad22af1d68cd` |
| Saída original, 1.302.449 bytes | `87be09aa73749c2c3ecf48e34e5584f703956476f88d67b818cf99fca59eb74a` |
| Saída arquivada, 33.868 bytes | `9fccc6f624ca477ef1b5bd3800c0c7b6a62cec774175d2e6ec65a7a788fbe702` |

## Métricas e motivos de veto

| Critério | Meta | Selecionada | Passaram originais | Passaram extras | Passaram união |
| --- | ---: | ---: | ---: | ---: | ---: |
| Preservação de campos de canal | 100% | 60/60 | 225/225 | 45/45 | 270/270 |
| Chamadas em controle completo ou inválido | 0 | 0 em 2 controles | 225/225 | 45/45 | 270/270 |
| Aplicações parciais | 0 | 0 em 90 relatos | 225/225 | 45/45 | 270/270 |
| Conclusões em revisão esperada | 0/18 | 0/18 | 0/225 | 27/45 | 27/270 |
| Rebaixamento de urgente | 0 | 0 em 13 alvos | 135/225 | 27/45 | 162/270 |
| Acerto aplicado de categoria | ≥90% com denominador positivo | 32/32 | 225/225 | 45/45 | 270/270 |
| Acerto aplicado de prioridade | ≥90% com denominador positivo | 33/33 | 210/225 | 45/45 | 255/270 |
| Cobertura automática | ≥51/72 | 51/72 | 180/225 | 27/45 | 207/270 |
| Urgente bruto | ≥11/13 | 12/13 | 225/225 | 45/45 | 270/270 |

A selecionada completou corretamente 51/72 classificáveis e encaminhou
39/90 relatos à revisão. O urgente aplicado corretamente ficou em 10/13.
Houve rejeição por campo de 24/60 alvos para categoria e 20/60 para
prioridade. Suporte bruto de categoria por classe foi Pix 17, repasse 16,
maquininha 17, informação insuficiente 10. Suporte de prioridade foi
básica 12, intermediária 13, avançada 12, urgente 13, informação
insuficiente 10. A tabela completa guarda matriz, suporte, precisão,
revocação, F1 e intervalos de Wilson para cada linha. Os intervalos
selecionados foram 89,28%–100% para categoria aplicada, 89,57%–100% para
prioridade aplicada e 59,49%–80,06% para cobertura automática.

Os dois controles de bloqueio, completo e inválido, registraram zero
chamadas. Os três controles de acionamento validaram categoria em branco
com uma chamada de categoria, prioridade nula com uma chamada de prioridade
e ambos omitidos com uma chamada de cada especialista. São registros
históricos auditados.

A política original comparável, categoria 0,90, prioridade 0,70, deltas
0, completava 2/18 casos que exigiam revisão, cobria 58/72 classificáveis,
acertava os 58/72 e encaminhava 30/90 relatos à revisão. Categoria 0,95
levou dois casos de revisão esperada e sete classificáveis adicionais à
revisão. As duas categorias insolúveis tinham scores 0,902685 e 0,904549
no topo. O urgente aplicado caiu de 11/13 para 10/13, e o urgente bruto
permaneceu em 12/13. Na captura histórica de tau 0,50 nos dois campos,
os números foram 3/18 conclusões em revisão, cobertura 67/72 e correta
63/72, 20/90 revisões, 12/13 urgentes brutos e 11/13 urgentes aplicados.

Das 45 extras, 18 com tau de prioridade 0,50 ou 0,60 completaram
indevidamente 1/18 casos e rebaixaram um urgente. Dezoito com tau de
prioridade 0,80 ou 0,90 eliminaram esses dois erros e ficaram abaixo da
meta de cobertura, com 46/72 ou 41/72. As nove com tau 0,70 tiveram
métricas idênticas, e a ordem original de desempate escolheu os deltas
zero. Os resultados históricos reprovados ficam preservados.

## Limites e reprodução da conferência

A extensão reaproveitou os vetores já gravados. Houve zero treino,
inferência, carregamento de pesos, chamadas de API ou exposição final.
Nenhum congelamento de política, autorização de final, adoção,
publicação ou mudança da demonstração foi produzido. O p95 observado de
177,61 ms, p50 de 60,82 ms, máximo de 254,01 ms e partida até READY
de 9,198 s pertencem à captura histórica. O tempo de 0,146553 s mede
apenas o cálculo da extensão. A meta de latência final p95 de 3.000 ms
segue pendente. A validação já tinha informado a escolha do corte 0,95,
e a amostra pública sintética limita a interpretação do ganho. Qualquer
qualificação final precisa de contrato de execução aprovado para esta
política, proveniência vinculada e autorização própria.

Na worktree da task, entre em `docs/evidencias/c05/sf2/revisao-01/` e
execute `rtk proxy sha256sum -c SHA256SUMS`. Compare o resultado de
`rtk proxy gzip -dc result.json.gz | rtk proxy sha256sum` com
`original_result_sha256` de `execution.json`. No JSON descompactado, a
lista `policies` contém 225 linhas originais seguidas das 45 extras, com
gates e vetos de cada linha. O recibo `execution.json` preserva o comando
da única execução, e as verificações acima usam somente os artefatos
gravados.

**Exercício.** Fixe prioridade tau 0,70 com deltas 0 nos dois campos.
Compare categoria tau 0,90 e 0,95 e calcule a diferença de revisão
`39 − 30` e a de cobertura correta `58 − 51`. Identifique quantos dos
nove relatos adicionais já exigiam revisão.
