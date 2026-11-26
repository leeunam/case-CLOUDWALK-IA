# C06/C07 · integração e reprodução com SetFit R1

**Estado em 26/11/2026.** C06, C07 e a publicação temporária com SetFit estão
aceitas. O serviço Python privado hospeda os dois especialistas e aplica a
política R1. O monólito Rails mantém o domínio e o atendente simulado responde
via Kafka. A C07 partiu de clone novo na revisão `89b9e68` e conferiu
três canais, isolamento de marcas e os mesmos históricos após reiniciar.
Após a revisão focal em `977ec3f`, o aceite externo verificou complemento,
acesso REST/WSS e resposta automática no navegador. O aceite por dados
móveis pertence à publicação F10 anterior com fixture.
[Aceite integrado C06](../../evidencias/c06/aceite-integrado/README.md) ·
[Reprodução C07](../../c07.md) ·
[Revisão final](../../evidencias/c06/revisao-final/README.md) ·
[Aceite público SetFit](../../c07-publicacao-setfit.md) ·
[Decisão e hashes](sf2/decisao-adocao-r1.md) ·
[Contrato HTTP normativo](../../contratos/classification-http/README.md).

## Ordem e interface compartilhada

1. O integrador revisa a documentação e comunica o SHA completo e imutável que contém a adoção e esta especificação para C06-A. Depois do aceite de A, publica um único SHA integrado para C06-B e C06-C. Ambas podem avançar em paralelo, em arquivos disjuntos, usando as fixtures de A.
2. Aprovar separadamente o cliente Rails e o serviço residente. Integrar A+B+C, executar o aceite real de C06 e só então passar a C07-D o SHA que contém também R01/R02. Disponibilizar os dois consumidores Kafka antes de começar a emitir requests 1.1. Ao reverter o provedor ativo, casos históricos SetFit e mensagens retidas ainda exigem leitores das duas versões.
3. Cada passagem pede expressamente ler `AGENTS.md`, `CONTEXT.md`, o card e esta especificação. Informar ID, SHA de base, branch e diretório antes de editar. Usar worktree própria já preparada ou verificar disponibilidade antes de criá-la, preservar mudanças alheias, entregar commits selecionados, evidências e resultado real de cada aceite. Apenas o integrador incorpora as frentes. A execução local não requer push ou merge pelo agente.
4. Usar dados sintéticos de produto próprios nas quatro frentes. O final já consumiu sua exposição. Relatos, gabaritos e observações individuais do ensaio permanecem na custódia. Preservar os pesos, as duas políticas, o núcleo R1 e os hashes das 17 fontes originais do worker. O aceite usa essas identidades, sem retreino nem busca de cortes.

A publica `docs/contratos/classification-http/{v1.json,pins.json,fixtures/}` e o vetor de catálogo. Rails e Python leem essa pasta por `CLASSIFICATION_CONTRACT_DIR`, com padrão relativo à raiz do repositório. O serviço usa `POST /internal/classification/v1/complete`, versão `classification-http/1.0`. A documenta a seleção das definições do schema para pedido, resposta e erros no README do contrato junto das fixtures. O contrato fixa os hashes aceitos e a serialização Ruby/Python. Os códigos, enums, limites de bytes, prazos e semântica de repetição são os da [norma HTTP](../../contratos/classification-http/README.md).

## Task 1: C06-A · contratos e consumidores compatíveis

**Posse e base.** `feat/setfit-contratos`, `.worktrees/c06-contratos`, a partir do SHA que
registra a adoção. Possui `docs/contratos/`, `script/check_contracts.rb`,
`backend/app/services/agent_integration/queue_turn.rb`, projeções REST em controllers/serializadores quando necessárias,
`integration/{agent_flow,test_agent_flow}.py`, `frontend/src/api/contract.ts` e
`frontend/src/staff/{CaseContext.tsx,blockingReason.ts}` e seus testes.

**Entrega.** REST staff usa as mesmas rotas com schema 1.1 e origem `setfit` por campo.
Preservar fixtures históricas e mostrar na UI a origem por campo e o motivo da revisão. Kafka
aceita requests `1.0` e `1.1`. `QueueTurn` emite `1.1` se qualquer campo tem origem `setfit`,
inclusive em rodadas seguintes, e `1.0` nos demais casos. O mock fixa retorno `1.0`
explicitamente e preserva a referência ao request. Reentregas reutilizam corpo persistido e ID.
Chaves, HMAC, offsets e receipts mantêm o contrato. Para reverter, desativar a geração de novas
classificações SetFit e preservar consumidores das duas versões enquanto houver casos ou
mensagens capazes de produzir ou carregar `1.1`.

