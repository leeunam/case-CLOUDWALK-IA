# C03 — Classificar um relato de desenvolvimento com Qwen pela Feita

Issue publicada: [#4](https://github.com/leeunam/case-CLOUDWALK-IA/issues/4). Consulte a issue para progresso e comentários atuais.

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).

## O que construir

Como avaliador, passar um relato pelo adaptador Feita/Qwen e obter a decisão
validada e o relatório do avaliador comum. Primeiro provar o fluxo com transporte
simulado; depois, quando liberado, executar um piloto pequeno de desenvolvimento.
O teste final é C05. O candidato inicial é `qwen/qwen3.8-27b`.

## Critérios de aceite

- [ ] Confirmar modelo, endpoint, capacidades, tarifa e formato de usage na Feita.
  Registrar data, solicitado/retornado e limitações; indisponibilidade é explícita.
- [ ] Enviar somente campos faltantes, com texto, critérios e catálogo da marca,
  exigindo valores permitidos e opção de informação insuficiente. Preservar as
  mesmas definições e exemplos semânticos oferecidos ao candidato local em C01.
- [ ] Validar a saída antes de agregá-la; preservar campos do canal e cumprir
  tudo-ou-revisão. JSON válido com código inventado continua inválido.
- [ ] Timeout, rate limit, resposta inválida, recusa e falha de transporte geram
  resultados rastreáveis. Limites/retentativas obedecem ao protocolo; nenhuma oculta.
- [ ] Registrar tokens cobrados, custo observado quando disponível e estimativa
  separada quando necessária. Sem usage/tarifa suficiente, não afirmar custo zero.
- [ ] Chave apenas no ambiente local, nunca em arquivos versionados, logs ou issues.
  Sem chave ou autorização/teto, o ensaio real para antes da chamada externa.
- [ ] Testes cobrem máscara simples/dupla, preservação, inválidos, abstenção e
  erros usando o avaliador comum. Saída de fixture é identificada como fixture.
- [ ] Com autorização, piloto limitado em exemplos de desenvolvimento gera
  artefatos reais. Se bloqueado, entregar implementação/testes e bloqueio preciso;
  não declarar aceite real concluído. Congelar prompt/versão para C05.

## Fora do escopo

Integrar no Rails, usar dados do teste final para ajustar prompt, treinar pesos,
criar chaves ou alterar o avaliador/schema comum sem combinar com o integrador.

## Bloqueado por

- [C02 — avaliador comum integrado](C02-avaliador.md).
- Para o piloto real: C01 com exemplos de desenvolvimento aprovados, credencial
  local configurada e autorização explícita de orçamento/limites.

## Execução e retorno

Papel: agente Qwen/Feita. SHA é o informado após C02; ler AGENTS.md/especificação
antes de criar sua branch/worktree. Propriedade: adaptador Qwen, seu prompt e
seus testes/guia. Pode rodar em paralelo com C04, sem editar seus arquivos.
Retornar commits, testes, artefatos, custo observado/indisponível e bloqueios.

## Exercício de aprendizagem

Ler uma requisição sintética e identificar quais tokens vêm dos critérios,
quais do relato e por que a categoria já fornecida não deve ser sobrescrita.
