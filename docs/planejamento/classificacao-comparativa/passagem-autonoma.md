# Passagem da execução autônoma · 23/11/2026

**Estado atual:** o responsável configurou a chave, autorizou até US$ 10 com mínimo de requisições, e o piloto real C03 usou uma chamada. Retornou `pix` + `urgent` corretamente em 1,826 s; o painel exibiu cobrança aproximada de US$ 0,000518. [Recibo](../../evidencias/c03/piloto-unitario-real.json). A decisão posterior de usar o tempo total da classificação foi implementada e integrada em `933836e`: selecionar explicitamente `--profile observed-total-1.1`, com p95 até 3.000 ms. Passaram 39 testes do avaliador; os 17 históricos conservaram seus hashes e nenhuma nova inferência foi feita. [Aceite](../../evidencias/latencia-total/avaliador-aceite.json).

**Atualização de escopo aprovada:** o responsável escolheu focar na avaliação
do Qwen e encerrar novos ajustes GLiClass nesta entrega. C04 conserva suas
evidências, sem aceite do modelo, e deixa de bloquear C05. C05 passa a qualificar
Qwen contra as metas aprovadas, sem alegar comparação pareada final.
[Plano e pré-voo](qualificacao-qwen.md). Na consulta pública de 23/11/2026,
a Feita exibiu `qwen/qwen3.8-27b` como `Down`; nenhuma inferência foi tentada.
Os 36 relatos continuam reservados, sem inferência. A execução aguarda
disponibilidade e adaptação/verificação do executor final e seu orçamento.
Nenhum modelo foi escolhido nem integrado ao Rails. C06/C07 continuam
dependentes de decisão elegível; F09/F10 e E01 mantêm suas dependências.

**Decisão técnica:** o relatório passou a 1.2 sob protocolo de qualidade 1.1, preservando o IPC 1.1 e os adaptadores. Isso permite verificar os resultados históricos pela regra original. Se essa divisão se mostrar inadequada, o custo será revisar o despacho dos perfis e seus metadados, sem reescrever as medições antigas.

O checkpoint abaixo descreve o estado anterior ao piloto e é preservado como histórico; suas antigas pendências de chave, teto e método de latência já foram resolvidas.

Base técnica integrada localmente: `93cdbd79cf318ffa4be8888a366a1368c06b250c`.
Este registro é um checkpoint; retomar pelo HEAD atual e conferir alterações e worktrees antes de editar. O código não foi enviado ao remoto. Os cards públicos foram atualizados separadamente.

