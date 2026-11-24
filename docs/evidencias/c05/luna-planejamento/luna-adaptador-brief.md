# Task3-A · Luna · Candidata e transporte sem finais

Leia primeiro este brief como fonte de requisitos e AGENTS.md/RTK/CONTEXT.
Base eaca1c6b64f407e628929023145d5cf1479973d2, branch feat/luna-feita,
worktree /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r3-luna-adaptador,
já preparada. O usuário aprovou D para preparação offline, semchamadaspagas.
F09/F10 operam em outras frentes. Esta é a fase anterior ao congelamento.

## Global Constraints (verbatim)

- Zero rede/API de IA, leitura de.env/chave/conta financeira real pelos agentes.
  Fixtures e contas temporárias somente. Sem push/subagentes/produção nesta frente.
- Modelo fixo `openai/gpt-5.6-luna` pela Feita. Providerreal `feita`, providerfixture
  `simulador-c05-luna`, adaptador1.0.0, semânticapolítica1.1.0 reutilizada.
  Uma chamada por caso apto; bypass completo/inválido e revisão integral.
  Sem scores inventados, exemplos/atalhos por ID ou segunda chamada.
- Reusar por SHA os bytes do prompt/política/rubrica R2, sem ajuste semântico.
  O cabeçalho Qwen na política é origem histórica; a fonte operacional nova
  explicita a identidade Luna. Operação nova: reasoning_effort=none,
  max_completion_tokens=128, stream=false, JSON Schema estrito só dos ausentes,
  sem temperatura/parâmetros não suportados. Fonte pública Feita e documentação
  oficial devem ficar registradas; nenhuma compatibilidade real presumida.
- Não ler/imprimir textos ou gabaritos dos36 finais (novos/antigos) ou outputs
  finais na frente da candidata. Até congelar, não executar preflight/Plan/
  suítes que carregam o pacote final inteiro. Entradas sintéticas isoladas e
  development permitido apenas. Candidata,operação e código usados ficam
  revisados e congelados antes de o integrador executar o perfil/final fixture.
- R2 e todos os históricos permanecem byte a byte. R3 usa perfil fixo
  `observed-total-luna-1.0`, protocoloqualidade1.3.0, relatório1.4.0, IPC1.1.0,
  vínculo de congelamento próprio apontando ao final R2 ainda não consumido.
  Não atribuir à Luna o congelamento Qwen nem aprovação humana dos36casos.
- Preservar métricas, cronômetro, seis IDs e limiares R2: development6casos/8alvos,
  corretos8/8,4/4fornecidos,3completos/3revisões,1urgente,0erro/timeout,
  todoscustosconciliados,p95≤3000ms(n6). Final36+13controles/44chamadas;
  acertoaplicado≥90%porcampo,cobertura≥21/29,revisãoindevida0/7,
  rebaixamentourgente0/6,reconhecimento≥5/6,preservação100%,parcialzero,
  p95total≤3000ms(n36),controles/startupseparados.
- Reusar c05/budget.py schema4 SEM mudanças, mesma conta global já existente
  e teto cumulativo10; não abrir/resetar conta real. Referência atual .02687405
  conservadora e sempendências. Novoescopo `c05-feita-luna`,manifestoprefixo
  `luna-`, IDestável por conta/candidata/final/stage. Guardas contra replay,
  prefixo, adulteração, origem/conta/modo cruzados e prova regenerada continuam.
- Selo não financeiro dos bytes originais, junto à conta; só conclusão original
  cria. Ausência/corrupção bloqueia final. Custo recebido conhecido é preservado
  e conciliado mesmo em erro; desconhecido/timeout conserva reserva e interrompe.
  Falha técnica encerra o lote sem outro POST; abstenção semântica pode seguir
  para ser avaliada pelo gate. Não liberar final porfixture_ready ou recibotardio.
- Transporte HTTPS persistente preguiçoso, sem retry/preconnect/HEAD. Primeira
  DNS/TLS/início do trabalhador dentro do relógio. Deadline monotônico total
  cobre DNS/TLS/leitura lenta inclusive conexão reaproveitada. Falha fecha canal
  e encerra sem reenviar. EOF fecha processofilho e não deixa trabalhador órfão.
- Branch/worktree/ownership distintos de F09/F10. Não tocar README/deploy/backend/
  frontend/integraçãoPython. Código comum só mínimo necessário, com defaults
  históricos preservados e interfaces coordenadas neste plano. Não duplicar
  executor,gates,metrics,ledger ou gerar uma plataforma de seleção de modelos.


## Sua tarefa (verbatim)

Ownership: novo script/classification_comparison/adapters/luna/ e extensão
mínima no adapters/qwen/adapter.py para um construtor de corpo fixo injetável
com default Qwen preservado. Nada de perfil/runner/dados finais nesta fatia.
Expor factory/classe Luna compatível com o Adapter existente, operando sobre
`classify(item)` e fechamento explícito do transporte; documentar assinatura
exata para Task3-B. Candidate.json segue contrato de identidade/prompt/política;
operational.json versiona corpo,conexão,parâmetros e política de falha.
Testes apenas envelopes artificiais e transporte duplo sem rede (reuso,deadline,
semretry,fechamento,uma chamada para dois campos,all-or-review,preservação).
Não executar suites históricas que carregam finais: o integrador fará depois.
Entregar commit+report, revisão independente e candidate-freeze com SHA dos
arquivos de runtime/manifesto/operação antes de prosseguir. Root escolhe e
registra o SHA-base integrado. Sem chamadas pagas.


## Interface e fronteira de dados

Não rodar common.preflight, qualquer Plan doR2 ou testes/checkers que carregam
os finais. Não abrir dataset/final-cases, golden com dadosfinais ou relatórios
reais finais. O integrador executará regressão ampla depois do congelamento.
Para testes construir envelopes artificiais e contratos isolados, sem rede.
As fontes de prompt/política/rubrica são as referências congeladas R2; pode
ler esses textos, nunca alterá-los. O cabeçalho histórico Qwen é registrado
como origem; nova operational.json explicita Luna, parâmetros e transportes.

Expor uma classe/factory Luna compatível com a interface do Adapter existente
para que a Task3-B apenas selecione a candidata fixa e gerencie close/EOF,
sem reescrever suas fontes congeladas. Se a mudança compartilhada ultrapassar
um hook pequeno de construtor do corpo, peça contexto antes de editar. Não
copiar toda a classe Qwen/RequestBudget. O vínculo financeiro/executor está
fora desta fase, mas a interface precisa aceitar o budget e transporte
injetável em fixture, com defaults históricos preservados.

Semimportarcarregar.env/chave/contareal. NenhumadespesaAPI/nemGET de sondagem.
Testes com chave artificial e conexão/processo duplos; não tocar contêineres
F09/F10 nem fazercarga. Não executarbarreirasdedados antes do freeze.
SeumentorC05-R3preflightestá disponível em .superpowers da raiz, seção1;
este brief e constraints normativas prevalecem sobre recomendações do parecer.

Report completo em /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.superpowers/sdd/conclusao-projeto/luna-adaptador-report.md:
base/branch/worktree/commit, interfaces exatas para próximo consumidor, arquivos,
SHAmanifesto/operação/código, testes sintéticos e limites, fontes de parâmetros,
comandos efetivamenteexecutados e exercício de uma chamada comdoiscampos.
Auto-revisar e fazercommitselecionadoportuguês ConventionalCommits. Não merge/push
nem subagentes. Retorne sóstatus/SHA/resumodetestes/preocupações. Revisãoindependente
fazparte da próxima etapa do integrador; aguarde depois da entrega.