**Interface para B/C.** Fixar schema e fixtures compartilhadas para o HTTP privado
`POST /internal/classification/v1/complete`. O pedido tem `contract_version`, `id` da tentativa,
`text` da mensagem inicial, `received`, `catalog` e `catalog_version` da marca. A resposta `200`
identifica contrato, tentativa, versão e hash do catálogo, `outcome`, `applied`, `fields`,
`calls`, hashes de pacote, modelo, políticas e frame bruto, e duração monotônica. Fixar a
serialização comum do catálogo num vetor de teste Ruby/Python e usar os bytes exatos da linha
JSONL, incluindo LF, para o hash do frame. `422` representa violação do contrato, `503` é recusa
antes da admissão. Prazo vencido ou transporte interrompido sem prova de recusa segue para
revisão. O sidecar projeta para `sf2-ipc/1.0`, com versão semântica do catálogo distinta da
versão operacional da marca.

A materializa as definições fechadas da norma, incluindo pins do pacote, das duas cabeças, das duas políticas e do inventário qualificado. As fixtures públicas são sintéticas e incluem pedido e retorno de sucesso, revisão, erro, recusa por status (inclusive `422 text_out_of_scope`) e o vetor de catálogo de 449 bytes. O checker confere também invariantes relacionais que um JSON Schema isolado não expressa.

**Aceite.** Checker valida fixtures REST históricas e 1.1, request Kafka 1.0 e 1.1 e rejeição de
`setfit` em 1.0. Ponte e mock processam ambas as versões. O mock gera resultado 1.0 e conserva
IDs em reentrega. Testes e build do frontend cobrem origem mista, histórico Jev e revisão. A
demo ainda usa o provedor fixture nesta fatia.

## Task 2: C06-B · complemento e revisão no Rails

**Posse e base.** `feat/setfit-classificacao`, `.worktrees/c06-setfit`, a partir de A integrada.
Possui serviços, jobs e modelos de `classification/`, configuração das filas Solid Queue,
serviços de entrada, ativação e correção em `attendances/`, migração aditiva se necessária e
testes Rails do fluxo de classificação. Testes de emissão Kafka e de projeção REST da fatia A ficam com A. O cliente HTTP usa a interface de A e pode ser verificado com um servidor falso; B possui exclusivamente configuração de filas e alterações de persistência.

**Entrega.** Selecionar `CLASSIFICATION_PROVIDER=jev|setfit` (padrão `jev`), preservando os modos Jev existentes. No modo SetFit usar `SETFIT_URL=http://setfit:8080` e a pasta de contratos/pins de A. Expor `Classification::Result`
com os atributos existentes de status, classificação, issues, evidência, repetição e espera. Preservar a injeção de provedor nos testes de concorrência. `nil` e `""` significam ausência. Entrada completa
ou inválida, inclusive espaços sem código e tipos incorretos, gera zero chamadas. Complemento
exige catálogo compatível com os códigos e descrições canônicas aprovados. Incompatibilidade
leva a `unsupported_catalog` antes da inferência, inclusive quando o código fornecido é válido
no Rails. Casos já completos seguem o catálogo operacional da marca.

Fixar provedor do pedido e capturar catálogo/versão/hash, identificador da mensagem inicial, campos presentes e lease no claim, preservando locks
marca → caso → pedido. Pedidos pendentes antigos conservam o provedor de origem quando
recuperável. Se a origem for indeterminada na migração de modo, encerrar em revisão explícita.
Chamar HTTP fora da transação. Aplicar 5 s no sidecar, incluindo validação, e 6 s de prazo absoluto
no Ruby, abaixo do lease de 30 s. Para o caminho HTTP, repetir só após `503 busy|not_ready` validado que comprove recusa pré-admissão, no teto atual de duas tentativas. Todo `422`, inclusive `text_out_of_scope`, leva à revisão sem aplicação ou repetição. A recuperação de processo continua limitada pelo
mesmo teto. B possui a fila Solid Queue `classification_setfit`, com um processo de uma thread, e exclui essa fila dos consumidores gerais. Preservar o consumo da fila legada e a recuperação. A espera por vaga ocorre no PostgreSQL antes do claim. Se o processo Rails morrer após o envio, a recuperação pode iniciar outra tentativa sob o teto. A garantia durável é uma aplicação e uma rodada/outbox por ativação.

