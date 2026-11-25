# Pré-voo financeiro da C05-R5 em 25/11/2026

**Parecer estático.** O candidato B aceitou as evidências financeiras e calculou USD 1,239 por pedido em aberto. A configuração entregue bloqueia a execução. A preparação usou arquivos públicos e a captura local do integrador. Houve zero chamadas, zero acesso a credenciais ou à conta real. O custo, a latência e a qualidade reais da R5 continuam sem medição.

Base do integrador `main@433c442d135925098f4d724ed6688b80bf43bf1b`. Candidato examinado `feat/luna-executor-r5@0161b962b298720d39823b45c76ef45a1af679a0`, em `.worktrees/r5-luna-executor`. Política 2.1.0 do commit `38ac4cb81abe9f84469e379cee30e6bb976e25dd`. Revisão de B e revisão ampla A+B precedem qualquer consumo. Se alguma delas mudar o código, renovar a conferência estática sobre a revisão efetivamente integrada.

## Quanto reservar e quanto observar

| USD por milhão de tokens | Entrada | Saída | Leitura de cache | Escrita de cache |
|---|---:|---:|---:|---:|
| Padrão | 0,20 | 1,20 | 0,02 | 0,25 |
| Contexto longo | 0,40 | 1,80 | 0,04 | 0,50 |

A captura Feita do integrador em 25/11 identifica modelo operacional, contexto exibido de 1,05 milhão, saída de 32 mil, preços padrão de entrada, saída e leitura de cache, USD 0,01/crédito e parâmetros compatíveis. O snapshot oficial do modelo conferido em 25/11 às 02:39 UTC documenta o limiar de 272 mil tokens, multiplicadores de 2× para entrada e 1,5× para saída, e escrita de cache a 1,25× da entrada sem cache. A coluna de escrita e a faixa longa são inferências conservadoras. O pedido é `max_completion_tokens=384`, `reasoning_effort=none`, `stream=false`. A cobertura financeira usa 1.050.000 tokens de entrada e 140.000 de saída e soma entrada, leitura e escrita antes de aplicar os limites. Os máximos oficiais publicados eram 922.000 de entrada e 128.000 de saída.

`(1.050.000 × (0,40 + 0,04 + 0,50) + 140.000 × 1,80) / 1.000.000 = USD 1,239`. A concorrência é um. O ledger reserva antes de cada despacho e libera a diferença somente mediante conciliação. A exposição teórica bruta de seis reservas é USD 7,434 e de 44 é USD 54,516. O teto cumulativo global é USD 10 e prevalece sobre o tamanho nominal de cada etapa. Uma etapa pode parar por falta de saldo.

**Cenário ilustrativo, reproduzível.** Os seis corpos R5 construídos localmente com as entradas públicas de desenvolvimento da R4, na ordem congelada, tinham 7.112, 7.085, 7.161, 7.086, 7.496 e 7.449 bytes UTF-8. Como análise de sensibilidade, suponha tantos tokens de entrada quantos bytes em cada corpo, 384 tokens de saída por pedido e as quatro tarifas máximas. A conta dá USD 0,04493286 para os seis e, se todos os 44 finais tivessem o tamanho do maior desses seis, USD 0,34044736 para o final. A equivalência entre bytes e tokens e o tamanho suposto da amostra final são hipóteses ilustrativas. O fornecedor pode contabilizar tokens adicionais. A projeção não participa do bloqueio financeiro e não constitui medida do custo real. Quando houver resposta, usar os créditos identificados daquela resposta × 0,01 em decimal exato e o recibo individual. A unidade publicada de `usage.cost` permanece desconhecida. Custo ausente, saldo insuficiente, falha técnica ou divergência exigem parada e registro pelos mecanismos existentes.

