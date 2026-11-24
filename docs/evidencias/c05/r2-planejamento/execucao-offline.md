# SDD ledger — plan: docs/planejamento/classificacao-comparativa/rodada-2-implementacao.md

Contrato-base c00ac5431630c92d30349c13529d5071ad9879b4. Usuário escolheu A explicitamente, liberando implementação offline, sem chamadas pagas. Main é integrador, PDF excluído preexistente preservado.

## Preflight de interfaces

| Tarefas/interface | Produz / consome | Verificação e resolução |
| --- | --- | --- |
| Task1 própria | Prompt/política/candidate.json pinados → instrucões da API | Mesma rubrica/IPC/schema. Não testamos obediência de LLM por fixture. Nada de dados finais. |
| Task2 própria | 36 novos finais e gabarito exploratório → revisão sem candidato | Quotas fecham12por máscara,29+7,48alvos. Revisor e conferente novos; origemporIA clara; sem antigo conteúdo/saída no autor. |
| Task1 ↔ Task2 | Versão congelada e dados separados | Paths/worktrees disjuntos, candidate freeze antes de integrador abrir textos finais; sem fonte não commitada entre frentes. |
| Task1/2 ↔ Task3 | Candidata/dados aceitos → novo pacote/perfil R2 | Arquivos novos e fontes/locks. Task3 só começa na base integrada. Golden antigo não se torna R2. |
| Task3 própria | Dois stages6/36+13, gate, conta compartilhada → run/relatórios | Cronômetro/decide canônicos; não basta fixturepass para liberar real. Settings financeiros mantêm reserva/custo/timeout, sem conta real. |
| Task3 ↔ históricos | Mudança de seletores/módulos comuns → perfis antigos | Versão report1.3 distingueprotocolo1.2. Verificar históricossem mudarbytes, não confundir sourcepins com código atual. |
| Task4 ↔ demais | Relatórios/task reviews → CLI fixture/integrador/finalreview | Revisões por tarefa e uma ampla; alterações de código sempre pelo implementador. Zero rede/API paga. |

Ruling: execução paralela de Tasks1/2 em worktrees e ownerships disjuntos, como aprovado e requerido pela coordenação em paralelo. O limite do helper contra implementadores simultâneos evita conflitos no mesmo checkout; aqui o contrato comum e a separação de dados são verificáveis. Se errado, congelar a candidata e refazer o novo final sem exposição; nunca requalificar com dados contaminados.
Ruling: o helper writing-plans não está disponível no catálogo nem no diretório local pesquisado. O plano técnico foi escrito manualmente seguindo o desenho escolhido, com tarefas/aceites/ownership e preflight; não é motivo para pedir outra aprovação da mesma implementação offline. Se faltar uma invariante, revisar o contrato e o plano antes de consumi-los; nenhuma chamada paga é liberada por isso.

Task1: pending. Task2: pending. Task3: pending. Task4: pending. Sem parked findings.

Task1 em curso: /root/r2_instrucoes, Sol high, branch feat/r2-instrucoes-qwen, .worktrees/r2-qwen, basec00ac54. Task2 em curso: /root/r2_autor_dados, Sol high, docs/r2-protocolo-dados, .worktrees/r2-dados, basec00ac54. Ambas sem redes/chaves e paths disjuntos.

Ruling: o report development não declara elegibilidade do modelo; gate fixture_ready apenas libera final fixture, sem p95 de modelo fabricado. Real exige pass com seis durações observadas e os gates, com mode/conta/fontes equivalentes. Se errado, separar/proteger o gate antes do lote pago; nunca aceitar fixture como prova real.

Ruling: permitir keyword de scope esperado em Settings.load financeiro existente, default antigo intacto, para evitar duplicar validação financeira no R2; R2passac05-qwen-r2. Budget/schema4 não mudam. Se errado, refatorar composição do validador e repetir regressões financeiras antes de habilitar qualquer real.

Task1 implementada262d51c,3novosartefatos,JSON/hash/request3masks/diffcheckOK. Nenhuma inferência. Prompt1658bytes (antes239), custo/latência não medidos. TaskreviewfreshSolhighpendente; não congelar/abrir novos textos ainda.

Task 1: complete (c00ac54..262d51c, spec+quality approved,0findings). Candidata congelada em docs/evidencias/c05/r2-planejamento/candidate-freeze.json, SHAmanifestdb800577..., promptc03848e1..., polític a6893a119... ANTES de root abrir novos textos. Nenhuma mudança de instrução após isso; violação exige novo final. Task2 autoria29973d7, ainda não revisada.

