# C06 — Encaminhar um atendimento pelo classificador escolhido

Issue publicada: [#7](https://github.com/leeunam/case-CLOUDWALK-IA/issues/7). Consulte a issue para progresso e comentários atuais.

A decisão de 26/11/2026 liberou a integração do SetFit R1 após o final independente e a auditoria. O trabalho segue C06-A → C06-B e C06-C. A reprodução C07-D depende do aceite integrado. [Adoção](../sf2/decisao-adocao-r1.md) · [Tarefas e bases](../c06-setfit-integracao.md).

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
  interpretável e novas inferências usam origem `setfit`.
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
- [ ] Serviço privado residente carrega o pacote local verificado, preserva as 17 fontes do worker e aplica a política R1 qualificada. O mock e a ponte leem as versões Kafka históricas e a nova antes de ativar a emissão.

## Fora do escopo

Troca de modelo por atendimento, fallback automático entre modelos, UI para
seleção de modelos, treinamento ou alteração de filas/capacidade/handoff.

## Dependências

A seleção em C05 foi concluída. C06-A começa no SHA integrado que contém a adoção. B e C dependem da base comum de contratos de A. [Contrato privado](../../../contratos/classification-http/README.md).

## Execução e retorno

Papel: agente de integração F04/F05. Ler AGENTS.md/especificação; começar no SHA
contendo a decisão e as dependências integradas. Alterações compartilhadas em
schema/config/contratos são coordenadas centralmente antes de consumo paralelo.
Entregar commits, verificações reais, IDs de correlação e roteiro reproduzível.
Não alterar a configuração ativa de outra tarefa durante seus ensaios.

## Exercício de aprendizagem

Seguir um caso com categoria válida e prioridade ausente; apontar onde o canal
é preservado, onde o modelo decide e onde o Rails autoriza o envio pelo broker.