**Último estado público.** O SHA-256 de `docs/evidencias/c05/luna-r4-ensaio-real-01/development-finance-after.json` é `681bf5df9338bc99ad88f59abf7fe9b5e458006aec8a038f163d37664c1b560e`. Contabilizado USD 0,03093512, disponível USD 9,96906488, 62 reservas liquidadas, zero pendentes, quatro execuções (três encerradas, uma interrompida), sem congelamento. É um retrato histórico. O integrador verificará identidade, versão 4, cap, saldo, estados, correções e pendências diretamente antes da execução.

## Arquivos que o integrador pode publicar

Destino `docs/evidencias/c05/luna-r5-preflight-2026-11-25/`. Copiar os bytes dos três arquivos da coordenação para os nomes abaixo. As três evidências R4 usadas diretamente (rota, limites e conversão) conservam seus caminhos e hashes históricos. A captura R5 fundamenta a tarifa atual. O histórico de tarifas R4 é uma referência suplementar.

| Fonte no SDD | Nome no destino | SHA-256 atual |
|---|---|---|
| `r5-feita-public-check.json` | `feita-public-check.json` | `ac0e4d42f30c4c260beb13c2e29b8d6eae02cbb1aa99ef065c94bde9c306c060` |
| `financial-evidence-draft.json` | `financial-evidence.json` | `56f1703f658249354cfddfb13a89f617de2d8bdf12907990a9db0de4ad37fa9b` |
| `r5-config-real-draft.json` | `config-real-planejada.json` | `5e204af8d47922bb89c7e2db5d9c20e84987f2757175e6cc68fe1a49e3c6a129` |

Em árvore temporária com esses destinos e os snapshots R4, `R5Settings.load` da revisão B verificou os pins. `verify_execution()` recusou a cópia com os flags `billable_limits_confirmed=false` e `tariff_verified=false`. As quatro dimensões de preço conferiram em decimal. Foram conferidos os 37 hashes de B, os 17 arquivos completos e sete funções por AST do freeze v2. Os exemplos distribuídos permanecem desabilitados. A entrada financeira não cria manifesto ou autorização.

## Sequência que cabe ao integrador

