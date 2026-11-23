# C02 — Executar um lote fixture e produzir o relatório comparativo comum

Issue publicada: [#3](https://github.com/leeunam/case-CLOUDWALK-IA/issues/3). Consulte a issue para progresso e comentários atuais.

Estado: **aceita e integrada localmente** em `d8e09b62e42122e08e3c8edc7f3566dcdb82a173`.
O [relatório C02](../../../c02.md) registra 27 testes, revisão final e exemplo
reproduzido do código aceito. Esta entrega usa somente fixtures.

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).

## O que construir

Como avaliador, fornecer um conjunto validado e receber um relatório reproduzível
com resultados por campo, preservação, aplicação, revisão, erros, latência e
custo. Uma fixture determinística deve percorrer o mesmo contrato e agregador
que os adaptadores reais, sem chamar fornecedores. A execução é independente
de Rails, Kafka e da interface do help desk.

## Critérios de aceite

- [x] Validar schema, versão, catálogo, máscaras e hashes antes do lote; recusar
  entrada divergente sem gastar créditos. CLI documenta configuração e dry run.
- [x] Um lote fixture percorre entrada → adaptador → validação → decisão/aplicação
  → relatório JSON e legível, com inventário dos artefatos e comando de reprodução.
- [x] Campos recebidos são preservados e excluídos dos acertos produzidos pelo
  modelo. Escolha bruta, aplicação e estado de revisão têm contagens distintas.
- [x] Relatar urgentes corretamente separados, cobertura, abstenções corretas e
  indevidas, inválidos e erros, com denominadores por campo/máscara/estrato.
- [x] Sem latência/custo real, escrever não medido. Com medição parcial, manter
  erros e denominadores; indisponibilidade total não aparece como sucesso.
- [x] Registrar cada tentativa e origem da tarifa/usage. Oferecer limites de
  casos, concorrência e tentativas; modo fixture é o padrão seguro de teste.
- [x] Testes com dados controlados comprovam denominadores, tudo-ou-revisão,
  abstenção total, urgente rebaixado, falha total/parcial e evidência ausente.
- [x] Registrar resultado de cada adaptador por uma interface comum, incluindo
  o formato de invocação entre Ruby/Python, sem exigir parser Choice do Jev.
- [x] Integrar e publicar o commit-base do avaliador e exemplos antes de C03/C04.

## Fora do escopo

Integrar no webhook, escolher modelo, alterar pesos, executar o teste final
ou converter fixture em evidência da qualidade de um modelo real.

## Bloqueado por

- [C01 — protocolo aprovado](C01-protocolo.md).

## Execução e retorno

Papel: agente do avaliador. Ler AGENTS.md/especificação; receber do integrador
o SHA com C01 integrado; usar branch/worktree próprias e declarar esses dados.
Propriedade: avaliador comum e seus controles; não editar adaptadores de outra
frente nem contratos públicos. Mudança no schema congelado volta ao integrador
antes de ser consumida. Retornar commits, comandos, testes e um relatório fixture.

## Exercício de aprendizagem

Escolher um caso com uma escolha bruta correta e aplicação recusada; localizar
por que a resposta não conta como classificação automática aplicada.

## Manutenção aceita — 2026-11-23

Correções `0a910fa` e `4f96743`, integradas em `6c27eb6`, preservam observações/cobranças tardias e valores Unicode inválidos sem aplicar a classificação nem perder evidências. Suíte completa: 31 testes em 27,938 s, zero falhas ou erros; revisões dirigidas aprovadas. [Registro](../../../evidencias/c02/manutencao-integracao.json). Nenhuma mudança nos critérios, contratos ou autorização de gasto.
