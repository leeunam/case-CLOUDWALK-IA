# Instruções para agentes

Leia `/home/inteli/.codex/RTK.md` e use `rtk` nos comandos de terminal.

## Ao iniciar ou retomar uma tarefa

1. Leia este arquivo, `CONTEXT.md` e a tarefa correspondente em
   `docs/planejamento/plano-de-execucao.md`.
2. Consulte as regras pertinentes em `docs/planejamento/especificacao-mvp.md`
   e as decisões em `docs/planejamento/decisoes.md`. Preserve a distinção entre
   escolhas confirmadas e propostas.
3. Confira diretório atual, branch, alterações locais e worktrees existentes
   antes de editar. Preserve arquivos e alterações de outras tarefas.
4. Informe o ID da tarefa, o commit-base, a branch e o diretório de trabalho.

## Isolamento para implementação

- Cada frente de implementação usa uma worktree e uma branch próprias.
  Use a worktree que o integrador ou a ferramenta já preparou para a tarefa.
  Ao continuar a mesma tarefa, reutilize esse ambiente.
- Se ainda faltar um ambiente isolado, crie uma worktree a partir do commit-base
  informado pelo integrador, com branch `feat/<assunto-curto>` para código,
  testes e integrações, ou `docs/<assunto-curto>` para documentação, e diretório
  `.worktrees/<tarefa>-<agente>` na raiz do repositório principal. Confirme que
  esse caminho e essa branch estão livres antes de criar. Se já existirem,
  verifique a quem pertencem antes de reutilizar.
- Depois de criar a worktree, execute comandos e edições dentro dela. Alterações
  não commitadas de outro diretório precisam ser integradas à base antes de
  serem consumidas por outra frente.
- O checkout principal fica com o integrador para planejamento, revisão,
  bootstrap e integração. Revisões somente leitura podem usar esse checkout.
- Antes do primeiro commit, o integrador prepara a base no checkout principal.
  Após o commit inicial conter estas instruções e o planejamento, as tarefas
  de implementação podem criar suas worktrees. Selecione explicitamente os
  arquivos do commit e preserve arquivos de usuário alheios à tarefa.
- Siga o escopo e as dependências do ID recebido. Combine com o integrador as
  alterações em contratos, schema, configurações e transições compartilhadas
  antes de as outras frentes consumirem a mudança.
- Use Conventional Commits em português, como `feat:`, `fix:`, `docs:` e
  `test:`. Escolha o tipo do commit pelo conteúdo da mudança. Antes de publicar
  uma branch com outro nome, verifique as referências existentes e preserve
  o histórico e as revisões das MRs.

## Entrega e aprendizagem

- Faça a verificação prevista no aceite e registre o resultado real, incluindo
  falhas e verificações pendentes.
- Entregue ID da tarefa, branch, worktree, commit-base, alterações, testes
  executados e passos para reproduzir. A integração fica com o integrador.
- Explique em português a mudança e proponha um pequeno exercício ligado ao
  fluxo implementado para o responsável executar e entender o resultado.
- Este chat centraliza dúvidas de escopo, passagem entre agentes e revisão.
  Ao encaminhar trabalho a outra ferramenta, a mensagem inicial deve pedir
  explicitamente a leitura deste arquivo e indicar tarefa e commit-base.