1. Fechar as revisões, integrar a revisão aceita e registrar separadamente a decisão sobre o escopo operacional R5. Os documentos da R5 registram preparação offline e teto global previamente aprovado. A escolha “Luna com evidência verificável” e o pedido de concluir o projeto devem ser descritos em seu contexto. Os números 6, 44 e 384 provêm do plano técnico. Um eventual registro específico deve identificar a interpretação do responsável, modelo, candidata, integridade das fontes, etapas, limites, custo e condições de parada. Manter intacto o histórico de autorizações das outras rodadas.
2. Usar checkout de execução dedicado com fontes limpas. Fixar o commit que contém B aceito, o freeze v2 e os arquivos financeiros, o SHA-256 da configuração efetivamente aprovada e a declaração de escopo antes de gerar o plano. Se uma cópia de operação vier a ter confirmações financeiras diferentes do rascunho, congelar e registrar seu próprio hash. Verificar os bytes do disco contra os blobs do commit, o hash da política e as sete funções compartilhadas. Um `git diff` de arquivos rastreados não detecta importações locais novas. Executar essa conferência antes de criar os diretórios novos de saída e usar a mesma revisão até fechar a auditoria. Qualquer divergência interrompe o fluxo.
3. Conferir, com o mecanismo existente, a conta global de escopo `real`, ID `903a037b4b9140438e152ade172889ca`, no caminho fixado por `luna.round_spec.ACCOUNT_RELATIVE`. Validar schema 4, teto cumulativo de USD 10, saldo para USD 1,239, ausência de execução aberta, congelamento, custo ou reserva pendente, inclusive `gateway_pending` ligado a reserva já liquidada. Comparar com o retrato histórico e explicar qualquer diferença antes de novo despacho. Salvar agregados antes e depois de cada etapa e o código de saída mesmo em interrupção. A conta e os selos privados ficam no local original.
4. O auxiliar anterior `luna_r4_real_stage.py` só serve de referência. Para a R5, conferir revisão, SHA da configuração e fontes, escopo `c05-feita-luna-r5`, modelo solicitado e esperado, protocolo 1.5.0, relatório 1.6.0, IPC 1.1.0 e política 2.1.0. O dry-run com conta produz um manifesto-modelo desabilitado. Conferir a conta, a etapa, o hash dos insumos e do congelamento, o mapa dos hashes executáveis, 6/44 pedidos máximos, uma tentativa, concorrência um e reserva 1,239. Cada etapa usa diretórios novos. O fluxo canônico já faz a reserva transacional e a validação de autorização, sem necessidade de duplicá-los em um auxiliar.
5. Desenvolvimento real, se houver decisão de execução, terá até seis pedidos. Preservar recibo, relatório, diário, envelopes, manifesto e selo. Gate reprovado retorna código 2 inclusive quando as seis chamadas já foram liquidadas e a execução consta como `finished`. Outras falhas também podem retornar 2. Distinguir reprovação de erro pelo gate, prefixo, interrupção e extrato. Fechar o balanço mesmo quando o processo for interrompido externamente. Parar sem nova tentativa, sonda ou 16 diagnósticos. Um prefixo ou `fixture_ready` não libera o final.
6. Só considerar o final com gate original `mode=real`, `status=pass` e selo original verificáveis. Conferir com `r2.gate.verify` do executor antes de qualquer consumo do final. O CLI também faz essa validação no caminho de autorização antes de abrir a execução. O dry-run isolado apenas referencia a prova. O protocolo pede 8/8 alvos, 4/4 preservados, 3 conclusões corretas, 3 revisões integrais, 1 urgência, zero erros, 6 liquidações e p95 total ≤3.000 ms em 6 observações. O final usa a mesma conta, configuração, revisão e prova original e admite até 44 pedidos para 36 relatos e 13 controles, incluindo um controle injetado e quatro sem tentativa. Rodar o checker e `verify-final` com ambos os selos. A saída zero do CLI final atesta fechamento, e a elegibilidade é a do recibo verificado. Uma intervenção que altere gabarito ou metas invalida a comparação.
7. O resultado do classificador se refere à combinação Luna + política local. O envelope preserva a proposta original em `audit.raw_content`, o campo proposto, a citação, o veredicto e eventual veto. A escolha IPC e os contadores oficiais de reconhecimento usam a saída após a política. Comparar separadamente acertos vetados e erros aceitos quando houver dados reais, conservando o envelope integral e as classificações de controle. A fixture verifica o fluxo e a integridade. O selo é a âncora independente para os arquivos publicados.

**Comandos de conferência para o integrador.** As variáveis abaixo representam caminhos explícitos no checkout fixado. O dry-run requer diretório ainda inexistente e usa a configuração e a conta explicitamente selecionadas. O checker confere os artefatos públicos. `verify-final` requer o resultado e os selos efetivamente produzidos no modo real.

```sh
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-r5
rtk proxy python3 -B script/classification_comparison/luna_r5/execute.py run --dry-run \
  --mode real --stage development --config "$CFG" --output "$DEV_PLAN" \
  --account "$CONTA" --account-id "$ID_CONTA" --cap-usd 10
rtk proxy python3 -B script/check_classification_contracts.py \
  --profile observed-total-luna-r5 --report "$ETAPA/report.json"
rtk proxy python3 -B script/classification_comparison/luna_r5/execute.py verify-final \
  --mode real --stage final --config "$CFG" --account "$CONTA" --account-id "$ID_CONTA" \
  --cap-usd 10 --development-gate "$DEV/development-gate.json" --output "$FINAL"
```

Não houve dry-run com conta, despacho, medição de modelos ou verificação de selos reais neste pré-voo. Os caminhos de saída e a revisão final do integrador ainda dependem da revisão ampla e da publicação dos arquivos de configuração.
