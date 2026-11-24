# C05-R2 · Implementação offline da opção A

Spec: [desenho aprovado](rodada-2-proposta.md), emenda D017 e CLASS-SPEC-001.
Autorização: resposta do responsável «A — melhorar as instruções, uma chamada
(recomendado)», em 24/11/2026, à escolha que liberava somente implementação
offline. Base anterior ao contrato: `ea318ed1d07a878a35304d652458a2d2e5bd52e6`.
O integrador registra o SHA comum contendo este plano antes do despacho.

## Global Constraints

- Somente offline: zero chamadas ao fornecedor, nenhuma leitura de `.env`,
  chave ou conta financeira real pelos agentes. Sem Rails, Kafka, produção,
  fallback, nova prioridade, treinamento ou segunda chamada verificadora.
- Manter modelo `qwen/qwen3.8-27b`, uma chamada por caso, formato JSON e IPC
  1.1.0. Nova candidata: adaptador 1.2.0, prompt 1.1.0 e política 1.1.0.
  Não exigir palavra literal para classificar, inventar confiança numérica,
  exemplos finais ou exceções por ID. Catálogo e rubrica semântica existentes
  permanecem byte a byte; nova instrução deve implementá-los com mais clareza.
- Não alterar os bytes dos datasets, protocolos, prompts, políticas, schemas,
  exemplos e relatórios históricos. Pode adicionar perfil e testes em código
  compartilhado, mantendo seleção, decisões e cronômetro dos perfis anteriores.
  Conservar verificáveis os 17 históricos originais, os dois pilotos reais e o
  primeiro final. Não reciclar os 36 finais antigos.
- R2 final: 36 IDs `r2-001` a `r2-036`, 12 por máscara. Na máscara categoria:
  10 classificáveis + 2 com categoria insuficiente; na prioridade: 10
  classificáveis + 2 insuficientes; na dupla: 9 classificáveis + 3 com categoria
  insuficiente. Dos três duplos insuficientes, um tem prioridade urgent, um
  prioridade não urgente determinável e um prioridade insuficiente. Total
  29 classificáveis / 7 revisão; 5 alvos categoria insuficiente / 3 prioridade
  insuficiente, sobreposição 1. Seis urgentes com prioridade omitida: três na
  máscara prioridade, dois classificáveis duplos e o duplo ambíguo urgente.
- Manter limites: preservar 100% dos válidos; zero chamadas em entradas completas
  ou inválidas; zero aplicação parcial, zero conclusão automática nos 7 de
  revisão, zero urgente automaticamente rebaixado; acerto aplicado ≥90% por
  campo; cobertura ≥21/29; reconhecimento bruto urgente ≥5/6; p95 total
  nearest-rank ≤3.000 ms, n=36, incluindo erros/timeouts observados. Controles
  e startup separados. Nenhum score calibrado ou aprovação por fixture.
- R2 desenvolvimento: os 24 IDs antigos de development ficam idênticos no
  pacote novo; somente 6 são selecionados para o ensaio real futuro:
  `jev-004`, `jev-013`, `jev-002`, `jev-023`, `jev-006`, `jev-039`, nesta ordem.
  O gate exige 8/8 alvos corretos incluindo abstenções, 4/4 fornecidos
  preservados, 3 completos corretos / 3 revisão, 1/1 urgente, zero erro/invalid/
  timeout, todos os custos conciliáveis e p95 ≤3.000 ms (n=6, máximo).
- Manter 13 controles já definidos (8 naturais candidatos + 4 bypass + 1
  injetado). Desenvolvimento real não repete controles nem baseline; final
  tem até 44 chamadas. Total futuro até 50, sem retries/resume ou ajuste
  automático depois de resultados. Não há autorização de execução real R2.
