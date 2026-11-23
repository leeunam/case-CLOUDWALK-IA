# C07 — Reproduzir a demonstração com o modelo selecionado

## Parent e especificação

[Quadro CLASS-001](../README.md) · [CLASS-SPEC-001](../especificacao.md).

## O que construir

Como avaliador, instalar a demonstração em ambiente limpo, seguir o guia e
reproduzir uma classificação real, uma revisão/correção e o atendimento via
Kafka. A apresentação explica por que o modelo foi escolhido e quais resultados
e limitações foram medidos. Esta é a passagem da comparação para a F09.

## Critérios de aceite

- [ ] README e roteiro identificam requisitos, configuração sem segredos, modo
  fixture versus real, custos/recursos, modelo/revisão, catálogos e política usada.
- [ ] Instalação limpa sobe a demo e executa inferência do vencedor com recurso
  documentado; carregamento dos pesos ou acesso à API tem falha diagnosticável.
- [ ] Percorrer classificação direta, complemento, revisão/correção, resposta
  via Kafka e handoff humano, mantendo isolamento e contexto/histórico.
- [ ] Evidenciar recuperação dos consumidores e correções do analisador após R01/R02.
  Novas evidências têm revisão própria; os resultados históricos F08 não são apagados.
- [ ] Outra pessoa consegue repetir a comparação seguindo os arquivos do projeto,
  respeitando orçamento e aprovação de dados. Relatórios fixture são identificados.
- [ ] Checklist apresenta apenas evidências realmente executadas e pendências
  remanescentes; não declara produção ou dez mil conexões sem medição correspondente.
- [ ] Registrar revisão usada, comandos, resultados, limitações e acessos locais
  sintéticos. A conclusão não inclui push, deploy ou contratação de infraestrutura.

## Fora do escopo

Publicação F10 em URL externa, compra de infraestrutura, novos modelos e nova
matriz de escala sem protocolo e recursos próprios.

## Bloqueado por

- [C06 — fluxo integrado](C06-integracao.md).
- [R01 — recuperação dos consumidores](R01-recuperacao.md).
- [R02 — confiabilidade da análise de carga](R02-analisador.md).

## Execução e retorno

Papel: agente de reprodução, com aceite central. Ler AGENTS.md/especificação;
o SHA precisa conter todas as dependências integradas, não apenas branches locais
separadas. Usar ambiente de teste próprio e limpar apenas seus recursos.
Retornar roteiro, comandos executados, evidências e um exercício para apresentação.

## Exercício de aprendizagem

Apresentar um caso de complemento e explicar a diferença entre aceitar a entrada,
classificá-la, responder ao cliente e comprovar recuperação após uma interrupção.
