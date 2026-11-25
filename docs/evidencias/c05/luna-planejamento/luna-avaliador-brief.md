# Task3-B · Perfil Luna e executor offline integrado

Leia este brief primeiro; ele contém requisitos normativos. Leia AGENTS/RTK/CONTEXT.
Base integrada7f04b9b3b2e75c3db4993bcaf0ce82140a86f96f, branchfeat/avaliador-luna,
worktree /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r3-luna-avaliador
já preparada. F09/F10 estão integradas, mas fora de seu ownership. Usuário aprovou
D/Luna para preparação offline; nenhuma nova chamada paga.

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

Começar só na base com candidata congelada. Novo protocolo/vínculos/schema e
artefatos Luna; mínimo refactor interno de Plan/CLI/gate/settings/final_adapter
para descritor de rodada fixo. R2wrapper preservado e Lunawrapper dedicado em
script/classification_comparison/luna/. Bloquear perfil na CLIgenérica C02.
Reusar mesmos dados,controles,decide,relógio,financeiro e selo; modos distinguem
fixture_ready de passreal. Fixtures não qualificam o modelo nem fabricam p95.
Flags reais/examples permanecemfalse. Vincular toda fonte/código/conta, escolha
fixa do modelo, tarifa/limites e gate ao manifesto. Não relaxar teto/replay.
Testar fluxo6+44fixture,gatefailed,prefixo,erro técnico,custos conhecidos/desconhecidos,
replay/confignova/modocruzado,provas/métricasalteradas e integridade de fontes.
Regressões C02/C05/Qwen/R2 e checkers/históricos afetados sem editar seus bytes.
Report com comandos efetivos e pendências. Revisão por tarefa e integração local.


## Base congelada e interfaces aceitas

A candidata Task3-A foi revisada emcda8fc83d82cfc9c8cf4b746732fb11088edf751 e
congelada emdocs/evidencias/c05/luna-planejamento/candidate-freeze.json
(commit7f04b9b). O autor A nunca leu finais. Agora esta frente pode carregar o
pacote para checagem/fixtures, mas NÃO muda os textos, gabaritos, instruções,
parâmetros ou qualquer arquivo listado emruntime_and_semantic_sources_sha256.
A revisão histórica dos36 foi porIA,0/36humana. R3nãoalegaqueoldfreezedeQwenfoiLuna.

Manifesto Luna5chaves(incluirrubric). CandidateSHA1daac4749be2e8ac07989780ce5b4aae58f3f7f2bbbf460fdfb904a98295caf5,
operationalSHA0666cdd1c99f58c52512681563b72ddcaf4f97593071a1797104526d062678da.
Verreportversionado docs/evidencias/c05/luna-planejamento/luna-adaptador-report.md.
Interfaceestável:
`LunaAdapter(identity, run_id, instructions, transport, budget=None, timeout_ms=5000)`
classify(item)/close(); `LunaTransport(api_key)` callable(body,deadline,dispatched)/close.
Identidade real é a do manifesto; fixture muda apenasmode/provider parafixture/
simulador-c05-luna. Camposbudget max_tokens128/reasoningNone são auxiliares;
HTTPefetivoémax_completion_tokens128/reasoning_effortnone/streamfalse/schemaestrito.
RealexigebudgetválidoantesPOST. FixtureNone nãoatribuiestimativaQwen. Budgetpresente
exigetarifaválida. NãoeditarAparaadaptarsettings;usefacade/delegaçãopequena seprecisar,
semduplicarfinanceiro e semmudarRequestBudget/Qwenpilotcongelados.

**Fechar sempre gatewayemfinally**,mesmosecapture=functionsemclose. EOF,timeout,
interrupçãoprecisamrecolherfilho. Transporteconta erechecainício/callbackssíncronos,
mas otimeoutcanônicoexterno doC02 continua necessário. HTTPnão200preserva bytes
deusoantesdeerro. Apósobservation comstatuserror/invalid,nãodespacharnovocaso;
antesdaparadapreservareliquidarcustoconhecido. Custoausente/timeoutretémreserva
einterrompe;abstençãosemânticaavaliável podecontinuaratégate.

## Propriedade e desenho mínimo