- Pacote R2: 24 development preservados + 36 finais novos, total 60. O autor
  do final não lê antigos textos/saídas; a frente de prompt não lê novos finais.
  Referência exploratória criada e revisada por agentes diferentes antes de
  qualquer inferência, com origem declarada. Disputas de rótulo persistentes
  exigem o responsável. Conferente de similaridade é um terceiro papel, fora
  do prompt/autoria, sem outputs do Qwen. Separação operacional, sem alegação
  de ACL ou independência matemática.
- Nova avaliação: perfil `observed-total-r2`, protocolo de qualidade 1.2.0,
  relatório 1.3.0, IPC 1.1.0. Novos arquivos de fontes/locks; não rebater fontes
  antigas ou fazer relatório antigo parecer R2. O cronômetro canônico e a
  regra all-or-review permanecem.
- Reutilizar conta SQLite v4 do escopo global com teto US$10, nunca inicializar
  conta real nesta entrega. Gasto anterior conhecido US$0,02300927, apenas como
  referência auditada, não como saldo externo ou autorização. Importar/reusar
  a proteção financeira C05; não reescrever `c05/budget.py` nem sua schema.
  Fixtures usam conta temporária mode=fixture. Reserva antes do despacho,
  evidência monetária independente da classificação, timeout/desconhecido
  retém e interrompe. Exemplos reais/manifestos começam desabilitados.
- Branch e worktree exclusivas por frente. Não editar main nem consumir
  alterações não commitadas de outra worktree. Sem push. Commits selecionados
  em português/Conventional Commits. Não tocar na exclusão preexistente do PDF.

## Sequência e propriedade

Tasks 1 e 2 podem andar em paralelo em worktrees disjuntas; os requisitos
compartilhados estão acima. A candidata é revisada e congelada antes de o
integrador abrir os novos textos. Task 2 recebe revisão independente de
rótulos e conferência de semelhança antes da integração. Task 3 começa sobre
base integrada com ambas aceitas e suas fontes congeladas. Task 4 revisa o
conjunto, sem consumo real. O integrador mantém o ledger e todos os rulings.

## Task 1: Criar e congelar as instruções candidatas

Ambiente: branch `feat/r2-instrucoes-qwen`, worktree `.worktrees/r2-qwen`,
base comum fornecida pelo integrador. Propriedade exclusiva:
`script/classification_comparison/adapters/qwen/r2/`.

Criar `prompt.txt`, `politica.txt` e `candidate.json`. O JSON contém exatamente
`contract_version`, `identity`, `prompt`, `policy`; identity usa mode real,
provider feita, requested/expected_returned_model qwen/qwen3.8-27b,
adapter_version 1.2.0 e policy_version 1.1.0. Referências prompt/policy seguem
path/version/sha256 e apontam para os arquivos novos, versões 1.1.0.
Não incluir comando legado, autorização, gabarito, exemplos ou dados finais.

Leia somente AGENTS, CONTEXT, este brief, catálogo/rubrica, os arquivos do
adaptador Qwen legados e, se necessário, os 24 casos antigos de development.
Não abra dataset global inteiro para estudar outros casos; use uma extração
restrita de development. Não leia relatórios/saídas antigas nem a frente R2
de dados ou arquivos novos de finais. O brief já contém os requisitos.

Instruções devem separar suporte de cada campo, reconhecer falta de fato
discriminante, não preencher assunto por gravidade ou prioridade por assunto,
interpretar linguagem clara sem depender de palavra isolada, e retornar só
JSON obrigatório. Rubrica comum é anexada pelo executor; não copiar definições
que possam divergir. Uma versão candidata, zero exemplos no prompt.

Validar JSON, referências e hashes; conferir request_body existente com campos
ausentes/preservação, sem transporte real. Não criar testes que afirmem que
um texto de prompt é obedecido por LLM; testar apenas estrutura verificável.
Registrar autoverificação, comandos, preocupação real e commit no report.
Freeze: o integrador aceita por revisão independente e registra hash/commit;
depois disso nenhuma alteração motivada por novos finais ou resultados.

