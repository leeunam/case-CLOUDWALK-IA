# SF2-05A · tentativa de qualificação local

**Parecer inconclusivo.** O pré-voo passou. O supervisor iniciou o processo de
treino em 25/11/2026 às 20:59:51 UTC. Cerca de 2,45 s depois, o processo encerrou
com código 1, antes do registro de ajuste de categoria. O único diagnóstico
do worker foi `SF2 (PermissionError): [Errno 1] Operation not permitted`.
O log sintetiza a exceção e não identifica a operação negada.

A base foi `99885274faef5b5ee281ca4d87b9d840f85550ac`,
árvore `8944e7a0f2bd7c1e299a344eafb2ee0d12c24173`, na branch
`feat/sf2-qualificacao` e worktree `.worktrees/sf2-qualificacao`.

## Pré-voo conferido

- Manifesto público aceito com 150 relatos de treino e 90 de validação.
  O validador confirmou os bytes dos dados, das anotações e dos recibos.
- Os 240 comprimentos retokenizados reproduziram o inventário aceito,
  com 14 a 78 tokens. O limite da receita é 128.
- O selo público concordou com as contagens e os hashes do resumo de custódia.
  Os arquivos privados finais permaneceram sob custódia.
- O ambiente reutilizado passou na conferência de 73 pins, dos imports,
  do wheel PyTorch CPU, do `pip check` e dos dez arquivos do snapshot.
  A configuração observada foi 2 threads intra-op e 2 inter-op.
  Havia 11,66 GiB livres em disco e 5,05 GiB de memória disponível.
- O comando usou uma lista explícita de variáveis, modo offline e caches
  da worktree. Downloads e chamadas à API do classificador nesta passagem
  foram zero.

## Resultado e critérios pendentes

O [recibo do supervisor](status.json) registrou `failed` com
`exit_code=1`. A tentativa não produziu manifesto de pesos, provas de
ajuste ou convergência, duração acumulada de aprendizado, medidas de CPU/RAM
do treino nem verificações de reload. [Log integral](commands.log).

| Verificação | Resultado |
| --- | --- |
| Ajuste e exportação de categoria e prioridade | Sem artefato válido |
| Coleta dos 90 e controles | Pendente de pacote e reload, zero execuções |
| Acerto aplicado de categoria e prioridade | Sem medida |
| Preservação, zero chamadas dos controles e veto atômico | Sem medida |
| Revisão esperada e cobertura automática | Sem medida |
| Reconhecimento de urgentes e prioridade aplicada | Sem medida |
| Scores, 225 políticas e latência da validação | Sem medida |
| Congelamento, digest de liberação e lote final | Indisponíveis |

O parecer é de execução inconclusiva. C06 segue bloqueada.

## Rastreabilidade e reprodução da conferência

Os arquivos JSON e o log nesta pasta são cópias da execução original.
[preflight.json](preflight.json) identifica a base, os recursos, a lista de
variáveis e o `training_argv` completo. [launch-training.json](launch-training.json)
registra esse mesmo comando, o PID visto pelo executor e a localização da
saída; a CLI do supervisor produz [status.json](status.json) e
[commands.log](commands.log). A saída original fica no caminho
`script/classification_comparison/setfit_sf2/.cache/qualificacao-01/`
da worktree. Há somente o log e o recibo no subdiretório `training-01/`.

Confira primeiro os arquivos arquivados com
`rtk proxy sha256sum -c SHA256SUMS` a partir desta pasta.
`training-files.json` resolve cada papel de
[training-freeze.json](training-freeze.json). As fontes versionadas
podem ser lidas na base via `rtk git show <base>:<caminho>`.
`environment.json` guarda a revisão e os hashes dos arquivos usados,
além das versões instaladas. O manifesto do código foi produzido pela
CLI `training code-manifest`.

Para auditar o preparo, confira `prepare-preflight.py` e `launch-training.py`,
cópias dos roteiros operacionais. O primeiro exige a worktree limpa na base
indicada e usa apenas caminhos de dados públicos. Ele gera os argumentos,
congela os hashes e verifica os comprimentos com o tokenizador local. O segundo
confere o hash do recibo, cria um registro exclusivo da tentativa e executa
`training_argv` no ambiente registrado. Nesta passagem houve uma tentativa
do supervisor. Os roteiros ficam arquivados para inspeção da execução.

**Exercício.** Escolha `arguments` no arquivo `training-freeze.json`,
confira o hash de `arguments.json` e identifique a receita de cada campo.
Depois, compare o recibo de pré-voo com `status.json` para localizar a
etapa em que a evidência termina.
