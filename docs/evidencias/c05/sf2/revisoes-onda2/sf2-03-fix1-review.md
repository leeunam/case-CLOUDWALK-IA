# SF2-03 · Re-revisão da correção 1

**SPEC aprovada. QUALITY aprovada.** Os dois achados Important e o Minor estão **ADDRESSED**. Nenhum achado novo no diff da correção.

Base `d5819f7d47d16ed5394a224fa25fdeecf13e56d1`, entrega `420db5d3d618f6a43a43053161efa8ebb08ddff6`, branch `feat/sf2-treinamento`, worktree `.worktrees/sf2-treinamento`. As referências de linha abaixo partem de `script/classification_comparison/setfit_sf2/training/`.

## SPEC

**Important 1 · ADDRESSED — cancelamento e publicação.** Em `supervise.py:157`, a limpeza cobre staging e os destinos dos artefatos. O supervisor registra a reversão de cada destino antes de movê-lo (`supervise.py:166`). A saída só fica elegível com o recibo terminal. Em `supervise.py:47`, o supervisor bloqueia SIGTERM/SIGINT, consulta os sinais pendentes, considera também o sinal já registrado e troca o recibo por renomeação atômica. O corte para aceitar cancelamento é essa consulta protegida. Entre a consulta e a troca, um novo sinal permanece bloqueado e conta como posterior ao compromisso. O recibo torna o resultado visível após a troca. A limpeza só é desarmada depois do retorno de `commit()` (`supervise.py:171`).

As regressões em `test_supervise.py:98`, `test_supervise.py:126` e `test_supervise.py:151` cobrem as duas movimentações, a preparação do recibo, um sinal já pendente e um sinal posterior. Executei dois controles adicionais em diretório temporário para distinguir o corte lógico da operação em disco. Um SIGTERM gerado depois da consulta e imediatamente antes da renomeação permaneceu pendente sob a máscara, com retorno 0 e recibo `complete`. Uma falha de sistema de arquivos simulada na mesma renomeação retornou 1 e deixou apenas o log e o recibo `failed`. Pacote, evidência e staging foram revertidos nesse segundo caso.

**Important 2 · ADDRESSED — fontes efetivas do congelamento.** `environment.py:18` percorre cada inclusão de requisitos e retorna as versões e os arquivos de origem. `environment.py:41` usa esse resolvedor para verificar o ambiente. `fit.py:20` usa o mesmo resolvedor no inventário, que inclui os três arquivos de pins. `fit.py:23` inclui a inicialização e os quatro módulos de contrato usados no treino. `fit.py:34` compara o inventário recalculado ao congelado antes de aceitar as entradas. A regressão `test_package.py:28` altera separadamente, em cópias temporárias, os cinco módulos de contrato e os três arquivos de requisitos e exige a rejeição de cada divergência.

## QUALITY

**Minor 1 · ADDRESSED — recibo terminal para exceções inesperadas.** A exceção sai do contexto de reversão, entra no tratamento em `supervise.py:173` e gera recibo terminal com horário, estado e código diferente de zero em `supervise.py:182`. O supervisor propaga exceções inesperadas depois de gravar o diagnóstico. `test_supervise.py:170` percorre o caminho real de publicação com evidência sintética sem a chave de digest. A regressão exige `KeyError`, `failed/1`, horário final e ausência dos artefatos.

## Alcance

Revisei os cinco arquivos alterados no pacote da correção. Os 17 testes, a conferência de 73 pins e a verificação dos dez membros do snapshot são resultados reportados pelo autor. As duas verificações independentes acima usaram arquivos temporários e o supervisor, sem treino ou inferência. A integração com 04 e a execução de pesquisa em 05 continuam em seus respectivos aceites. Nenhum dado final reservado foi acessado.