## Task 2: Criar o final independente e revisar os rótulos

Ambiente: branch `docs/r2-protocolo-dados`, worktree `.worktrees/r2-dados`,
base comum. Propriedade exclusiva inicial:
`docs/planejamento/classificacao-comparativa/r2/final-cases.json` e
`data-authorship.json` nessa pasta. Não alterar código, protocolos ou históricos.

Leia somente AGENTS/CONTEXT, este brief, rubrica comum e catálogo. Não leia
`script/f08/jev/dataset.json`, qualquer JSONL/report de candidatos, docs de
resultado, instruções candidatas novas ou textos finais antigos. IDs e textos
devem ser inéditos a partir de outros cenários e construções linguísticas.

`final-cases.json`: objeto com version 2.0.0, review
`authored_pending_independent_review`, language pt-BR e cases. Cada caso tem
id, text, received, missing, expected, stratum (rotina/urgente/ambiguo),
rationale em português. missing/expected contêm somente alvos, em ordem
category/priority. received guarda os fornecidos válidos e alvos ausentes;
usar a mesma semântica de normalização. IDs r2-001..012 categoria,
r2-013..024 prioridade, r2-025..036 dupla. Quotas são as Global Constraints.

Texto deve sustentar as respostas determináveis e tornar verdadeira a falta
de informação dos insuficientes, sem rótulo de bastidor. Variar marcas
sintéticas, categorias e níveis; a marca não muda a semântica. Rationale
explica a evidência do texto antes de modelo. Nenhum dado pessoal real.
`data-authorship.json` registra autor/agente, base, método, restrições de
acesso, contagens e pending_independent_review; não fingir aprovação humana.

Validar estrutura, unicidade, máscaras, quotas, caracteres/JSON e rótulos de
catálogo. Não ler os antigos textos para comparar semelhanças. Não imprimir
textos novos no retorno; report completo em arquivo, resumo só metadados.

Após entrega, o integrador solicita a um agente novo revisão de todos os 36
rótulos contra rubrica/catálogo sem acesso ao candidato ou resultados, e a um
terceiro conferente a comparação de semelhanças com os 60 textos antigos,
sem respostas do Qwen. Registros finais `data-review.json` e
`similarity-review.json` trazem hashes/vereditos e origem; não há aprovação
enquanto existirem divergências abertas. Feedback que exigir corrigir casos
volta ao mesmo autor, sem transportar antigos textos ou outputs. O custo de
uma violação de separação é refazer o final, não esconder a exposição.

## Task 3: Integrar perfil, contrato e executor R2 offline

Ambiente: branch `feat/r2-avaliador`, worktree `.worktrees/r2-avaliador`, base
integrada fornecida depois dos aceites Tasks 1/2. Propriedade:
novos arquivos em `script/classification_comparison/r2/`, pacote/contrato
`docs/planejamento/classificacao-comparativa/r2/`, exemplos contratuais novos
`contratos/relatorio-1.3/` e mudanças mínimas nos módulos comuns de verificação/
execução. Não alterar textos congelados ou gabarito para acomodar testes.

1. Montar `dataset.json` com os 24 development antigos byte-equivalentes por
   objeto, seguidos dos 36 finais aceitos; `split.json`, `protocol.json`,
   provenance/reviews/locks. Perfis históricos e fontes ficam preservados.
   Seleção R2 explícita, schema report1.3 com novo $id; IPC permanece1.1.
   Confirmar hashes dos reviews e dataset final antes de planejar ou executar.
2. Fazer verificação/fixtures reproduzíveis do perfil e golden report R2.
   Fontes antigas ou adulteradas, membership/quota e gabarito em projeção de
   requisição devem ser rejeitados. Reusar decide, Journal e relógio C02;
   reconhecimento de família de perfis deve preservar a régua antiga.