Na liquidação, conferir tentativa vigente, lease, status, versão da classificação, versão/hash
de catálogo e valores do canal sob lock. Aplicar todos os campos ausentes juntos, ativar fila e
gravar uma rodada/outbox na transação. Catálogo alterado leva a revisão. Lease vencido e
correção já aplicada impedem a aplicação tardia. Guardar evidência por tentativa com
identidades, hashes, contagens, motivos, scores brutos, margens, cortes e duração disponíveis,
preservando snapshot e primeira evidência. Usar `channel`, `jev`, `setfit` e `supervisor` por
campo. A auditoria referencia a tentativa sem duplicar o texto cru.

**Aceite.** Com PostgreSQL e provedor controlável, verificar entradas completa, inválida, um ou
dois ausentes, resposta parcial/abstenção, catálogo incompatível e mudança em voo,
reentrega/conflito, correção em voo e retorno após lease sem novo claim. Conferir campos,
auditoria e uma única rodada/outbox. Cobrir autorização do supervisor em uma marca e bloqueio na
outra, jobs legados e regressão em fixture. Rodar os testes de `classification_flow`,
`classification_concurrency`, `configuration_domain_races` e `attendance_flow`.

## Task 3: C06-C · sidecar residente e aceite integrado

**Posse e base.** `feat/setfit-sidecar`, `.worktrees/c06-sidecar`, a partir de A integrada.
Possui serviço HTTP e testes de transporte em novo módulo junto de
`script/classification_comparison/setfit_sf2/`, empacotamento e configuração da demo SetFit
local em `compose*.yml` e `script/demo.py`. Consome o worker congelado `setfit_sf2.adapter` e
`runtime_r1.{context,decision}`. O aceite real depende de B integrada.

**Entrega.** C monta `CLASSIFICATION_CONTRACT_DIR` para os consumidores e fornece, no overlay local, `CLASSIFICATION_PROVIDER=setfit` e `SETFIT_URL=http://setfit:8080`. Preparar build reproduzível com Python 3.11.13 e dependências CPU nas versões do congelamento, incluindo PyTorch 2.12.0+cpu, SetFit 1.2.0 e scikit-learn 1.8.0. Fixar a imagem de build CPU e as versões de dependências efetivamente usadas, construí-la em ambiente limpo e verificar carregamento e decisão na aplicação. Verificar origem, membros e hashes do pacote antes da desserialização Joblib. Publicar um procedimento de fornecimento local portátil do pacote aprovado (arquivo empacotado ou diretório exportado pelo custodiante, com manifesto e seus membros), fora do Git, com conferência a partir do digest independente da adoção. O operador fornece um caminho local escolhido durante a instalação, montado somente para leitura. O procedimento não pode depender dos caminhos absolutos de worktrees/cache da pesquisa nem de downloads de pesos anônimos.

Sidecar sem porta publicada, na rede privada do worker Rails, com pacote somente
leitura e identidades verificadas antes da carga. Manter um subprocesso JSONL residente e um
dono do pipe, com admissão serial e resposta `503 busy` sem fila interna. Aplicar 65.536 bytes tanto ao corpo de entrada como ao frame completo com LF, prazo interno de 5.000 ms incluindo verificação e 60.000 ms para partida. Esses limites de bytes são adicionais aos do IPC qualificado. Manter rede privada exclusiva entre worker Rails e serviço. Pesos e selos entram em modo somente leitura. Readiness exige
`READY` e identidades esperadas. Conferir os mesmos 17 arquivos e o núcleo R1 com os hashes da adoção. Validar a observação da coleta e usar `load_context`, `derive` e `verify` para a decisão aprovada, conservando o hash dos bytes do frame incluindo LF. Antes de admitir inferência, medir o máximo dos tokenizadores solicitados do pacote, verificados conforme pins, com a mesma configuração e tokens especiais do worker, sem truncar nem carregar outro encoder. Acima de 128 tokens com essa comprovação, devolver `422 text_out_of_scope` antes da escrita no pipe, sem inferência ou reinício. Na ausência dessa prova, o frame `too_long` que R1 recusa vira `502 invalid_worker_frame`, revisão sem aplicação nem repetição. Em EOF, frame inválido ou timeout, retirar prontidão, colher o filho
e reiniciar com tentativas limitadas. Uma sessão interrompida descarta frames tardios. A demo
local tem seleção explícita do modo real e preserva o fixture como padrão, inclusive na pilha
publicada.

