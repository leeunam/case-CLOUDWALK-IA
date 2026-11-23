# C06 — Encaminhar um atendimento pelo classificador escolhido

Issue publicada: [#7](https://github.com/leeunam/case-CLOUDWALK-IA/issues/7). Consulte a issue para progresso e comentários atuais.

Escopo vigente: integrar Qwen somente se C05 comprovar elegibilidade e o
responsável aprovar a adoção. Novos ajustes GLiClass foram encerrados nesta
entrega. O resultado histórico de C04 continua preservado; não é pré-requisito
de elegibilidade para C05.

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).

## O que construir

Como cliente e supervisor, abrir atendimento com campo ausente, acompanhar a
classificação real do modelo escolhido e receber resposta via Kafka ou revisão
com motivo. Integrar um classificador ativo por configuração ao fluxo existente,
preservando histórico, correção humana e autorização por marca.

## Critérios de aceite

- [ ] Antes da implementação, integrador fixa origem/proveniência e atualiza os
  contratos/fixtures/tipos consumidores em conjunto. Histórico Jev permanece
  interpretável; Qwen/GLiClass não são gravados falsamente com origem Jev.
- [ ] Com classificação completa ou entrada inválida, há zero inferências reais.
  Um campo ausente solicita só esse campo; dois ausentes seguem a política comum.
- [ ] Entrada válida com complemento concluído ativa a fila correta da marca,
  envia uma rodada pelo broker e recebe resposta consultável na interface.
- [ ] Abstenção, resposta inválida ou falha definitiva deixam revisão com motivo;
  supervisor corrige e encaminha uma única vez, com auditoria e origem corretas.
- [ ] Reentrega/idempotência, resultado tardio, versão/catálogo alterados e correção
  humana posterior preservam as regras existentes, sem aplicação indevida.
- [ ] Evidência registra provedor/modelo/política/latência/uso disponíveis sem exigir
  probabilidades inventadas. Timeout, lease e retentativas têm limites coerentes.
- [ ] Testes e passagem real cobrem ao menos os caminhos completo, complemento,
  revisão/correção e resultado tardio, incluindo isolamento entre duas marcas.
- [ ] Se o Qwen for elegível e sua adoção for aprovada, configurar somente
  credencial/rede permitidas. Contratos de webhooks
  e eventos Kafka não mudam incidentalmente.

## Fora do escopo

Troca de modelo por atendimento, fallback automático entre modelos, UI para
seleção de modelos, treinamento ou alteração de filas/capacidade/handoff.

## Bloqueado por

- [C05 — decisão humana com vencedor elegível](C05-decisao.md).
- Contrato de proveniência congelado pelo integrador; fechar C05 com resultado
  inconclusivo não libera esta tarefa.

## Execução e retorno

Papel: agente de integração F04/F05. Ler AGENTS.md/especificação; começar no SHA
contendo a decisão e as dependências integradas. Alterações compartilhadas em
schema/config/contratos são coordenadas centralmente antes de consumo paralelo.
Entregar commits, verificações reais, IDs de correlação e roteiro reproduzível.
Não alterar a configuração ativa de outra tarefa durante seus ensaios.

## Exercício de aprendizagem

Seguir um caso com categoria válida e prioridade ausente; apontar onde o canal
é preservado, onde o modelo decide e onde o Rails autoriza o envio pelo broker.