| Frente | Estado e evidência |
| --- | --- |
| R01 | Aceita: consumidores recuperaram associação em cerca de 12 s no ensaio controlado. [Relatório](../../r01.md). |
| R02 | Aceita: 49 testes e históricos de carga preservados. [Relatório](../../r02.md). |
| C01 | Aceita: critérios/divisão 24/36 aprovados e proveniência do gabarito declarada. [Aceite](aceite-c01.md). |
| C02 | Aceita com manutenção integrada: 31 testes, diário, interrupções, cobrança conhecida e Unicode preservados. [Relatório](../../c02.md). |
| C03 | Implementação offline aceita, 24 testes e lote fixture de 24 relatos/13 controles revalidado. Piloto real bloqueado por credencial, teto e condições de faturamento. [Relatório](../../c03.md). |
| C04 | Código e investigação revisados: 29 testes sintéticos e dez lotes reais adicionais validados. Timeouts e rebaixamento de urgência observados; configuração não aceita para C05. [Relatório](../../c04.md). |
| C05 | Pendente: comparação real pareada, método de latência remota e decisão humana. Não houve inferência do holdout. |
| C06/C07 | Dependem de escolha elegível, contrato público de proveniência e integração. O experimento permanece separado do Rails. |
| F09/F10 | Reprodução final e publicação por URL pendentes. Infraestrutura e gastos não foram contratados. |
| E01 | Mantida para depois de F09 concluída e F10 publicada: atendente conversacional real, se houver tempo. [Issue 11](https://github.com/leeunam/case-CLOUDWALK-IA/issues/11). |

## O que a investigação GLiClass permite dizer

As descrições de rótulos melhoraram as três categorias iniciais, mas os lotes de 24 foram interrompidos cedo pelo prazo do worker. As decisões posteriores registram revisão sem novo forward. Em execução isolada, `jev-002` recebeu basic onde o esperado era urgent, com 4,061 s e categoria do canal preservada. `jev-003` expirou com dois campos, sem aplicação parcial, em 4,862 s. Cada lote isolado tem um relato e não completa a população dos lotes anteriores. Ranking alto não comprova probabilidade calibrada. Todas essas execuções são de desenvolvimento e inconclusivas para escolha final.

Não selecionar GLiClass para produção com essa evidência. Preservar configurações A/B/C/D, resultados negativos, 49 versões de runtime, revisão dos pesos e os limites. Um novo ajuste de política/hardware exige plano e registro próprios, sem usar o teste final para calibrar. A instalação limpa com o lock final ainda precisa ser executada.

## Retomada com o responsável

1. Preencher localmente `.env.feita.local`, na raiz do checkout principal, com `FEITA_API_KEY`. O arquivo está ignorado, foi preparado vazio com permissão 0600 e não é carregado automaticamente. Não enviar a chave ao chat.
2. Autorizar explicitamente um teto em dólares para o piloto Qwen: um relato de desenvolvimento e oito controles naturais, no máximo nove requisições, uma tentativa e concorrência um. Não houve consumo de créditos nesta execução.
3. O integrador confirma as condições de faturamento/limites, prepara um manifesto separado ligado aos hashes congelados e carrega a chave apenas no processo. A chave sozinha não habilita gasto.
4. Executar o piloto Qwen e revisar saída, identidade retornada, uso, latência e erros. O estado aquecido do fornecedor remoto continua desconhecido; discutir o método antes de C05, sem aprovar o gate por presunção.
5. Revisar com o responsável a viabilidade do candidato local e congelar o desenho do comparativo. C05 requer permissão e escopo próprios para os 36 reservados; a autorização de desenvolvimento não libera o teste final. O responsável escolhe o vencedor após as evidências. Nenhum candidato pode ser selecionado se não houver evidência suficiente.

Os modelos de autorização e piloto Qwen versionados continuam desabilitados e sem teto. O documento [autorização de piloto](autorizacao-de-piloto.md) explica os vínculos e limites.

## Ambientes preservados

C03 e C04 começaram na mesma base `56f74fbb0795ca95b2a08ee4f4069de9f7d50f74` e receberam a manutenção comum antes do aceite.

| Frente | Branch | Worktree | Revisão de código medida/revisada |
| --- | --- | --- | --- |
| C02 | `feat/avaliador-classificacao` | `.worktrees/c02-avaliador` | `4f967439d192b9eec63d8bcf404067d304e05bf8` |
| C03 | `feat/qwen-feita` | `.worktrees/c03-qwen` | `fe9f69f46d7e4d701e47154042e6a1af07f44047` |
| C04 | `feat/gliclass-local` | `.worktrees/c04-gliclass` | `bf837b38abc91f92bf17300eebe60be76adfff87` |

As dependências e pesos locais estão na worktree C04, fora do Git. A integração levou apenas código, documentação e evidências sintéticas. As worktrees foram preservadas para retomada. A exclusão local preexistente do PDF do enunciado não foi incluída em commit nem restaurada.

## Decisões técnicas tomadas durante a execução

1. **Proveniência explícita no contrato 1.1:** controles artificiais têm origem própria e não simulam identidade ou chamadas do candidato. Mantém as regras e os dados aprovados. Se essa escolha estiver inadequada, o custo é adaptar o formato técnico e seus consumidores. [Decisão](ajuste-de-proveniencia-c02.md).
2. **Autorização financeira por execução:** manifesto separado ligado ao protocolo/modelo/piloto por hashes, em vez de alterar o protocolo congelado para ligar gasto. Nenhum gasto foi autorizado. Se inadequado, o custo é revisar a configuração antes de um piloto. [Decisão](autorizacao-de-piloto.md).
3. **Contexto experimental de até 2048 tokens:** o valor 512 do encoder não foi presumido como teto arquitetural. O teste conservou o contexto completo, prazo e guarda de memória. O risco era falha por tempo/RAM, que deveria ser registrada. O contexto coube, mas a latência e os timeouts limitaram os resultados; isso não relaxa a meta de qualidade ou desempenho.

## Exercício para retomarmos juntos

No relatório C04, siga `jev-002` por entrada, observação e decisão. Identifique a categoria recebida, a prioridade prevista e a aplicada. Explique por que o ranking 0,952 não permite aprovar esse resultado. Depois repetiremos o mesmo rastreamento em um resultado real do Qwen, quando o piloto for autorizado.