Novo script/classification_comparison/luna/ comentrypoint/configs/descritordarodada
fixos; docs/planejamento/classificacao-comparativa/luna/ paraprotocol/binding e
contratos/relatorio-1.4/ (novosfontes/locks/examples). Refactorsmínimos compartilhados
emr2/{plan,execute,gate},c05/{settings,final_adapter},common/journal/metrics/run/checker
sóparareusoindispensável. Não modificarbudget.py/schema4 nemfreeze/candidata/runtimeA,
R2/históricos/fontes.Don'tduplicarCLI/gates/ledger. NãoUI/backend/deploy/README/integration.
Seoutrainterfacefornecessária,informeantes.

Um descritorinternode rodada porentrypoint(caller nãoselecionamodeloarbitrário)
derivaperfil,scope,provider,versions,candidate/operationalrefs,paths,manifestprefix,
settingsclass eadapterfactory. R2wrappereassinaturasdefaultspreservados. Imports
explícitos evitamcolisãoglobalplan/execute entrepastas. Verprévoo técnico versionado
no plano(seções2/3) paraacoplamentos concretos a eliminar. Report1.4próprio énecessário:
profile_for_report escolhe versão anteshashdoproto. ValidarR2packagecomseu
protocolooriginal, depoisR3bindings/equivalência. AlteraçõesdeaprovacaoDficamem
R3, não reescreveraprovacaoAdoR2.

Mesma conta real deveficar vinculada antesdekey/API: caminho canônico da conta
existente relativo ao checkout principal Git em
.worktrees/c05-comparacao/.superpowers/financial/c05-qwen/account-v4.sqlite3.
Fixturepodeusarqualquertemporário. Validar no modo real ocaminhoaprovadoexistente,
idexplícito,scope ecap10; nãoaceitaroutroarquivoparamontaroutrosUS10. VocêNÃOabre
essearquivo;testar comfakesearquivosfixture,preflightrealcomchaves/contasficapara
root. ManifestIDestável porconta,candidata/final/stage(padrãoJSONcanônicoR2)prefixoluna-.
Config/git/outputmudadosnãoliberamreplay. Gate/Selo atestamround/fontes originais.

Tarifaunknownnãoézero. Fixtureconfigs usarvaloresdeclaradamentesintéticos,válidos;
realexamples flagsfalse efontependente, sempromessade preço/coberturaconfirmada.
Configreal futura precisarátarifas/limites/referênciascomhash, incluindo cache e
contextolongoparareserva.A fonte oficialLunadizmaxinput922000/maxoutput128000;
Feitarotamostroucontext1.05M/maxoutput32K. Reserva de saída usa pelo menos128000
(e.g140000)epiorfaixade preçosfundamentada, nãosó128pedidos. A coleta decimal
bruta deveusarusage.credits x.01 sócomfonteconfirmada; costunitunknownnãoéUSD.
Manterusoreal/reserva/estimativaseparados eguarda dereferênciasha,semflagsTrue
vaziasliberaremreal. Prévoo depagamentorealrootposterior,nenhumSDK/keynova.

## Aceites e report

TesteLunaCLI fixturedevelopment6 e final36+13/44namesmacontatemp:50reservas
settled,fixture_ready,nocallreal,p95unmeasured/modelinconclusive. Testargatefailed,
prefixo,real/fixturecross,dados,candidate/account/config/proofrewrites,replay,
max1request/scorezero,metricnumeratorforged,knownfee-invalidresponse+stop,
timeout/unknownfee+hold,nosocketPOSTafterexpiry. Reusarjournal/canonicalmetrics.
ProvarCLIgenéricaC02negaLunaantesdesubprocesso oucredencial.

Depoisdebaserefactoring, rodarregressõesafetadasC02/C05/Qwen/R2 econtratos/checkers,
23LunaAdaptertests e todoshistóricos atuais(21anteriores+prefixorealR2), conferir
bytes contra base semmostrarcasesnoslogs. Não repetirsoquepassousemnovaalteração.
Nenhumarededofornecedor ou.env/personalconta. Não usar fixtures para elegibilidade.

Report completo em /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.superpowers/sdd/conclusao-projeto/luna-avaliador-report.md:
SHAs/interfaces/alterações/comandosefetivos/resultados/limitações,roteiroCLIfixture
reproduzidoecontagenscorretas,proposta depré-voorealqueaindaexigeautorização.
CommitselecionadoportuguêsConventional. Semsubagentes/merge/push. Retorno curto.