3. CLI `r2/execute.py`: init-account/status/reconcile podem delegar o serviço
   financeiro existente; `run --stage development|final --mode fixture|real`,
   dry-run, manifesto específico, conta/id/teto e confirmação explícitos.
   Não incluir loader de .env. Stage development planeja só os 6 IDs definidos,
   sem controles; final planeja36+13/44. Proteger fonte e ordem/IDs por stage.
4. Adaptador reutiliza request_body/interpretation/transport Qwen e evidência
   monetária C05, com parâmetros128/reasoningfalse preservados. Reusar funções
   atuais quando possível; não duplicar a lógica financeira nem generalizar
   produto para escolher modelo. Novo settings/binding refletem perfil/stage,
   candidata, configsha, código, fontes, IDs, conta e teto.
5. Gate do development: preservar relatório/journal de seis e produzir um
   resultado verificável contra as condições explícitas do Spec. Final exige
   prova de development completo/pass do mesmo mode, conta, candidata,
   protocolo, config financeira e revisão de código. Prova fixture não libera
   real; prefixo, fonte/custo adulterados ou gate failed não liberam final.
   Referência de gate e hashes entram no manifesto final, antes de chave/rede.
   O report de development continua inconclusive para elegibilidade do modelo;
   seu gate operacional é separado. Em fixture, tempos de LLM não são medidos:
   resultado `fixture_ready` pode liberar apenas final fixture, após conferir
   os campos/decisões sintéticos e custos simulados. Não fabricar p95 fixture
   para passar a régua real. Development real exige status `pass` com todas as
   seis durações reais e as demais condições; nenhum `fixture_ready` libera real.
6. Execução não repete stage/binding/manifesto para completar interrompido.
   Real permanece bloqueado sem manifesto próprio habilitado e confirmação;
   exemplos/config real falsos. Limites faturáveis/referências verificados só
   no futuro pré-voo real, com a conta existente. Nenhum budget real é aberto.
7. Fixtures: simular desenvolvimento pass e final completo36+13/44; fixture
   não comprova qualidade. Cobrir falha do gate, perfil antigo/arquivo alterado,
   entrada completa/inválida, revisão integral, desconhecido/timeout/custo
   conhecido, permanência da conta, replay e modo divergente. Testes podem
   reusar as suítes pertinentes; evitar espelhar o código.

Executar os testes novos, regressões C02/C05/Qwen afetadas, checker dos novos
artefatos e históricos preservados. Documentar comandos reais e pendências.
Não reexecutar suites sem mudança, falha ou preocupação nova. Se aparecer
requisito financeiro fora do serviço existente, voltar ao integrador antes
de mudar interface compartilhada.

Para evitar duplicação do validador financeiro, está autorizada uma extensão
pequena de `c05/settings.py`: parâmetro keyword de scope esperado em
`Settings.load`, com padrão antigo preservado. O R2 passa seu scope fixo
`c05-qwen-r2`. Mesmas restrições e cálculo de reserva; não relaxar preço,
precisão, referências, unidade ou limites. Cobrir aceitação/rejeição por scope
e regressões C05. Isso não autoriza alteração em `c05/budget.py`.

## Task 4: Revisar, registrar e integrar a preparação offline

Revisão de especificação e qualidade por tarefa, correções dirigidas e uma
revisão ampla final. O integrador percorre o CLI fixture com development
pass/final completo e verifica arquivos/hashes e bloqueios reais sem chave.
Preservar review/relatórios/decisões e registrar fronteiras de dados e todos
os rulings antes de remover somente o scratch deste plano. Manter conta
financeira real e worktrees irmãs intactas. Integração local autorizada;
sem push ou criação de novas issues não solicitadas. Atualizar o card C05.

Entregar commit/base/branch/worktree, alterações, verificações e exercício
ligado à revisão integral. Declarar zero chamadas pagas e nenhuma afirmação
de ganho do modelo. Próximo passo pago exige plano e autorização concretos;
não pedir confirmação adicional para implementar o escopo offline já escolhido.
