# C05 — Qualificar o Qwen e decidir sua adoção

Issue publicada: [#6](https://github.com/leeunam/case-CLOUDWALK-IA/issues/6). Consulte a issue para progresso e comentários atuais.

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).

## O que construir

Como responsável, verificar se o Qwen atende aos critérios aprovados e registrar
uma decisão explicável. O responsável aprovou encerrar novos ajustes do GLiClass
nesta entrega e focar no Qwen. A execução final usa os 36 relatos reservados,
catálogos, máscaras e limites já aprovados, com adaptador/prompt/política
congelados. O agente prepara o relatório; a decisão operacional é do responsável
neste chat. Não apresentar o resultado como comparação pareada final.

[Plano e pré-voo vigente](../qualificacao-qwen.md). A execução real aguarda
disponibilidade e controles de execução verificados; a consulta pública de
23/11/2026 exibiu o modelo como `Down`. Nenhuma chamada paga foi tentada nessa consulta.

## Critérios de aceite

- [ ] Antes do lote, conferir aprovações de rótulos e orçamento, hashes, versões,
  políticas, limites e ambiente. Bloquear preflight divergente sem consumir API.
- [ ] Executar a qualificação final do Qwen, preservando cada tentativa, erro,
  abstenção, denominador e modelo efetivo. Não ajustar o candidato ao ver o holdout.
- [ ] Publicar acerto bruto/aplicado por campo, urgentes rebaixados/abstenções/
  falhas, cobertura, inválidos, p50/p95 com amostras e custo real/estimado/local.
- [ ] Usar `observed-total-1.1`: p95 do tempo total da classificação até
  3.000 ms, incluindo falhas/timeouts observados e todos os estados térmicos.
  Registrar inicialização e estado térmico separadamente, além de hardware,
  rede e condições. Modelos no mesmo host não têm benchmarks concorrentes.
- [ ] Relatório inclui dados brutos, hashes/inventário e instruções de reprodução,
  com checagem independente das contagens. Credenciais e saldo ficam ausentes.
- [ ] Relacionar os resultados aos limites definidos antes do ensaio. Não premiar
  um modelo que se abstém em todos os casos; expor trade-offs e tamanho da amostra.
- [ ] ADR registra resultado: Qwen elegível e adoção aprovada pelo responsável,
  não elegível ou evidência insuficiente. Falha do piloto/fornecedor permanece
  visível. Não forçar uma escolha e não apresentar evidência sintética como produção.
- [ ] C06 só é liberada se houver vencedor elegível e aprovação humana explícita.
  Se não houver, registrar os próximos passos como nova decisão de escopo.

## Fora do escopo

Mudar prompts/limiares durante o teste, integrar o vencedor silenciosamente,
expandir a outros modelos, treinar pesos ou afirmar capacidade de dez mil chats.

## Bloqueado por

- [C03 — Qwen com piloto aceito e versão congelada](C03-qwen.md).
- C04 não bloqueia esta qualificação: sua investigação foi encerrada nesta entrega,
  preservando as limitações e evidências, por decisão do responsável.
- Gates de dados e execução real aprovados em C01.

## Execução e retorno

Papel: chat central com o responsável. Integrador fornece SHA contendo C02–C04
integradas; ler AGENTS.md/especificação e usar ambiente próprio para o ensaio.
Usar os rótulos congelados conforme a revisão autorizada em C01, declarando
oito aprovações diretas e 52 revisões por IA delegada. Não ajustar rótulos às
respostas dos candidatos. A escolha do vencedor continua com o responsável.
Retornar comandos, artefatos, gastos, limitações e ADR assinada pela decisão humana.

## Exercício de aprendizagem

Explicar por que o modelo com maior acerto pode ser inadequado se rebaixar
urgentes, e por que um modelo que revisa tudo não resolve o objetivo operacional.

## Pré-requisitos técnicos do ensaio final

O executor do piloto C03 aceita apenas desenvolvimento e controles. Sua
autorização não libera automaticamente os 36 relatos reservados. Depois do
piloto real aceito, preparar escopo e autorização próprios para o lote final,
vinculados aos IDs e hashes congelados, sem reutilizar a permissão do piloto.
A decisão posterior do responsável usa o tempo total da classificação, sem
exigir aquecimento comprovado. C01-L/C02-L foram aceitas e integradas em
`933836e`, com protocolo de qualidade 1.1, relatório 1.2 e IPC 1.1.
Selecionar explicitamente `--profile observed-total-1.1`; o default antigo
permanece apenas para reprodução histórica. [Método e aceite](../plano-latencia-total.md).
Os 39 testes do avaliador passaram e os 17 históricos conservaram os hashes,
sem novas chamadas de modelo. A fixture não comprova a meta de nenhum candidato.
Essa atualização técnica não inicia o ensaio final nem escolhe o vencedor.
