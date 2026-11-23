# Passagem dos cards para este chat ou outros chats

## Antes de delegar

O chat central é o integrador. Aqui ficam revisão dos rótulos, critérios de
aceitação, orçamento, contratos compartilhados, análise dos resultados e escolha
humana do classificador. O responsável pode estudar e executar qualquer card
neste mesmo chat; a separação abaixo serve para permitir trabalho independente.

Use o [quadro](README.md), a [especificação](especificacao.md) e o card inteiro.
A base fonte estudada é `cb9683179d713e7bcbfc95c54003dc30630ab7ad`. O SHA de
execução deve conter o planejamento aprovado e as dependências integradas.
O integrador informa esse SHA por extenso ao liberar o card; não usar uma
referência antiga só por estar impressa neste guia.

Os nomes abaixo são sugestões de ambientes a conferir/criar quando a tarefa
for liberada. Não foram criadas nove worktrees antecipadamente. Se uma branch
ou diretório já existir, verificar seu dono e reutilizar somente para retomar
a mesma tarefa, conforme AGENTS.md.

| Card | Branch sugerida | Worktree sugerida | Base necessária |
| --- | --- | --- | --- |
| C01 | `docs/protocolo-classificacao` | `.worktrees/c01-protocolo` | Planejamento atual. |
| C02 | `feat/avaliador-classificacao` | `.worktrees/c02-avaliador` | C01 aprovado e integrado. |
| C03 | `feat/qwen-feita` | `.worktrees/c03-qwen` | C02 integrado; mesma base de C04. |
| C04 | `feat/gliclass-local` | `.worktrees/c04-gliclass` | C02 integrado; mesma base de C03. |
| C05 | `docs/resultado-classificacao` | `.worktrees/c05-comparacao` | C03 e C04 integrados e aceitos. |
| C06 | `feat/classificador-selecionado` | `.worktrees/c06-integracao` | Decisão C05 e contrato de proveniência aprovados. |
| C07 | `feat/reproducao-classificacao` | `.worktrees/c07-reproducao` | C06, R01 e R02 integrados/aceitos. |
| R01 | `feat/recuperacao-consumidores` | `.worktrees/r01-kafka` | Planejamento e linha de base F08. |
| R02 | `feat/integridade-ensaio-f08` | `.worktrees/r02-analisador` | Planejamento e analisador F08 atual. |

## Limites de propriedade

Paths abaixo são áreas previstas para orientar a execução, não uma ordem de
criar estruturas vazias agora. Qualquer mudança de interface é integrada antes
de outros agentes consumirem seu novo formato.

- **C01:** especificação, rubrica, catálogo/dados revisados e schema/fixtures
  do experimento. Preservar contratos públicos existentes até C06.
- **C02:** avaliador comparativo independente, recomendado em
  `script/classification_comparison/`, e guia de uso. Definir pontos de extensão
  separados para adaptadores Qwen e GLiClass e congelar invocação/saída comum.
- **C03:** adaptador Qwen e seus exemplos/testes/guia nessa área própria.
- **C04:** adaptador GLiClass, dependências/runtime local e seus exemplos/testes/guia.
- **C05:** artefatos reais em diretório próprio de evidências e ADR da escolha;
  não editar os modelos/prompt/política congelados durante o teste final.
- **C06:** configuração, adaptador de produto, jobs e proveniência, com atualizações
  coordenadas de schema/fixtures/tipos. O avaliador não substitui o fluxo Rails.
- **C07:** documentação/runtime da demo e evidências de instalação limpa.
- **R01:** consumidores e regressão de recuperação; qualquer Compose compartilhado
  deve ser combinado com o integrador.
- **R02:** `script/f08/load/` e sua documentação/testes; não editar o novo avaliador
  de classificação nem apagar arquivos históricos de evidência.

## Mensagem de entrada de outro chat

O integrador deve preencher os cinco campos abaixo ao liberar o trabalho.
Não despachar esta mensagem com placeholders nem sem dependências aceitas.

```text
Leia primeiro AGENTS.md, CONTEXT.md e as instruções RTK indicadas no AGENTS.

Tarefa: <ID e título do card liberado>.
Commit-base: <SHA completo informado pelo integrador, com dependências integradas>.
Branch: <branch conferida/preparada para esta tarefa>.
Worktree: <caminho absoluto conferido/preparado para esta tarefa>.
Card: <caminho do Markdown ou URL da issue correspondente>.

Leia CLASS-SPEC-001 e o card inteiro. Confirme base, branch, diretório e
alterações locais antes de trabalhar. Reutilize o ambiente preparado; se
faltar, siga o isolamento do AGENTS.md. Preserve alterações de outras frentes.

Implemente somente o comportamento especificado e seus critérios de aceite.
Mudanças de contrato, schema ou configuração compartilhada voltam ao integrador
antes de outra frente consumi-las. Não escolha o vencedor pelo responsável.
Não use dados de teste para ajustar prompts/limiares. Não publique segredos.
Chamadas pagas exigem a liberação e os limites descritos no card; crédito
disponível e esta mensagem não substituem essa autorização.

Faça commits Conventional Commits em português. Não faça merge ou push.
Entregue tarefa/base/branch/worktree, commits, verificações realmente executadas,
resultado e evidências, passos de reprodução, bloqueios e o exercício do card.
A integração e as decisões humanas ficam no chat central.
```

## Estado e passagem de fase

Fluxo de cada card: **planejado → liberado → em execução → em revisão → aceito**.
Use **bloqueado** com motivo quando faltar dado, credencial, orçamento, base ou
ambiente. Informar uma limitação é diferente de concluir o aceite.

Somente o integrador libera a próxima etapa depois da revisão. C05 tem uma
condição adicional: aprovação humana de vencedor elegível; fechar um relatório
inconclusivo não libera automaticamente C06.

Um chat consegue continuar sem reler esta conversa quando possui card,
especificação, commit-base e ambiente corretos. O GitHub acompanha estado e
evidências; decisões normativas também entram no planejamento versionado.
Enquanto o código não estiver disponível no remoto, os chats precisam do
checkout local. Nenhuma chave é compartilhada entre chats por mensagem.
