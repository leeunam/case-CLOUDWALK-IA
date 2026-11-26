# Operação do piloto E01

O integrador executa P1 em um projeto local dedicado. P2–P6 dependem da conciliação de P1. A matriz tem seis conversas, nove mensagens e duas marcas fictícias. Cada despacho passa pelo simulador Rails, pela ponte Kafka, pelo consumidor Luna e pelo ledger privado autenticado. O orçamento compartilhado e as 24 autorizações continuam sob controle do Rails. [Matriz congelada](planejamento/e01-atendente-real.md#matriz-congelada-para-o-piloto) · [Pré-voo financeiro](../backend/E01.md)

## Antes de P1

1. Confirmar o aceite offline E01-04 e o pré-voo aplicável à conta e à rota. Reservar a porta escolhida para a API do projeto. Usar o mesmo usuário do sistema para toda a execução.
2. Subir a infraestrutura E01 em projeto próprio, por exemplo `cloudwalk_e01_piloto`, com `compose.yml`, `compose.demo.yml`, `compose.e01.yml` e o overlay local real do integrador. O overlay configura `E01_BACKEND=luna`, a saída para a Feita exclusivamente no consumidor, a chave montada somente para leitura e `CLOUDWALK_E01_AUDIT_DIR` para a captura financeira privada. Os dados desta execução usam o Rails em desenvolvimento, o PostgreSQL `cloudwalk_development` e o Kafka próprios deste projeto. Manter os volumes durante toda a avaliação.
3. Deixar o serviço `mock` com backend Luna criado e parado. Os demais serviços da cadeia devem estar prontos. O runner identifica os contêineres pelas etiquetas do Compose e confere que a URL aponta para a porta publicada pelo serviço `api` em `127.0.0.1`. O runner usa o Docker local para iniciar e parar apenas esse consumidor e o `psql` do contêiner `db` para consultar o ledger em transação de leitura.
4. A primeira execução espera um projeto dedicado sem ingressos anteriores. Ao encontrar atividade sem journal correspondente, investigar os recibos já existentes antes de qualquer ação. Não apagar o journal, recriar volumes ou usar outro projeto para repetir a compra.

```sh
python3 -B script/e01/pilot.py canary --project cloudwalk_e01_piloto --base-url http://127.0.0.1:43309
```

P1 envia uma mensagem de Pix com prioridade básica pelo chat Aurora. A preparação da sessão usa o cookie do simulador, CSRF e o identificador da sessão em memória. Antes do POST, o runner grava o turno e a chave de idempotência, sincroniza o arquivo e seu diretório. Um POST sem recibo fica inconclusivo. Após o recibo, inicia o consumidor, espera no máximo uma rodada de 60 segundos para o resultado e solicita a parada também em caso de erro. A parada do contêiner e as leituras HTTP/PostgreSQL têm limites de tempo próprios. Em caso de encerramento forçado do processo ou do computador, verificar imediatamente se o consumidor está parado. As reexecuções recusam turnos já iniciados. Não há comando de reenvio.

O journal privado fica em `~/.local/state/cloudwalk-e01/<projeto>/journal.json`. Ele contém apenas dados deste piloto, incluindo o histórico sintético e a proposta persistida. O relatório `public.json`, ao lado, usa uma lista explícita de campos e omite as mensagens, cookies, chaves, sessões e o identificador bruto do provedor. Ambos usam modo 0600. Um lock local impede dois runners no mesmo projeto e usuário. Cada leitura do orçamento vincula o projeto, a URL, o identificador do cluster PostgreSQL, o nome e o OID da base e a linha de piloto 1. Se a máquina mudar, preservar o estado e reconciliar antes de qualquer retomada.

## Conciliar um despacho

Revisar a orientação e sua fonte contra a edição congelada. Verificar os hashes do pedido e da proposta, a aplicação no Rails, o tempo de persistência e o estado do caso. A aprovação datada registra essa revisão humana. Para P1, cruzar três registros do mesmo despacho.

- O journal contém `usage.provider_response_id`, os contadores normalizados e a provisão registrada pelo Rails.
- O arquivo de captura privada da Luna contém `id`, `model`, `status`, `started_at`, `finished_at`, `request_sha256` e o objeto financeiro `usage`. Comparar `prompt_tokens`, `prompt_tokens_details.cached_tokens` e `completion_tokens` com o ledger. A falta de uma contagem mantém a conciliação pendente. O hash da captura identifica os bytes do POST ao provedor, enquanto o hash do ledger identifica os bytes do evento interno.
- O registro independente da Feita precisa identificar o mesmo ID, a cobrança individual, a unidade financeira e a precisão. Salvar privadamente o documento de origem e uma extração JSON com os campos abaixo. O revisor responde pela correspondência entre a extração e o documento consultado. Se a interface mostrar apenas um total agregado, a conciliação individual continua pendente. Valores arredondados exigem também a resolução e a regra usada pela fonte. Não preencher o custo com uma estimativa do ledger.

Exemplo de **formato** para a extração, com marcadores a substituir pelos valores observados. `source` identifica a origem consultável. Para cobrança expressa em USD, usar `"unit":"USD"` e omitir a taxa e sua referência.

```json
{
  "id": "<id observado na Feita>",
  "source": "<extrato individual consultado, data e referência privada>",
  "precision": "exact",
  "observed_at": "<instante ISO 8601 com fuso>",
  "amount": "<decimal exato transcrito>",
  "unit": "credits",
  "usd_per_credit": "<taxa decimal documentada>",
  "conversion_source": "<referência aplicável à conta e data>"
}
```

Para arredondamento ao valor mais próximo, usar `"precision":"nearest"`. Para truncamento de uma cobrança não negativa, usar `"precision":"truncated"`. Informar `quantum` como decimal na unidade original e `precision_source` como referência que documenta a precisão e a regra. O relatório conserva o valor exibido e os extremos conservadores do intervalo. Seu limite superior precisa caber no valor contabilizado. Quando a regra ou unidade não tiver respaldo, preservar a pendência.

Preparar um arquivo de aprovação privado por turno. Os nomes de arquivo são relativos ao arquivo de aprovação ou absolutos. Copiar `binding` integralmente do journal. Gerar os hashes SHA-256 dos dois arquivos de evidência e usar a data real da revisão.

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
  "provider_record": {"file": "<extração do extrato independente>", "sha256": "<digest>"}
}
```

```sh
python3 -B script/e01/pilot.py remaining --project cloudwalk_e01_piloto --base-url http://127.0.0.1:43309 --approval /caminho/privado/p1-aprovado.json
```

O comando verifica a aprovação antes de enviar P2. Cada turno seguinte exige ausência de reserva pendente, contagens do mesmo piloto e resultado anterior íntegro. O histórico é comparado por ordem, autor e texto. O runner confere a marca, canal, classificação, fonte, versão, passos ou pergunta, disposição, estado, motivo e resumo do encaminhamento, referências e confirmação explícita para resolver. `procedure_checked` é o procedimento usado na comparação com a base. O fluxo registra `source_refs` e a regra no ledger. A prova de isolamento dos candidatos no contexto depende dos testes e do código de seleção da base. A captura financeira preserva apenas campos do despacho.

Uma falha interrompe a matriz e preserva o que já foi executado. Timeout, uso ausente, cobrança ambígua, falha de parada ou interrupção exigem inspeção. Parar o consumidor caso a confirmação da parada tenha falhado. Abrir o journal para conferir o caso/turno, as reservas e as contagens antes de interpretar o relatório. A última leitura do banco é uma fotografia e pode preceder uma expiração ou liquidação posterior.

Depois de uma revisão bem-sucedida, o comando de conciliação individual complementa os tempos de provedor e o gasto monetário observado. Ele também pode registrar P1 separadamente antes de `remaining`.

```sh
python3 -B script/e01/pilot.py reconcile --project cloudwalk_e01_piloto --base-url http://127.0.0.1:43309 --turn P2.1 --approval /caminho/privado/p2-1-aprovado.json
```

`reserved_at_claim_usd` é a reserva inicial de cada execução. `accounted_usd` é o valor contabilizado no ledger, que no perfil conservador provisiona um teto pelo uso verificado. `provider_observed_usd` vem da conciliação individual e fica nulo até ela existir. A soma dos recibos conciliados é parcial enquanto a contagem de recibos ficar abaixo dos despachos. Uma verificação automática bem-sucedida recebe `checked`. A coluna `human_reviewed` indica as aprovações já conciliadas.

Os ensaios históricos Luna R3/R5 publicaram extratos filtrados com ID `gateway:gen-…`, créditos e conversão para USD. Nos arquivos examinados faltam os campos brutos de cache do envelope de resposta. Esse material explica quais campos procurar. A primeira cobrança E01 e sua unidade precisam de verificação própria. [Extrato R3](evidencias/c05/luna-ensaio-real-01/financial-receipts.json) · [Extrato R5](evidencias/c05/luna-r5-ensaio-real-01/financial-receipts.json)

## Exercício offline

Rode os testes e observe o caso de perda do recibo: existe um único envio, a intenção permanece no journal e a segunda tentativa é recusada.

```sh
python3 -B -m unittest discover -s script/e01 -p test_pilot.py -v
```
