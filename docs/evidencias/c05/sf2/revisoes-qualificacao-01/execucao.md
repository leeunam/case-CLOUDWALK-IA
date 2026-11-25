# SF2-05A · relatório da qualificação local

**Validação reprovada.** A execução concluiu um treino por campo, passou no
reload e registrou 90 relatos e 5 controles em uma única coleta de validação.
Os 120 vetores foram reaproveitados nas 225 políticas da grade. Nenhuma ficou elegível.
Até os maiores cortes concluíram pelo menos 2 casos com revisão obrigatória.
O conjunto final permanece selado. C06 segue bloqueada.

| Item | Registro |
| --- | --- |
| Tarefa | SF2-05A, executor independente de 03/04 |
| Base | `99885274faef5b5ee281ca4d87b9d840f85550ac` |
| Árvore da base | `8944e7a0f2bd7c1e299a344eafb2ee0d12c24173` |
| Branch | `feat/sf2-qualificacao` |
| Worktree | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-qualificacao` |
| Commit do lançamento interrompido | `5ff803fad83391ef8ddfe3a85cdde2663d318132` |
| HEAD da evidência | `4eb86a3282f94f32119042a0f6aa075e9f72960a` |
| Evidências | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-qualificacao/docs/evidencias/c05/sf2/qualificacao-01/` |
| Saídas originais | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-qualificacao/script/classification_comparison/setfit_sf2/.cache/qualificacao-01/` |

## Pré-voo e custódia

A worktree estava limpa na base estipulada. O verificador 03 confirmou o
Python 3.11, os 73 pins, os imports, a identidade do wheel CPU, as threads
2 intra-op e 2 inter-op e todos os 10 arquivos do snapshot. `pip check`
retornou `No broken requirements found.` A revisão do modelo de partida
é `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`.

Os contratos confirmaram o manifesto público e o `trainingFreeze` com os
150 relatos de treino, os 90 de validação, as anotações e os recibos reais.
Conferi as fontes versionadas byte a byte contra a base e o selo público
contra o resumo de custódia. A retokenização dos 240 relatos públicos
reproduziu o recibo, com 14 a 78 tokens incluindo especiais. O roteiro
auxiliar inicialmente consultou uma chave inexistente no recibo de
tokenização. Corrigi a consulta para conferir a revisão, com o snapshot
já verificado contra o lock, e repeti apenas as conferências determinísticas
antes do primeiro lançamento.

| Artefato | SHA-256 |
| --- | --- |
| Pré-voo 01 | `a91cef53ec003b14186a2dc41a23801239cd829ece718f8b71286d2ca2465ae4` |
| Pré-voo 02 | `0a2d353c03b1858f76e90d5a4d626f7db6b8a9b2072b876fa8f5d92825857da3` |
| Congelamento de pré-treino, comum aos lançamentos | `1a3a3baa405cf2cd45a15cc3e4ca3a0a654e6ac978f4d280c8b5cb301113112a` |
| Inventário das 16 fontes de treino | `599cda69dd60125dc5c55840dde7c4db3927b4029e9a417fc834f7ce254fb67b` |
| Argumentos aprovados | `27d1ed81103598cedb32118c824d0f6b6bdfca2deccf449754cc1e52c222b7f5` |
| Protocolo | `c0efd6d42ee50fd7775ff9db5ffcb9119db5861fd19c9b198b73ca01ce0eecaf` |
| Manifesto público | `36cbb5dab996775391a0c59802892a2b30d558fbf35b13e2620f0e7950d01ec9` |
| Selo público final | `71bea26395321246ef00c4374465c6cd8bd3320252a7729429cfad5e3c2263a4` |
| Ambiente | `d1372330105671e740d6c702b09f645867d7a09bd9edc60d66936b619739e06f` |

Enviei os hashes e o comando ao integrador antes de cada lançamento. Os
recibos `preflight.json` e `launch-training.json` guardam o comando completo
da CLI `training train`, cwd e ambiente explícito originado de `env -i`.
Os dois lançamentos usaram o snapshot pinado em leitura, modo offline e
caches da própria worktree. O pré-voo 01 registrou 11,66 GiB livres em
disco e 5,05 GiB de memória disponível. Antes do 02 havia 11,66 GiB livres
e 6,80 GiB de memória disponível. Nesta passagem houve zero downloads e
zero chamadas à API do classificador.

## Lançamentos e treino observado

**01.** PID 7 no ambiente do executor. Status `failed`, exit 1, de
`20:59:51.010375` até `20:59:53.463431` UTC. O log da execução contém
`SF2 (PermissionError): [Errno 1] Operation not permitted`.
Ele não identifica a operação negada. Não houve anúncio de ajuste de
categoria ou prioridade, que a fonte aceita imprime com flush antes
de entrar no ajuste, nem artefato de saída. Os 2,45 s medem a duração
do supervisor, sem medida acumulada de aprendizado nesta tentativa.

O integrador fez uma sonda separada de `socketpair()` e observou
`EPERM` no ambiente padrão e sucesso sob a permissão revisada.
A sonda demonstra a limitação do ambiente padrão, com causa exata da
exceção 01 ainda sem observação direta. O integrador autorizou um
novo lançamento com permissão para IPC local. Revalidei todos os hashes
vinculados ao congelamento. O argv 02 mudou só no diretório de saída.
O log e o status 01 permaneceram preservados.

**02.** PID 1398471. Status `complete`, exit 0. Início
`2026-11-25T21:02:05.154381+00:00`, fim
`2026-11-25T21:17:41.052504+00:00`. Aprendizado acumulado
**913,684538 s** de 1.800 s. O supervisor usa a soma
das duas janelas de ajuste, incluindo as cabeças. O worker registrou
933,755 s de parede, 1801,310 s de CPU e pico de 3.775.188 KiB de RAM.
O log contém um anúncio de ajuste para categoria e um para prioridade.
O modelo, a receita e os dados permaneceram fixos.

| Campo | Pares | Passos | Iterações da cabeça | Duração do ajuste do campo |
| --- | --- | --- | --- | --- |
| Categoria | 1500 | 188 | 23 | 428,434904 s |
| Prioridade | 1500 | 188 | 21 | 485,248129 s |

Os encoders partiram do mesmo peso monitorado
`78cf2f3362db15912cea1a37deb66237cc6636b9f5a031e260146e54ecaa2ed2`.
Depois do ajuste, os SHA-256 desse parâmetro foram
`9a32d9206bac4ccc63b958601e5b055e41ea9e9129a8e50f8ee45b25196c58e3` em
categoria e `d5e1815d451795d1bba8adc688dc13ad6a0fb8f0b9fb4dadb452c2c48abcddca`
em prioridade. Cada cabeça convergiu com a ordem de classes registrada.

- A cabeça de categoria usa a sequência `informacao_insuficiente`, `payouts`, `pix`, `terminal`.
- A cabeça de prioridade usa a sequência `advanced`, `basic`, `informacao_insuficiente`, `intermediate`, `urgent`.

O supervisor exportou os dois encoders em Safetensors, as cabeças locais
e seus inventários. O reload em três relatos públicos de treino por
campo reproduziu os seis vetores com erro absoluto máximo 0, contra
tolerância `1e-6`, mantendo argmax e motivos de decisão nos cortes.
O pré-voo de avaliação conferiu os 36 membros do pacote, as versões
efetivas, as configurações dos dois especialistas, a prova de reload e
os 17 membros do inventário do adaptador. O startup operacional foi
fixado em 60 s antes da coleta. O prazo por caso de 5.000 ms vem do protocolo.

| Registro | SHA-256 |
| --- | --- |
| Status 01 | `48ec924fa9f2d952200aae3bad57c1a450fa18fda31fd46eff0fc2d398022e24` |
| Log 01 | `1a368b912cd2d332160ae9aa12aa11fa9d7ad1ac7ae10eae6abd02b30c5d8eb5` |
| Status 02 | `aa6653736151f6cfcf8ba38498d316cff6451f795577df049993bfd22fdc0cbc` |
| Log 02 | `3fe60f151bf1beea66ebca3532e204ef3e2c1f4ce3028a632b1f15e867efc224` |
| Evidência 02 | `3e34e3d1010f671859f259351430783eef9030c463ef1d55b426c6128852e705` |
| Manifesto do pacote legítimo | `224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872` |
| Configuração da avaliação | `d59c7e18b3ff7d8e4eb6a662568897b1522855aae153feca3dae1f9316460832` |

## Uma coleta e uma extração dos frames

O comando `evaluation validate` iniciou às 21:17:59.782192 e
encerrou às 21:18:18.558552 UTC com `failed`, exit 1 por reprovação
dos critérios, stderr vazio. O selo não registrou interrupção. As 95
linhas do journal contêm uma passagem pelos 90 relatos mais os cinco
controles. Completo e inválido tiveram zero chamadas, categoria em
branco acionou só categoria, prioridade nula só prioridade e omissão
dos dois campos acionou os dois especialistas.

O extrator `training scores` leu os frames originais e o SHA-256 do selo,
exit 0. Os objetos JSON dos scores de 03 e 04 coincidem, contendo 60
vetores de categoria, 60 de prioridade e zero erros de score. Os hashes
dos arquivos são distintos por serialização. O replay de 225 políticas
foi calculado pela CLI 04 sobre esses vetores e não usou novas previsões.
A auditoria conferiu os quatro membros do selo, a correspondência entre a
captura e o pré-voo, os hashes do replay e a contagem das políticas.

| Evidência | SHA-256 |
| --- | --- |
| Frames originais | `d70ce59a1579a282f238dd37bdb154f1fa6500bc61e92299f49577255a1cbdab` |
| Selo dos frames e journal | `cb5d6bad2f0a7bb58492fc13710fef2102b283e34820cc9cd930c99bc2e8c985` |
| Tempos externos | `bfadaaf7b853f54f150d2d406dcac7fc5727f90672573c07350a92448d78a61e` |
| Scores 03 | `bccbfeb5e1ad9985a1a35ac05392dd215f91eedaa72e7adcf7309f969587051d` |
| Scores 04 | `59ae17e97256c55603d77a9d1850fdac56708a7fde7a4cf050136c4a3cb78c06` |
| Grade original descompactada | `d5315f425ed9e94e1680b99619a45ae7894c45c358fb819d0bc7bf2a3742c537` |
| Relatório 04 | `3dabedbf31424ea8820d2a5ebd54943b9f8b7e923459ee336483f4f830ab5ac5` |

A latência externa da coleta teve p50 de 60,82 ms, p95 de 177,61 ms e máximo de
254,01 ms, com 90 observações. O tempo até READY ficou em
9198,357 ms. O avaliador amostrou pico de 218,60% de CPU
do processo e 2.065.235.968 bytes de RAM. As medidas de latência
se referem à política fixa de coleta. O critério de latência do final
não foi medido.

## Critérios e leitura da grade

Em cada campo, a captura usou `tau=0,50` e `delta=0,00`. O relatório de
validação usa os resultados dessa coleta porque a grade não teve
vencedora. A última coluna conta, por critério, as políticas que o passaram.

| Critério | Meta | Coleta | Políticas que passaram |
| --- | --- | --- | --- |
| Preservação dos campos recebidos | 100% | 60/60 | 225/225 |
| Chamadas dos controles completos ou inválidos | 0 | 0 | 225/225 |
| Complementos parciais | 0 | 0 | 225/225 |
| Conclusões em revisão esperada | 0/18 | 3/18 | 0/225 |
| Urgente aplicado como não urgente | 0 | 1 | 135/225 |
| Acerto aplicado de categoria | ≥ 90% | 45/47 (95,74%) | 225/225 |
| Acerto aplicado de prioridade | ≥ 90% | 39/44 (88,64%) | 210/225 |
| Cobertura automática dos classificáveis | ≥ 51/72 | 67/72 (93,06%) | 180/225 |
| Urgentes reconhecidos na escolha bruta | ≥ 11/13 | 12/13 | 225/225 |

Na coleta, 11/13 urgentes foram efetivamente aplicados como urgentes.
A cobertura correta foi 63/72. Revisão por caso foi
20/90, e por campo `9/60` para categoria e
`14/60` para prioridade. As matrizes brutas, suporte, precisão,
recall, F1 e intervalos de Wilson por classe ficam em `report.json`.

As 90 políticas que passaram pelos demais critérios fizeram
2/18 conclusões indevidas em relatos de revisão. A cobertura correta
máxima nesse grupo foi 62/72. Na grade completa, as
135 políticas com duas conclusões indevidas cobriram de
46/72 a 62/72
casos classificáveis. As outras 90 fizeram três
conclusões indevidas. Nos maiores cortes para ambos os campos
(0,90 e 0,20), a prioridade chegou a 26/26 nos
complementos aplicados e o rebaixamento caiu a zero. A cobertura ficou
em 46/72, abaixo de 51/72, e
as duas conclusões indevidas persistiram.

| ID público | Campo | Rótulo de referência | Valor aplicado | Maior score | Margem |
| --- | --- | --- | --- | --- | --- |
| `sf2-validation-001` | Prioridade | `urgent` | `advanced` | 0,631387 | 0,290562 |
| `sf2-validation-028` | Prioridade | `informacao_insuficiente` | `basic` | 0,659234 | 0,335514 |
| `sf2-validation-030` | Categoria | `informacao_insuficiente` | `pix` | 0,902685 | 0,813941 |
| `sf2-validation-061` | Categoria | `informacao_insuficiente` | `pix` | 0,904549 | 0,817659 |

A categoria foi o único campo ausente nos dois casos `-030` e `-061`.
Os scores de `pix` ultrapassaram 0,90 e as margens ficaram acima de 0,20
nos dois casos. Por essa razão, nem o corte mais restritivo disponível
veta os complementos. No caso `-001`, o score de `urgent` no mesmo vetor
foi 0,340826. Os
vetores completos e os campos recebidos constam em `tradeoffs.json`.
A interpretação é sobre a política e os casos públicos. Os scores
da cabeça permanecem sem calibração como probabilidades de acerto.

## Reproduzir a conferência e limites

1. Na pasta `docs/evidencias/c05/sf2/qualificacao-01/` e depois em
   `execucao-02/`, execute `rtk proxy sha256sum -c SHA256SUMS`.
   Os 12 itens de pré-voo e os 53 da execução 02 passaram.
2. Na primeira pasta, use
   `rtk proxy gzip -dc execucao-02/avaliacao/validation/grid.json.gz | rtk proxy sha256sum`
   e compare ao hash da grade em `selection.json`.
3. Os recibos `*-launch.json` registram o comando, o cwd e os caminhos
   de entrada e saída. Para reextrair sem inferência, use o
   `training scores` registrado em `scores-launch.json` sobre os mesmos
   frames e uma saída nova. Compare os objetos sem exigir a mesma
   formatação JSON. Os roteiros da auditoria e do resumo apenas leem as
   evidências da validação e os rótulos públicos.
4. Confira os membros do pacote local pelos índices e manifesto. Os pesos,
   o ambiente e os logs integrais permanecem na área ignorada da
   worktree. `rtk git diff <base> HEAD --check` passou e o checkout terminou
   limpo. A entrega versionada contém apenas documentos e evidências
   públicas de desenvolvimento.

O pré-voo e o resultado se aplicam às versões locais e a dados sintéticos
em português. Os exemplos seguem quotas definidas e as anotações,
conciliações e revisões de dados vieram de IA. Os resultados não
demonstram generalização para tráfego real. Sem política elegível,
a etapa de congelamento não foi invocada e não existe digest de
liberação. O pacote privado final permaneceu fechado, sem leitura,
varredura ou execução nesta passagem.

**Exercício.** Siga `sf2-validation-030` nos frames e nos scores. Confira
o maior score e a margem. Identifique por que ele entra tanto no
denominador do acerto aplicado de categoria quanto no de revisão esperada.