**Aceite.** Com worker falso, provar duas chamadas no mesmo processo, apenas a cabeça do campo
ausente, saturação, timeout, ressincronização por reinício e rejeição de identidade/frame divergente. Com o tokenizador qualificado provar a fronteira de 128/129 tokens de cada cabeça solicitada. No excesso, conferir `422 text_out_of_scope`, zero escritas no pipe e o mesmo PID pronto para o próximo pedido. Sem prova da tokenização, injetar o frame recusado pelo R1 e exigir `502 invalid_worker_frame` e revisão sem aplicação. Com a integração aprovada, rodar cenários sintéticos do produto em projeto local
isolado, duas marcas e um worker residente. Confirmar fluxo direto, complemento por campo e dos
dois, revisão/correção, atraso induzido e reentrega, fila correta, uma rodada Kafka e resposta
visível. Registrar correlações, partida/reinício, tempos de fila, inferência, HTTP e Kafka,
CPU/RAM e contadores de saturação/retentativa da pilha. Repetir o roteiro em fixture para regressão. A evidência integrada é produzida após a incorporação de B e C, em SHA fornecido pelo integrador. A prova com worker falso em C pode ser concluída antes desse ponto.

## Task 4: C07-D · instalação limpa e reprodução independente

**Posse e base.** `feat/reproducao-setfit`, `.worktrees/c07-setfit`, a partir do SHA com C06,
R01 e R02 integradas e aceitas. Possui README, roteiro, verificadores de instalação e evidências
próprias da demo. Correções de runtime identificadas aqui retornam ao dono da fatia
correspondente.

**Entrega e aceite.** Outra pessoa instala a partir do guia num projeto local limpo. O guia
identifica revisão, pacote e política, requisitos medidos, catálogos compatíveis, configuração e diagnóstico de carga. Explicitar como obter o pacote qualificado junto do custodiante, receber o artefato portátil, passá-lo por caminho local à montagem somente leitura e verificar os hashes. O clone fornece o código e os identificadores. Se o pacote externo faltar, registrar a etapa real como bloqueada e mostrar a falha de readiness. O guia não deve depender de um checkout de agente, retreino, chave de provedor ou uma URL de pesos presumida. Repetir direto, complemento real, revisão/correção, resposta Kafka,
handoff e persistência após reinício. Usar três canais e demonstrar o isolamento de duas marcas.
Comprovar recuperação de consumidores R01 e verificação do analisador R02, preservando os
resultados históricos F08 e o aceite F10 fixture. Registrar comandos, correlações, resultados
reais e pendências, com evidências locais próprias. Referenciar o protocolo para uma futura
reprodução autorizada da comparação. A reprodução da demo usa dados sintéticos próprios. Registrar separadamente a regressão histórica em fixture, os ensaios controlados R01/R02 e a inferência real do operador. A hipótese de 10 mil conexões segue exploratória. E01, atendente conversacional real, é evolução opcional após o fechamento.

**Verificações reproduzíveis das frentes.** A executa o checker de contratos (`bundle exec ruby ../script/check_contracts.rb` em `backend/`), `python -m unittest test_agent_flow` em `integration/` e testes/build do frontend. B executa `bundle exec rails test test/integration/{classification_flow,classification_concurrency,configuration_domain_races,attendance_flow}_test.rb` com PostgreSQL em shell com expansão de chaves. C registra o comando do seu teste de transporte e os comandos reais da pilha isolada; D reproduz o roteiro no SHA liberado e registra o que observou, inclusive dependências externas. As verificações descritas aqui são critérios das respectivas entregas.

**Exercício.** Seguir uma categoria recebida e prioridade complementada e localizar as origens e
os IDs que ligam aceite do canal, classificação e resposta Kafka.
