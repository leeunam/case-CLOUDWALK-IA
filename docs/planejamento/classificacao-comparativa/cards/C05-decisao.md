# C05 — Publicar a comparação pareada e decidir o classificador

Issue publicada: [#6](https://github.com/leeunam/case-CLOUDWALK-IA/issues/6). Consulte a issue para progresso e comentários atuais.

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).

## O que construir

Como responsável, comparar resultados reais dos dois candidatos e registrar uma
decisão explicável. A execução final usa os mesmos relatos/catálogos/máscaras e
os limites já aprovados, com adaptadores/políticas congelados. O agente prepara
o relatório; a decisão operacional é do responsável neste chat.

## Critérios de aceite

- [ ] Antes do lote, conferir aprovações de rótulos e orçamento, hashes, versões,
  políticas, limites e ambiente. Bloquear preflight divergente sem consumir API.
- [ ] Executar o teste final pareado, preservando cada tentativa, erro, abstenção,
  denominador e modelo efetivo. Não ajustar os candidatos ao ver o holdout.
- [ ] Publicar acerto bruto/aplicado por campo, urgentes rebaixados/abstenções/
  falhas, cobertura, inválidos, p50/p95 com amostras e custo real/estimado/local.
- [ ] Separar latência local fria/aquecida e chamada remota; documentar hardware,
  rede e condições. Modelos no mesmo host não têm benchmarks concorrentes.
- [ ] Relatório inclui dados brutos, hashes/inventário e instruções de reprodução,
  com checagem independente das contagens. Credenciais e saldo ficam ausentes.
- [ ] Relacionar os resultados aos limites definidos antes do ensaio. Não premiar
  um modelo que se abstém em todos os casos; expor trade-offs e tamanho da amostra.
- [ ] ADR registra resultado: vencedor elegível aprovado pelo responsável,
  nenhum elegível ou evidência insuficiente. Falha do piloto/fornecedor permanece
  visível. Não forçar uma escolha e não apresentar evidência sintética como produção.
- [ ] C06 só é liberada se houver vencedor elegível e aprovação humana explícita.
  Se não houver, registrar os próximos passos como nova decisão de escopo.

## Fora do escopo

Mudar prompts/limiares durante o teste, integrar o vencedor silenciosamente,
expandir a outros modelos, treinar pesos ou afirmar capacidade de dez mil chats.

## Bloqueado por

- [C03 — Qwen com piloto aceito e versão congelada](C03-qwen.md).
- [C04 — GLiClass com piloto aceito e versão congelada](C04-gliclass.md).
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