Task2 em revisãoindependente: /root/r2_revisar_dados(Astrahigh), diffc00ac54..29973d7, brief/report; não recebe antigos60textos/candidate/saídas. Em paralelo /root/r2_similaridade(Solhigh), somenteid/text antigo+novo, semrótulos/outputs/prompt. Root agora tem candidata congelada e pode revisar achados de dados sem alterar prompt. Task3briefregenerado com fixture_ready/defaultscope; aindanãodespachada.

Task2labelreview /root/r2_revisar_dados(Astrahigh) aprovou48/48alvos/36casos,0disputas,referênciaexploratóriaIA; relatórioJSONtemhashde29a2de.... Similaridade preliminar10IDsrequeremadjudicação; aguardandoresultadoformalantesdespachofix. Task3pré-vooemleitura /root/r2_avaliador(Solhigh), semnovofinal/editsatébaseintegrada.

Task2: fix round1/5 pendente. Labelreviewapproved48/48 mas conferentesimilaridadeachou4paráfrases+6sobreposições, novosIDs001/007/014/019/020/022/023/030/031/033. Rootadjudicouquefatosespecíficos justificamsubstituição. Feedbacksanitizado próprio emtask-2-fix-1.md, semoldIDs/textos/outputsparaautor. 26objetosmantidos; candidataimutável. Re-reviewdirigidanos10apóscorreção e quotasglobais.

Task2 fixround1/5 implementado29973d7..96b9dfa,10textos/rationalesalterados26objetosintactos;rótulos/máscaras/cotasiguais,hash4f1d712b.... Validador/reprodução/diffpassaram. Re-reviewindependenteescopado nos10 +pins/quotas globais, conservarprovas26carryforward. Aguardando antes de integração.

Ruling: a CLI genérica C02 não executa R2; o checker continua aceitando. Impede um caminho de processo sem a guarda financeira exclusiva. Se errado, ajustar a fronteira/entrypoint antes do lote real, não relaxar guardas para caber num teste.

Ruling: replay por stage/candidato/final/conta será forte mesmo com novo config ougitrevision usando manifest_id determinístico pinado no authorize; aproveita UNIQUE manifest_id já transacional no ledger4 sem nova tabela ouserviço. Se errado, corrigir chave/serialização e repetir testes de replay/corrida antes de live; não reinicializar conta nem autorizar retentativa em prefixo.

Task2re-reviewrótulosround1 aprovou48/48/36casos no96b9dfa,0disputas. Similaridadepreliminar1resíduo r2-014 (mecanismoQRdesviodurantepagamentos), aguardandorelatorioformal parafixround2/5único, preservando35casos/candidata. R2dataset aindanãocongelado.

Task2: fixround1/5 encerrou9sobreposiçõesresolvidas/1aberta r2-014; rótulos48/48aprovados no96b. Conferênciaformal preservada comoevidênciaround1. Despachofixround2/5somente1text/rationale, semoldtextoparaautor e35objetosintactos.

Task2fixround2/5 implementado96b9dfa..9648208,sótext/rationaler2-014alterados35preservados,hash17f5bae3.... Verificaçõesglobais/reproduçãopassaram. Pacote review-96b9dfa..9648208.diff; próximosre-reviewslabel1alvo+similaridade1vs60,carryforward35.

Task 2: complete (c00ac54..9648208, round2/5, labels48/48spec+qualityapproved, similarity36/36approved,0open). Reviews/consolidatedpins/formaldatafreeze versionadosapóscongelamentoTask1. Task3podeconsumirnovabasecomdadosaceitos. Nenhuma inferência.

Task3 implementação emcurso /root/r2_avaliador(Solhigh), baseintegrada b299fdd1a9bc52d45bd46cd87a4a7a9583a6d115, branchfeat/r2-avaliador, .worktrees/r2-avaliador. Briefregenerado comguardasantesdosmodos; demaisTask1/2complete. Task3preflight estático preservado noSDD. Semnova API; root fará CLIfixture e taskreview/finalreview apósentrega.

