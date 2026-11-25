# C05-R2 · Re-revisão da correção 1

- **SPEC · Reprovada.** A correção rejeita a adulteração posterior ao selo. Durante a conclusão, o selo ainda pode incorporar registros públicos que substituíram a saída original.
- **QUALITY · Reprovada.** O P1 continua aberto pela janela entre o encerramento financeiro e a coleta dos arquivos públicos. P2 e Minor fechados.
- Branch `feat/r2-avaliador`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r2-avaliador`. Revisão de `e6fe31c` a `9dfbc0d`, com base sincronizada `ef840a1`.

## P1 · Aberto no momento da conclusão

O executor publica o relatório e o evento `finished`, fecha o lote na conta e então chama `gate.collect` para reler o diretório público. O selo exclusivo é derivado dessa releitura. Assim, a proteção garante que o resultado apresentado permaneça igual depois do selo, mas a primeira gravação do selo ainda pode registrar dados substituídos. Referências em `script/classification_comparison/r2/execute.py:120`, `script/classification_comparison/r2/gate.py:74` e `script/classification_comparison/r2/seal.py:15`.

Confirmei em conta fixture temporária. O ponto de intervenção foi imediatamente depois da chamada original de `Account.close_run(finished=True)` e antes de `gate.collect` na execução que criou o selo. Usei um gancho de teste para agendar a troca nessa janela. A primeira observação produzida foi `pix` para `jev-004`. A intervenção mudou apenas os três arquivos públicos de observações, decisões e relatório para representar `payouts` e sua decisão correspondente. O gancho preservou o encerramento financeiro original. A troca manteve o diário e as seis reservas originais e ocorreu antes da existência do selo. O próprio executor registrou `fixture_ready` e 8/8 alvos no selo, e o pré-voo aceitou a prova. A etapa final ficou no pré-voo.

O cenário exige acesso de escrita aos arquivos públicos enquanto seu diretório ainda está sendo usado pela execução. A intervenção de teste controlou a ordem das operações. Ela não mediu a janela em processos independentes. A falha decorre da escolha do conteúdo a selar e permanece no modelo que preserva a integridade do programa, da conta e do selo privado.

O compromisso deve derivar dos dados originais produzidos pela execução. O encerramento deve confirmar a correspondência entre esses dados, os arquivos publicados e a prova antes de criar o selo. A releitura pública pode confirmar a publicação, com a autoridade do selo derivada da produção original. Preservar criação exclusiva, bloqueio por ausência do selo, unicidade de etapa e conta SQLite v4.

A contraprova original de adulteração depois do selo agora retorna `selo de development divergente`. O selo tem caminho derivado da conta e manifesto, criação exclusiva e permissões privadas. As rotas de coleta e verificação só leem a evidência. A falha remanescente fica na origem do compromisso durante a primeira gravação.

## P2 · Fechado

O checker R2 reconstrói gates, fatias, urgências, p50 e uso com os streams validados e as fontes congeladas. O veredito é verificado contra as métricas reconstruídas e a completude da evidência. A comparação adicional é específica do perfil R2. A contraprova original produziu `fail` e uma conclusão indevida. Com o numerador alterado para zero e o veredito para `pass`, o checker retornou `r2_metrics: gates`. Referência em `script/check_classification_contracts.py:623`.

## Minor · Fechado

O split identifica a versão 2.0.0 e o hash do pacote composto, com referência histórica mantida no protocolo. Os metadados separam envelope IPC com ID de contexto HTTP sem ID. O checker verifica a correspondência. Referências em `docs/planejamento/classificacao-comparativa/r2/split.json:2` e `script/check_classification_contracts.py:667`.

## Verificações desta revisão

Executei as duas contraprovas originais do parecer anterior e a verificação dirigida do ponto de conclusão descrita acima. A checagem de espaços e a comparação dos caminhos protegidos em relação a `ef840a1` retornaram código zero. A revisão usou o apêndice do implementador como registro das suítes, dos três checkers e dos 21 históricos. Os ensaios desta revisão foram offline em arquivos temporários, com conta fixture no cenário financeiro e zero chamadas externas.
