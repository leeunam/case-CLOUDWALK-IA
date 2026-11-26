# Operação do piloto E01

O integrador executa P1 em um projeto local dedicado. P2–P6 dependem da conciliação de P1. A matriz tem seis conversas, nove mensagens e duas marcas fictícias. Cada despacho passa pelo simulador Rails, pela ponte Kafka, pelo consumidor Luna e pelo ledger privado autenticado. O orçamento compartilhado e as 24 autorizações continuam sob controle do Rails. [Matriz congelada](planejamento/e01-atendente-real.md#matriz-congelada-para-o-piloto) · [Pré-voo financeiro](../backend/E01.md)

## Antes de P1

1. Confirmar o aceite offline E01-04 e o pré-voo aplicável à conta e à rota. Reservar a porta escolhida para a API do projeto. Usar o mesmo usuário do sistema para toda a execução.
2. Subir a infraestrutura E01 em projeto próprio, por exemplo `cloudwalk_e01_piloto`, com `compose.yml`, `compose.demo.yml`, `compose.e01.yml` e o overlay local real do integrador. O overlay configura `E01_BACKEND=luna`, a saída para a Feita exclusivamente no consumidor, a chave montada somente para leitura e `CLOUDWALK_E01_AUDIT_DIR` para a captura financeira privada. Os dados desta execução usam o Rails em desenvolvimento, o PostgreSQL `cloudwalk_development` e o Kafka próprios deste projeto. Manter os volumes durante toda a avaliação.
3. Deixar o serviço `mock` com backend Luna criado e parado. Os demais serviços da cadeia devem estar prontos. O runner identifica os contêineres pelas etiquetas do Compose e confere que a URL aponta para a porta publicada pelo serviço `api` em `127.0.0.1`. O runner usa o Docker local para iniciar e parar esse consumidor, copiar o diretório financeiro dedicado com o consumidor parado e consultar o ledger via `psql` em transação de leitura. O diretório de captura começa vazio e deve ser exclusivo da matriz durante toda a execução.
4. A primeira execução espera um projeto dedicado sem ingressos anteriores. Ao encontrar atividade sem journal correspondente, investigar os recibos já existentes antes de qualquer ação. Não apagar o journal, recriar volumes ou usar outro projeto para repetir a compra.

```sh
python3 -B script/e01/pilot.py canary --project cloudwalk_e01_piloto --base-url http://127.0.0.1:43309
```

P1 envia uma mensagem de Pix com prioridade básica pelo chat Aurora. A preparação da sessão usa o cookie do simulador, CSRF e o identificador da sessão em memória. Antes do POST, o runner grava o turno e a chave de idempotência, sincroniza o arquivo e seu diretório. Um POST sem recibo fica inconclusivo. Após o recibo, inicia o consumidor, espera no máximo uma rodada de 60 segundos para o resultado e solicita a parada também em caso de erro. A parada do contêiner e as leituras HTTP/PostgreSQL têm limites de tempo próprios. Em caso de encerramento forçado do processo ou do computador, verificar imediatamente se o consumidor está parado. As reexecuções recusam turnos já iniciados. Não há comando de reenvio.

O journal privado fica em `~/.local/state/cloudwalk-e01/<projeto>/journal.json`. Ele contém apenas dados deste piloto, incluindo o histórico sintético e a proposta persistida. O relatório `public.json`, ao lado, usa uma lista explícita de campos e omite as mensagens, cookies, chaves, sessões e o identificador bruto do provedor. Ambos usam modo 0600. O runner resolve o diretório pessoal pelo UID da conta do sistema. Mesmo com valores diferentes de `HOME`, processos desse usuário disputam o mesmo lock do projeto. Cada leitura do orçamento vincula o projeto, a URL, o identificador do cluster PostgreSQL, o nome e o OID da base e a linha de piloto 1. Se a máquina mudar, preservar o estado e reconciliar antes de qualquer retomada.

## Conciliar um despacho

Revisar a orientação e sua fonte contra a edição congelada. Verificar os hashes do pedido e da proposta, a aplicação no Rails, o tempo de persistência e o estado do caso. A aprovação datada registra essa revisão humana. Para P1, cruzar três registros do mesmo despacho.

- O journal contém o `account_ref` privado do snapshot, o ID do provedor, os contadores normalizados, o hash do pedido e a provisão registrada pelo Rails. Antes de liberar P2 o runner relê o mesmo caso e a mesma sequência no PostgreSQL e compara os identificadores, hashes, recibo aplicado, conta, uso e valores com P1.
- O arquivo de captura privada da Luna contém `id`, `model`, `status`, `started_at`, `finished_at`, `request_sha256` e o objeto financeiro `usage`. Comparar `prompt_tokens`, `completion_tokens` e sua soma `total_tokens` com o ledger. Quando `prompt_tokens_details` estiver presente, seu `cached_tokens` precisa ser inteiro válido e coincidir com o valor normalizado. A omissão integral do objeto permite aplicar zero desconto. Nesse caso, o relatório preserva `cached_tokens_observed: null` e o campo normalizado de desconto permanece 0. O hash da captura identifica os bytes do POST ao provedor, enquanto o hash do ledger identifica os bytes do evento interno.
- A fonte monetária precisa identificar a resposta da Feita e a unidade do valor. Usar o próprio recibo HTTPS com `usage.credits` ou `usage.cost`, ou um extrato individual do portal. Salvar uma extração JSON separada com digest distinto da captura e com `original` apontando para o documento usado. Para `provider_api_receipt`, o original é a captura do despacho e `field` seleciona o campo financeiro bruto. Para `provider_portal`, o original é a exportação privada ou imagem do extrato, com digest distinto dos outros dois arquivos. A conferência da autenticidade e da transcrição cabe ao revisor. A cobrança informada no recibo representa o valor reportado pela API. A liquidação na carteira exigiria evidência da própria carteira.

Exemplo de **formato** para extrair os créditos do recibo HTTPS. Todos os marcadores dependem de valores observados. O `account_ref` do documento e o `conversion_account_ref` da taxa devem coincidir com a conta do snapshot Rails. Quando a captura também identificar a conta, exige-se o mesmo valor. As referências privadas não aparecem no relatório público.

```json
{
  "id": "<id observado na Feita>",
  "source_type": "provider_api_receipt",
  "source": "<rota do gateway e referência privada do despacho>",
  "original": {"file": "<captura financeira original>", "sha256": "<digest do original>"},
  "account_ref": "<referência da conta>",
  "field": "credits",
  "precision": "exact",
  "observed_at": "<instante ISO 8601 com fuso>",
  "amount": "<decimal informado pela API>",
  "unit": "credits",
  "usd_per_credit": "<taxa decimal documentada>",
  "conversion_source": "<referência aplicável à conta e à data>",
  "conversion_account_ref": "<referência da conta>"
}
```

Para extrato do portal, usar `provider_portal` e omitir `field`. Uma observação em USD usa `"unit":"USD"`. Se houver créditos em qualquer um dos documentos, a conversão também exige a taxa e sua fonte aplicável. Cada campo monetário presente na captura precisa ser consistente com os demais e caber no intervalo do extrato. Para `usage.cost` sem `usage.cost_unit`, registrar também `cost_unit` e `cost_unit_source` identificando a evidência que estabelece a unidade de `cost`. Se um campo específico da API tiver arredondamento comprovado, registrar, por exemplo, `capture_precision.cost` com `precision`, `quantum` e `precision_source`. Os valores conhecidos precisam admitir uma cobrança comum considerando suas precisões. Um valor sem unidade fundamentada, saldo agregado ou divergência mantém P2 pendente.

Para arredondamento ao valor mais próximo, usar `"precision":"nearest"`. Para truncamento de uma cobrança não negativa, usar `"precision":"truncated"`. Informar `quantum` como decimal na unidade original e `precision_source` como referência que documenta a precisão e a regra. O relatório conserva o valor exibido e os extremos conservadores do intervalo. Seu limite superior precisa caber no valor contabilizado. Quando a regra ou unidade não tiver respaldo, preservar a pendência.

Preparar um arquivo de aprovação privado para P1 e para cada revisão humana posterior. Os nomes de arquivo são relativos ao arquivo de aprovação ou absolutos. Copiar `binding` integralmente do journal. Gerar os hashes SHA-256 dos dois arquivos de evidência e usar a data real da revisão.

```json
{
  "approved": true,
  "reviewer": "<identificação do integrador>",
  "reviewed_at": "<instante ISO 8601 com fuso>",
  "binding": {
    "project": "<projeto>",
    "api": "<origem local da API>",
    "cluster": "<identificador do cluster>",
    "database": "<nome>",
    "oid": "<oid>",
    "pilot": 1
  },
  "request_id": "<id da rodada no ledger>",
  "result_sha256": "<hash verificado da proposta>",
  "capture": {"file": "<captura da Luna>", "sha256": "<digest>"},
  "provider_record": {"file": "<extração do recibo da API ou do extrato>", "sha256": "<digest>"}
}
```

```sh
python3 -B script/e01/pilot.py remaining --project cloudwalk_e01_piloto --base-url http://127.0.0.1:43309 --approval /caminho/privado/p1-aprovado.json
```

O comando verifica a aprovação e o hash da captura original de P1 antes de enviar P2. Em cada turno seguinte, inclusive o último, o runner para o consumidor e copia seu diretório financeiro. A contagem de originais precisa coincidir com a de despachos e os hashes anteriores precisam reaparecer. A nova captura deve corresponder ao ID, à conta da rodada, aos tokens e aos horários do despacho. Cada campo monetário é comparado com os demais na precisão documentada e seu limite superior deve caber na provisão do ledger. O runner usa a unidade explícita da API ou a referência de unidade documentada em P1, além da conversão de créditos aprovada para aquela conta. Um campo monetário ou uma unidade explícita que a captura marcou como inválido impede o avanço. A cópia privada do recibo conciliado fica ao lado do journal, que registra o nome e o hash.

O runner só envia a próxima mensagem após essas verificações e mantém a sessão do simulador nos turnos da mesma conversa. Cada avanço exige ausência de reserva pendente, contagens do mesmo piloto e resultado anterior íntegro. O histórico é comparado por ordem, autor e texto. O runner confere a marca, canal, classificação, fonte, versão, passos ou pergunta, disposição, estado, motivo e resumo do encaminhamento, referências e confirmação explícita para resolver. `procedure_checked` é o procedimento usado na comparação com a base. O fluxo registra `source_refs` e a regra no ledger. A prova de isolamento dos candidatos no contexto depende dos testes e do código de seleção da base. A captura financeira preserva apenas campos do despacho.

Uma falha interrompe a matriz e preserva o que já foi executado. Timeout, uso ausente, cobrança ambígua, falha de parada ou interrupção exigem inspeção. Parar o consumidor caso a confirmação da parada tenha falhado. Abrir o journal para conferir o caso/turno, as reservas e as contagens antes de interpretar o relatório. A última leitura do banco é uma fotografia e pode preceder uma expiração ou liquidação posterior.

O comando de conciliação individual complementa os tempos e o valor informado pelo provedor. Uma rodada falha ou descartada com recibo atribuível e valor contabilizado também pode ser conciliada financeiramente. A extração deve indicar o mesmo pedido e `result_sha256` pode ser nulo quando inexiste proposta. O veredito do atendimento permanece `failed` ou `timeout`, e o canário reprovado bloqueia P2. Ele também pode registrar P1 separadamente antes de `remaining`.

```sh
python3 -B script/e01/pilot.py reconcile --project cloudwalk_e01_piloto --base-url http://127.0.0.1:43309 --turn P2.1 --approval /caminho/privado/p2-1-aprovado.json
```

`reserved_at_claim_usd` é a reserva inicial de cada execução. `accounted_usd` é o valor contabilizado no ledger, que no perfil conservador provisiona um teto pelo uso verificado. `provider_observed_usd` vem da conciliação individual e fica nulo até ela existir. A soma dos recibos conciliados é parcial enquanto a contagem de recibos ficar abaixo dos despachos. Uma verificação automática bem-sucedida recebe `checked`. A coluna `human_reviewed` só recebe `true` para uma orientação aceita com aprovação humana registrada. Após a conferência financeira automática, o campo aguarda a revisão humana da orientação. `financially_reconciled` também pode valer para falhas. O indicador `distinct_provider_ids_in_ledger_usage` conta pares distintos de conta e ID de resposta presentes no uso persistido. Um despacho `unknown` sem uso pode ter ID na captura privada e ficar fora dessa contagem. As autorizações de despacho aparecem em `dispatch_authorizations`. Um ID repetido em turnos diferentes bloqueia o próximo envio e exclui ambos os montantes da soma até esclarecer a atribuição.

Os ensaios históricos Luna R3/R5 publicaram extratos filtrados com ID `gateway:gen-…`, créditos e conversão para USD. Nos arquivos examinados faltam os campos brutos de cache do envelope de resposta. Esse material explica quais campos procurar. A primeira cobrança E01 e sua unidade precisam de verificação própria. [Extrato R3](evidencias/c05/luna-ensaio-real-01/financial-receipts.json) · [Extrato R5](evidencias/c05/luna-r5-ensaio-real-01/financial-receipts.json)

## Ensaio adicional da candidata E01-Q1

O primeiro ensaio de 26/11/2026 chegou a cinco despachos. P1.1, P2.1, P2.2 e P3.1 passaram. P3.2 terminou em `invalid_decision`, com uso e custo conciliados. A opção `--attempt e01-q1` abre uma única rodada adicional da matriz no mesmo projeto, banco e piloto 1. A execução completa acrescenta nove despachos e totaliza 14 das 24 autorizações originais. O limite acumulado continua em US$ 1. [Decisão do ensaio](planejamento/e01-atendente-real.md#ajuste-após-a-primeira-execução-real--e01-q1-e-e01-q2)

1. Após o aceite de Q1, use o checkout integrado para construir a imagem e recriar somente o consumidor, deixando-o parado. Preserve previamente os cinco arquivos originais do diretório indicado por `CLOUDWALK_E01_AUDIT_DIR`, os nomes e modos 0600 e a permissão de escrita do usuário do consumidor. Se as capturas estiverem na camada gravável do contêiner, copie-as para armazenamento privado antes de recriá-lo e restaure-as no diretório de auditoria do novo contêiner. Mantenha os volumes de PostgreSQL e Kafka, o pré-voo, a conta e a porta da API do projeto.
2. Separe o mesmo arquivo de aprovação de P1 usado no lote original e conserve as evidências que ele referencia. No primeiro comando do ensaio adicional, forneça esse arquivo com `--parent-approval`. O runner confere os registros duráveis das cinco execuções, a falha conhecida, o tarifário e as capturas. Ele compara o código Python do consumidor parado com os módulos do commit do checkout e registra o commit e a imagem no journal filho.
3. Defina a variável de shell `E01_BASE_URL` com a URL exata registrada em `binding.api` do journal original e execute o novo canário. O diretório privado do projeto guarda o journal e o relatório adicionais em `e01-q1/`. As duas execuções compartilham o lock do projeto. Antes do POST do novo P1, o runner grava também `e01-q1.intent.json` no diretório pai, com a chave do envio e o hash do journal original. Preserve o marcador junto ao pai. Se o filho for arquivado ou perder o registro dessa intenção, outra execução interrompe antes do envio. O filho registra o hash dos bytes do journal original, a conta, o tarifário, os pedidos, os IDs do provedor e os hashes das cinco capturas. Cada novo POST exige contagem de ingressos e despachos compatível, ausência de reserva pendente e saldo para reservar o próximo despacho. A autorização final de gasto continua a cargo do Rails.

```sh
python3 -B script/e01/pilot.py canary --attempt e01-q1 --project cloudwalk_e01_pilot_20261126 --base-url "$E01_BASE_URL" --parent-approval /caminho/privado/primeiro-p1-aprovado.json
```

4. Concilie o **novo P1** usando o novo ID de pedido, hash do resultado, captura de uso e recibo monetário. Se o responsável aprovou anteriormente essa mesma orientação e o integrador verificou sua identidade, o novo arquivo de conciliação pode incluir `prior_orientation_approval_sha256` com o hash do primeiro arquivo de aprovação. Registre em `reviewer` quem conferiu o novo registro. O runner valida o conteúdo e a fonte. O relatório marca `prior_identical_orientation_approved` e preserva `human_reviewed: false` nessa modalidade. Uma revisão humana direta do novo P1 segue o formato normal.
5. Execute o restante com o mesmo commit integrado e a mesma imagem. O comando `reconcile` também aceita `--attempt e01-q1` para conferir um despacho individual. A cada compra, as capturas anteriores devem reaparecer com os mesmos hashes. Qualquer intenção sem recibo, falha ou divergência financeira interrompe o ensaio. Reabrir o runner preserva essa intenção.

```sh
python3 -B script/e01/pilot.py remaining --attempt e01-q1 --project cloudwalk_e01_pilot_20261126 --base-url "$E01_BASE_URL" --approval /caminho/privado/novo-p1-conciliado.json
```

No relatório do filho, `previous_attempt` identifica as cinco execuções originais e seus estados. As nove linhas da matriz, os despachos identificados no ledger em `attempt_dispatches`, a respectiva provisão em `attempt_accounted_usd`, `receipts_reconciled` e `sum_of_reconciled_receipts_usd` dizem respeito à candidata. `dispatch_authorizations` e `ledger_last_read.accounted_usd` vêm do orçamento global. A contagem `distinct_provider_ids_in_ledger_usage` também considera os IDs de ambos os ensaios. `cumulative_provider_observed_usd` e `cumulative_receipts_reconciled` somam as cobranças conciliadas dos dois ensaios. Uma colisão de IDs do provedor torna essa soma indeterminada. O overlay E01 envia SIGINT ao consumidor para que ele feche a conexão e libere o grupo Kafka. O runner aguarda até dez segundos pela parada e informa falha se houver encerramento forçado.

## Exercício offline

Rode os testes e observe o caso de perda do recibo: existe um único envio, a intenção permanece no journal e a segunda tentativa é recusada.

```sh
python3 -B -m unittest discover -s script/e01 -p test_pilot.py -v
```
