# C04 — Classificar um relato de desenvolvimento com GLiClass local

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).

## O que construir

Como avaliador, executar `knowledgator/gliclass-multilang-mini` localmente e
produzir decisões pelo mesmo contrato e relatório usados no Qwen. Entregar uma
passagem reproduzível desde o relato até a evidência, com carregamento e consumo
de recursos identificados. O modelo inicial usa os pesos existentes, sem treino.

## Critérios de aceite

- [ ] Fixar revisão dos pesos, licença, dependências e procedimento de instalação,
  cache e carregamento. Registrar tamanho do artefato e dispositivo CPU/GPU.
- [ ] Usar o mesmo catálogo e descrições do protocolo, processar só campos
  faltantes e preservar os campos recebidos. Catálogo inválido não faz inferência.
  Mapear também os mesmos critérios de urgência, abstenção e eventuais exemplos
  de C01; registrar restrição de representação em vez de omitir informação.
- [ ] Converter decisões para o schema comum sem fabricar confiança calibrada.
  Política de score/abstenção é ajustada apenas em desenvolvimento/calibração,
  registrada e congelada antes de C05.
- [ ] Medir download/carregamento/cold start separadamente da inferência aquecida.
  Registrar latência total, amostra, RAM/CPU/GPU e concorrência da execução.
- [ ] Custo de chamada à API e custo local são conceitos distintos. Tempo e
  recursos ficam medidos; custo monetário de infraestrutura desconhecido fica
  indisponível, com qualquer estimativa devidamente identificada.
- [ ] Testes e piloto de desenvolvimento cobrem omissões simples/duplas,
  abstenção, inválidos e falha de carregamento/execução, usando o avaliador comum.
- [ ] O piloto real usa somente exemplos de desenvolvimento. Se o ambiente não
  suportar o modelo, registrar o bloqueio e as evidências sem inventar resultados.
- [ ] Uma configuração nova reproduz o piloto seguindo o guia. Entregar modelo,
  política e artefatos congelados para C05; não baixar pesos em cada atendimento.

## Fora do escopo

Fine-tuning, hospedar o serviço em produção, chamar a Feita, usar o holdout para
selecionar limiar ou modificar o código/schema da frente Qwen.

## Bloqueado por

- [C02 — avaliador comum integrado](C02-avaliador.md).
- Para piloto/ajustes: exemplos e política de desenvolvimento aprovados em C01.

## Execução e retorno

Papel: agente GLiClass. Ler AGENTS.md/especificação; receber o mesmo SHA de C02
usado por C03; branch/worktree próprias. Propriedade: adaptador local, runtime,
testes e guia próprios. Pilotos de recursos devem ser coordenados para não
concorrer com outro benchmark; implementação pode ser paralela com C03.
Retornar commits, comandos, modelo/revisão, recursos medidos e limitações.

## Exercício de aprendizagem

Comparar uma execução fria e uma aquecida e explicar qual tempo representa
melhor a inferência de um processo de demonstração já carregado.
