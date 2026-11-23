# R01 — Recuperar o consumo após perda da associação ao grupo Kafka

Issue publicada: [#8](https://github.com/leeunam/case-CLOUDWALK-IA/issues/8). Consulte a issue para progresso e comentários atuais.

Estado: **aceita localmente**. Código integrado em `2eee42ef6f7d81ed161ea8154fa810b5da3e2272`.
O [relatório R01](../../../r01.md) registra revisão e ensaio final.

## Parent e especificação

[Quadro CLASS-001](../README.md). Regressão F07 exposta pela F08; independe da
escolha do classificador. Fonte no checkout: diagnóstico F08 dos consumidores.

## O que construir

Como cliente, continuar recebendo respostas depois da volta do Kafka mesmo se
um consumidor perder sua associação/atribuição no grupo. Reproduzir a falha
`UNKNOWN_MEMBER_ID` na confirmação de offset e implementar recuperação automática
com confirmação contígua e idempotência dos efeitos, sem intervenção silenciosa.

## Critérios de aceite

- [x] Regressão reproduz perda de associação após efeito aceito e antes de confirmar
  offset, incluindo exceção e erro retornado por partição. Não tratar todo erro
  do broker como recuperável; registrar classificação e causa.
- [x] Os dois consumidores envolvidos retomam atribuição válida ou são reiniciados
  automaticamente por uma política operacional explícita, preservando o contrato
  de consumo. Não confirmar como proprietário de uma partição perdida.
- [x] Um offset só avança depois do efeito aceito ou de uma publicação terminal
  confirmada, sem saltar lacunas. Confirmação ambígua permite reentrega com
  identidade/bytes estáveis e um único efeito persistido.
- [x] Confirmar a transferência de partição entre membros e o primeiro progresso
  confirmado após recuperação, com grupo/tópico/partição/offset nos diagnósticos.
- [x] Um ensaio real controlado com Kafka comprova recuperação e escoamento no
  prazo definido antes do ensaio, sem reinício manual para aprovar a rodada.
  A perda de associação/rebalanceamento exercitada precisa ter evidência, não
  apenas uma parada que eventualmente não percorreu o erro. Modelos/simuladores,
  parâmetros, intervenção e recursos ficam registrados.
- [x] Casos que já atingiram falha/timeout têm procedimento canônico de recuperação
  testado, sem aceitar resultado obsoleto nem sobrescrever atuação humana.
- [x] Publicar as novas evidências separadamente. Preservar a rodada histórica
  reprovada e não reinterpretar seus 1.204 casos falhos como atendidos.

## Fora do escopo

Trocar broker, ajustar prazo apenas para passar na meta, integrar classificador
novo ou corrigir simultaneamente o analisador de R02.

## Bloqueado por

Nenhum card de classificação. Pode iniciar na base local conhecida, com SHA
de partida explícito do integrador. Ensaio real é serial com outros benchmarks.

## Execução e retorno

Papel: agente de robustez. Ler AGENTS.md/contratos e diagnóstico; usar branch e
worktree próprias. Preservar ordem, auditoria e isolamento; combinar alterações
compartilhadas de Compose/contratos com o integrador. Retornar reprodução,
commits, testes e evidência real, incluindo qualquer limite ou intervenção.

## Exercício de aprendizagem

Explicar por que o efeito pode estar no banco enquanto seu offset ainda não
foi confirmado e por que reprocessar exige idempotência.