Task3 entregue e6fe31cbe4dd2c96493bf455016163c6c68ff7dc,22files,134testsnovos/regressãopassaram,checkers3+21históricosbyteidênticos (18warm/3observed). RootinformouP2explica18warm. AutorCLI6+44fixture/50settled/.027350sintéticos,fixture_ready/p95unmeasured. Reporttask3comreceitareexecutada.Pacotereview-b299fdd..e6fe31c.diff gerado. TaskreviewfreshSolhighpendenteantesdeaceite.

Task3 taskreviewfreshSolhigh reprovou e6fe31c: P1 proofrewrite libera final apesar de6wrongsettled; P2 checkerR2não recompõe numeradores eaceita1→0deexpectedreview+pass; Minor splitdeclara fonteantiga/IDvisible. Contraprovas no reportforam executadas. Umafixround1/5consolidada serádespachada, preservadoreport/reviewinicial como evidência.

Ruling: ancorar saídas originais de development em selo JSONnãofinanceiroprivado junto da conta,O_EXCL+fsync, somentecaminho da conclusão original podecriar, inclusivefailed. Collector/verificador/final nunca reconstituem selo; perda/corrupção bloqueia. Budget/schema4intactos; semnovobilling. Se errado, ajustar atestação e testes antesde live; conservarconta/selos, não liberar resultado reemitido ou repetir estágio. Ameaça nãoincluiusuário com poderdeeditar programa/selo.

Task3 fixround1/5 9dfbc0d: 137tests/3checkers/21históricos passaram; re-review fechou P2/Minor mas P1 residual confirmado na conclusão antes do primeiro selo. Report task-3-re-review-round1.md. Round2/5 dirigida ao mesmo implementador: compromisso precisa derivar dos bytes originais produzidos, releitura pública só confere; sem alterar conta/budget/schema4/candidata/dados. ZeroAPI.

Task 3: complete (b299fdd..3f66bec, fixround2/5, SPEC+QUALITY aprovadas, zeroachadosabertos). P1 produtor/selo e P2 métricas reconstruídas fechados; Minor metadados fechado. Rodadafinal120testesafetados, anterior19contratossemalteração;3checkers/21históricos conferidos. Task4 CLI integrador3f66bec passou6+36/13/44fixture,50settled,2finished,fixture_ready,p95unmeasured,inconclusive,replayrecusado;zeroAPI. Revisão ampla final ainda pendente.

Ruling: o helper finishing-a-development-branch citado pelo fluxo não está disponível no catálogo nem nos dois diretórios locais de skills. Concluir manualmente revisão final, checagem de diff/status/ancestralidade e integração local já autorizada, preservando branches/worktrees e sem push. Se errado, corrigir a integração local antes de publicar; não inferir autorização de gasto, publicação ou exclusão de trabalho.
Task4 revisão ampla única /root/r2_revisao_final(Astrahigh), base ea318ed..1e98c45; pacote completo752784bytes. Código testado3f66bec, depois sódocs. 4documentos/33links locais conferidos, statusprincipal sóPDFpreexistente.

Task4 revisão ampla Astrahigh 1e98c45 exige uma onda final: P2 goldenR2com2requests/scoreinexistenteaceito; P3 approved/createdmetadataantigos e revisão do exemplo préperfil. FluxoCLI44correto. Escopofinalconsolidado em final-fix-brief.md, mesmoautor; re-review posterior dirigida, sem novaampla. Ruling: datas/evidência de24/11 sóautorizamAoffline, não rótuloshumanosnovos nemgasto; git_revision do exemplo deveexplicitarbaseverificávelR2semalegarexecuçãoreal. Seerrado, corrigiratribuiçãoantesdequalquerensaio, mantercandidato/dadoscongelados.

Task4 ondafinal b19a596: P2máximo1request/semScore e P3procedência corrigidos,23testescontrato/3checkers/21históricos/28pins passaram. Re-reviewAstrahigh final-re-review.md aprovouSPEC+QUALITY,0residuais. Integrador repetiuCLIfixtureapósalteração dochecker/fontes:6+36/13/44,50settled,2finished,replayrejeitado,fixture_ready/p95unmeasured/inconclusive,fonteb19a596,zeroAPI. Semnovaauditoriaampla.
Task 4: complete (preparaçãoofflineaceita,4tarefasconcluídas,0achadosabertos). Integração local e sincronização do tracker emfinalização; sempush, semnovaautorizaçãoAPI, C05aberta/C06bloqueada. Todosrulingspreservadosnoledger versãoevidência.
