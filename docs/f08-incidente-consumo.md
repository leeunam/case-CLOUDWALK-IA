# F08 — consumidores encerraram após perda da associação ao grupo

Na rodada complementar `f08-reference-1795208792430-8b61b6-04`, integração `dfbcc79`, os consumidores `events` e `mock` encerraram com código 1 observado pelo integrador. Ambos receberam `UNKNOWN_MEMBER_ID` (25) do Kafka ao tentar confirmar o offset de uma mensagem. A F08 deve registrar a falha do produto e manter essa execução como observada.

## Evidência e verificação offline

O diretório da rodada é `/tmp/cloudwalk-f08-reference-complemento/f08-reference-1795208792430-8b61b6/f08-reference-1795208792430-8b61b6-04`. No `fault.json`, o processo Kafka consta como iniciado às 21:31:29,378 UTC. Às 21:31:40,819 UTC, `events` informou 45.053 ms sem resposta bem-sucedida do coordenador do grupo. Às 21:31:40,972 UTC, `mock` informou 45.052 ms. Cada cliente anunciou revogação da atribuição e tentativa de reingresso. A confirmação síncrona do offset levantou exceção às 21:31:40,912 UTC em `events` e às 21:31:42,699 UTC em `mock`. Esses 45 s medem a ausência de uma resposta bem-sucedida do coordenador. O horário de partida do processo Kafka, isoladamente, não estabelece quando o grupo ficou pronto.

Para conferir a sequência usando somente os arquivos preservados, execute no diretório da rodada:

```sh
rtk rg -n 'SESSTMOUT|consumer\.commit\(message|UNKNOWN_MEMBER_ID' events-diagnostic.log mock-diagnostic.log
```

Nos dois arquivos, as linhas 285 e 299–300 contêm a expiração da sessão, a chamada e a exceção. O traceback não identifica a partição e o offset exatos da confirmação recusada. Os registros de mensagem vizinhos, sozinhos, não demonstram que o efeito correspondente se perdeu ou se duplicou. O veredito quantitativo depende do snapshot SQL e da reconciliação final da rodada. O resultado final está registrado abaixo.

## Por que ambos encerraram

Os dois serviços chamam a mesma função. `process_record` executa a ação ou publica uma falha terminal em `agent.failures`. A seguir, tenta confirmar o próximo offset daquela partição. A exceção da confirmação escapa da função. `consume` fecha o consumidor em `finally`, e o processo encerra. Os comentários do código descrevem esse encerramento como proteção contra avanço indevido e pressupõem um reinício para retomar o consumo. O Compose de carga não define reinício automático para esses serviços. [Fluxo do consumidor](../integration/agent_flow.py) · [Serviços do ensaio](../script/f08/load/compose.yml)

Existe uma janela entre a conclusão do efeito e a confirmação do offset. O mock pode já ter publicado o retorno e a ponte pode já ter recebido um recibo HTTP do Rails. O contrato admite reentrega e exige confirmação contígua por partição. O mock deriva o ID do retorno do ID da solicitação. O Rails reconhece um evento com mesmo ID e mesmos bytes, e trata como conflito o reuso do ID com conteúdo diferente. [Contrato de consumo](contratos/README.md) · [Deduplicação de retornos](../backend/app/services/attendances/apply_agent_result.rb)

## Critérios para uma correção futura

- Após perda de associação, os consumidores devem recuperar uma atribuição válida e retomar a partir da posição confirmada pelo coordenador. O antigo proprietário pode já ter perdido a partição. A recuperação deve distinguir falha de associação de erro fatal e cobrir tanto exceções quanto erros retornados por partição. [Semântica das atribuições na API oficial da Confluent](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#confluent_kafka.Consumer.subscribe)
- Para cada partição, comprovar que a recuperação preserva o próximo offset contíguo e a ordem. A confirmação depende de um efeito aceito ou de uma publicação terminal confirmada. Se o resultado da confirmação for ambíguo, a reentrega deve reutilizar a mesma identidade e os mesmos bytes e resultar em um único efeito persistido.
- Evidenciar o comportamento dos dois grupos, inclusive quando a partição passa a outro membro. Registrar grupo, tópico, partição, posição e código do broker, a nova atribuição e o primeiro progresso confirmado. Verificar disponibilidade dos consumidores e drenagem do backlog dentro da janela aplicável. O teste de regressão pode usar um coordenador simulado que devolva perda de associação após o efeito, sem interromper uma infraestrutura real.

A análise usou o código e os logs já existentes. Não houve teste, mudança no produto, reinício ou alteração dos artefatos da rodada.


## Reconciliação final

A [rodada final](evidencias/f08/referencia-complemento/f08-reference-1795208792430-8b61b6-04/report.json) foi **reprovada**, sem lacunas de medição. Recebeu 1.500 entradas iniciais com `202`; 301 tiveram primeira resposta e 1.199 atingiram falha. Das 300 continuações previstas, 60 foram enviadas e aceitas, 55 concluíram, cinco falharam e 240 não foram enviadas por ausência da primeira resposta. O snapshot final contém 1.204 casos em falha, outbox zero e lag total 1.206. O leitor capturou os 1.916 registros do intervalo Kafka fixado.

Não houve efeito duplicado nem perda irreversível comprovada. Isso não equivale a recuperação: 1.204 entradas aceitas não tiveram seu efeito esperado concluído. A consulta de integridade e os estados de falha permanecem publicados. O p95 de primeira resposta de 492,77 ms usa somente as 301 respostas presentes, deixando 1.199 entradas fora dessa distribuição; não descreve a experiência de todos os casos.

Os [registros do mock](evidencias/f08/referencia-complemento/f08-reference-1795208792430-8b61b6-04/mock-diagnostic.log), [registros da ponte](evidencias/f08/referencia-complemento/f08-reference-1795208792430-8b61b6-04/events-diagnostic.log) e [estados dos processos](evidencias/f08/referencia-complemento/f08-reference-1795208792430-8b61b6-04/consumer-states-diagnostic.json) foram coletados durante a execução, antes da limpeza. Ambos encerraram com código 1 e sem indicação de OOM. Essas consultas de diagnóstico foram somente leitura e ocorreram depois de a falha estar observada. Nenhum consumidor foi reiniciado para melhorar o resultado.

A correção pertence a uma frente posterior de robustez e operação. Deve preservar esta linha de base, provar retomada de associação/atribuição com offsets contíguos e identidades estáveis e publicar qualquer novo ensaio separadamente. Alterar um prazo ou adicionar um reinício apenas para aprovar esta rodada apagaria o comportamento que o experimento revelou.
