# F08-A — experimento de carga

O ensaio compara a mesma carga com o Kafka disponível e durante uma interrupção programada. A unidade da hipótese é a entrada com HTTP `202`: depois do aceite, a cadeia de entrega deve produzir os efeitos esperados e escoar, inclusive quando houver reentrega. A carga, os limites de referência e os patamares exploratórios são parâmetros deste experimento.

## Executar na raiz da worktree

Requer Linux, Python 3.11+, Docker com acesso ao daemon local, Docker Compose com suporte a `!reset` e `!override`, e acesso às imagens e dependências de build. O runner usa a imagem k6 2.3.0. Para executar todos os testes locais, também é necessário o k6 no host e permissão para abrir sockets TCP em loopback.

```bash
rtk proxy python3 -B -m unittest discover -s script/f08/load -v
rtk proxy python3 -B script/f08/load/run.py config
rtk proxy python3 -B script/f08/load/run.py smoke
```

O smoke oferece 15 casos em três segundos e observa por mais 20 segundos. Para verificar o mecanismo de interrupção em uma execução curta separada:

```bash
rtk proxy python3 -B script/f08/load/run.py smoke --seconds 12 --fault-after 3 --fault-seconds 5 --observe-seconds 25
```

A execução completa pertence ao chat central, com a máquina livre de outros benchmarks:

```bash
rtk proxy python3 -B script/f08/load/run.py reference
rtk proxy python3 -B script/f08/load/run.py ramp --stage 5:60 --stage 10:60 --stage 20:60 --stage 40:60
rtk proxy python3 -B script/f08/load/run.py human
rtk proxy python3 -B script/f08/load/run.py chat
```

| Cenário | Parâmetros padrão |
| --- | --- |
| Referência | Seis rodadas alternadas, três por condição. Cinco minutos a 5 novos casos/s e 120 s de observação após a carga. Na condição de falha, solicitar parada aos 60 s e a partida após 30 s de broker parado. |
| Aumento progressivo | Patamares de 5, 10, 20 e 40 novos casos/s, com 60 s cada e 120 s de observação final. Compare oferta, aceite, tempo até resposta e backlog por patamar. |
| Humano | 2 novos casos/s por 10 s e 120 s de observação. Entradas sintéticas de maquininha com prioridade avançada geram handoff. Os analistas do seed respondem, aguardam o cliente, retomam e resolvem, pelos endpoints canônicos. Registra estado, carteira, trabalho ativo e limite do perfil observado. |
| Chat | Patamares seriais de 100, 1.000 e 10.000 sessões, com preparação/conexão distribuída em 120 s, janela estável de 300 s e 20 s de observação depois. Uma escrita por sessão a cada 100 s, com fases distribuídas. No patamar máximo, o alvo é 100 mensagens/s. |

Cada rodada usa uma pilha nova no projeto `cloudwalk_f08_load`, sem portas publicadas e com rede interna e volumes próprios. O runner exige um daemon por socket Unix local, recusa recursos preexistentes, usa segredos sintéticos e remove apenas os recursos do projeto que iniciou. A prontidão verifica a API e a atribuição das três partições de cada grupo operacional. O aquecimento faz um envio real e aguarda a resposta e os offsets antes de iniciar a carga. A interrupção programada afeta apenas o Kafka. As políticas atuais de entrega e retentativa do produto ficam em vigor. Uma falha de limpeza bloqueia a rodada, preserva suas medidas e interrompe o lote com código diferente de zero. A matriz identifica cada rodada que ficou sem execução e o motivo.

Use `--help` para ver os parâmetros. Exemplos de ajustes são `--seed`, `--vus`, `--observe-seconds` (até 120), `--rounds` por condição e `--chat-target` repetível. Alterações de parâmetros aparecem no manifesto. Para reproduzir apenas uma rodada exploratória de chat, use `chat --chat-target 100`.

## Metodologia e interpretação

- **Distribuição.** A referência planeja 1.500 entradas e 300 continuações. Cada uma das seis combinações entre Aurora, Horizonte, chat, WhatsApp e e-mail recebe 250 iniciais e 50 continuações. Todos os casos entram como `pix/basic`; a classificação é válida e o Jev está desabilitado. O relatório verifica solicitações e tentativas de classificação observadas. O mock atual tem atraso artificial desativado por implementação. A latência medida inclui execução da aplicação, entrega, consumo e rede.
- **Dois turnos.** O k6 mantém a oferta de novas entradas em modelo aberto. Um processo separado consulta em lote as continuações elegíveis a cada 250 ms e programa o envio para a primeira resposta registrada no banco mais 5 s. Se a resposta for vista tarde, o atraso do envio fica registrado. Quando a janela termina antes do envio, a continuação fica no plano com seu motivo. A continuação retém conversa, cliente, marca e canal, e usa um novo `source_event_id`. Um reenvio para investigar idempotência deve usar o mesmo ID e os mesmos bytes do plano. O ensaio registra a primeira tentativa de cada envio.
- **Relógios.** Aceite é o intervalo entre o início da solicitação e o retorno HTTP `202`. Resposta persistida usa o `created_at` UTC da mensagem de IA associada à rodada pelo `result_event_id`, subtraído do início do webhook. Esse carimbo vem da gravação da mensagem na transação. O instante exato do commit fica indisponível. A consulta lê depois do commit, e seu atraso aparece numa métrica própria para a amostra elegível a continuação. O relatório mostra a diferença observada entre relógios e o número de latências negativas excluídas. Os percentis usam posição de ordem superior, com tamanho da amostra em cada rodada. O início anunciado pelo k6 e os horários de cada estágio ficam disponíveis para conferência.
- **Taxas e gargalo.** O aceite inicial tem denominador de todas as entradas planejadas, e o relatório também mostra o denominador das efetivamente emitidas. Cada estágio guarda seus próprios limites de IDs. O primeiro slot ocorre no início. O período que o k6 usa para distribuir os slots recebe uma margem de até 10 ms no estágio inteiro, limitada a meio intervalo entre chegadas, para excluir o slot da fronteira final. A duração da carga e o total planejado continuam definidos por taxa × segundos. O campo `generator_accounting` distingue chamadas registradas, IDs únicos, entradas planejadas sem oferta, iterações excedentes suprimidas e descartes brutos informados pelo k6 por falta de VUs disponíveis. Elas indicam um déficit de oferta e podem se acumular quando o destino demora e mantém os VUs ocupados. Compare os descartes com CPU/RAM do gerador, tempo HTTP, recursos das aplicações e progresso das filas antes de atribuir a causa. A série por segundo usa a emissão, o fim do HTTP e os timestamps da persistência. Conclusão de turno de IA e resolução de caso são contagens distintas. O mock normalmente deixa o caso aberto depois da primeira resposta e resolve no segundo turno.
- **Backlog e recuperação.** SQL somente leitura, a cada 2 s, registra outbox pendente e falha, atendimentos aguardando entrega ou retorno e conexões de banco por banco/estado. A cada 5 s, os offsets finais e os próximos offsets confirmados medem lag por partição/grupo; sem offset confirmado, usa-se o início do log, conforme `auto.offset.reset=earliest` do produto. Uma amostra indisponível fica nula. O período decorrido até a primeira leitura Kafka válida após a partida inclui a prontidão e a resolução da amostragem. O indicador de drenagem após prontidão é a primeira observação de zero pendências e lag zero recente. A meta final usa o último carimbo exigido para cada turno com efeito ou aceite: mensagem da IA, conclusão do turno, publicação da outbox, auditoria do resultado e, no segundo turno, resolução persistida no caso. Exige também zero pendências em SQL e lag zero em leituras iniciadas depois da última chegada prevista e do último efeito, concluídas até o limite. A última amostra SQL deve ter começado nos 5 s finais e a última amostra Kafka nos 12 s finais. Os intervalos representam a resolução da amostragem. O snapshot posterior por si só é insuficiente para provar drenagem. O manifesto registra o instante do snapshot, que pode ocorrer depois do limite para incluir requisições já iniciadas. Amostras SQL, Kafka, Docker e da consulta de continuações incluem tempo gasto pelo observador. Os máximos são observados por amostragem.
- **Reconciliação.** Use o plano, os recibos, offsets, SHA-256 dos bytes e os efeitos no PostgreSQL. A chave de entrada combina canal e `source_event_id`; o relatório liga caso, correlação, geração, rodada, IDs de request/resultado, mensagens e auditoria. Cada turno concluído exige um registro de requisição em `agent.requests` e um de resultado em `agent.events`, ligados por tipo, IDs de evento, caso, turno, correlação e referência à requisição. A reconciliação guarda as partições e os offsets encontrados. Uma captura incompleta ou sem par causal bloqueia a medição e preserva a contagem de efeitos registrados no banco. Um evento repetido em múltiplos offsets é uma reentrega observada no broker. Duplicação de efeito exige mais de um efeito esperado para a mesma identidade no banco. Uma entrada visível no banco sem `202` é ambiguidade de aceite. Ausência de resposta com trabalho em voo fica pendente. Falha de outbox, descarte, timeout do agente ou evento terminal de falha aparecem com evidência quando disponível. A ausência de um efeito que o recibo ou aplicação confirmaram, com snapshot disponível, conta como perda comprovada. Cada linha do arquivo de reconciliação guarda o estado. O relatório mantém as rodadas separadas.
- **Chat.** Cada VU autentica uma sessão sintética, abre um caso inicial e usa o cookie de sessão, CSRF e o protocolo Action Cable. O indicador simultâneo depende de `confirm_subscription` e do fechamento ou troca de assinatura. Escritas usam a API real do simulador e as notificações acionam leitura incremental. Antes da primeira escrita periódica, uma sessão fecha a assinatura confirmada com cursor positivo, escreve pelo HTTP no mesmo caso e aguarda confirmação da mesma assinatura. A leitura incremental precisa usar o cursor anterior e incluir o ID da mensagem de cliente persistida depois dele. Abertura de outro caso ou leitura inicial com cursor zero invalida a prova. Preparação e prova de recuperação ficam fora da taxa principal. Cada escrita é classificada pelo `case_id` retornado como abertura ou continuação. A preparação também gera carga e aparece separada no relatório.

A cobertura de recursos indica quais serviços tiveram CPU e RAM observadas, quais medidas do host existem e quantas amostras falharam. Ausência dessas medidas bloqueia a avaliação e preserva as metas e falhas de produto observadas. Em smokes curtos, o gerador pode terminar antes da coleta Docker e a CPU do host depende de duas leituras.

O observador abre um processo independente para cada leitura Kafka, inclusive na prontidão e na captura final. A consulta periódica tem prazo total de 8 s, e o custo inclui a criação do processo e da conexão. Uma saída inesperada, um timeout ou uma resposta incompleta gera uma amostra de lag indisponível com motivo. O processo que consulta SQL e agenda as continuações segue trabalhando. A captura final tem prazo próprio de 52 s e grava os registros Kafka diretamente no JSONL. O relatório exige contagens coerentes entre os offsets esperados, o total lido e o arquivo de registros.

## Artefatos por rodada

| Artefato | Conteúdo |
| --- | --- |
| `manifest.json` | Revisão Git, hash dos scripts, seed, parâmetros, horários UTC, versões, IDs de imagens, limites, réplicas, concorrência, prontidão, aquecimento, falha e inventário. |
| `plan.json`, `k6-console.jsonl`, `k6-summary.json`, `followups.jsonl` | IDs e bytes reconstruíveis, eventos do gerador, contadores do k6 e continuações com timestamps. |
| `sql-samples.jsonl`, `kafka-lag.jsonl`, `resources.jsonl`, `followup-samples.jsonl` | Evolução temporal, CPU/RAM dos serviços e gerador, memória/CPU do host, custos de amostragem e conexões do banco. |
| `kafka-baseline.json`, `kafka-offset-range.json` | Offsets por tópico e partição depois do aquecimento e intervalo efetivo da captura final. |
| `persistence.json`, `kafka-records.jsonl`, `reconciliation.jsonl` | Efeitos persistidos, metadados de Kafka lidos por intervalo de offsets sem confirmar consumo, e comparação por identidade. |
| `report.json`, `report.md`, `matrix.json`, `matrix.md` | Medidas, metas, estado aprovado/reprovado/bloqueado e comparação lado a lado das rodadas executadas. |

O diretório padrão é `script/f08/load/results/`. O esquema dos artefatos principais está em `script/f08/load/results.schema.json`. Os relatórios omitem senhas, segredo de assinatura, cookies, tokens CSRF e IDs de sessão. Os corpos do plano contêm apenas dados sintéticos.

## Verificação nesta entrega

| Verificação | Resultado observado |
| --- | --- |
| Testes automatizados | 32 aprovados, incluindo os dois ensaios TCP em loopback com o k6, o caso lento com descartes e as regressões de drenagem, reconexão, integridade, recursos e limpeza. |
| Compose | v5.1.0 compilou 13 serviços incluindo os perfis opcionais. Rede interna, volumes próprios e nenhuma porta publicada. |
| Smoke real | Rodada `f08-smoke-1795206209189-d05f95-01` em `6d0feb5`, aprovada. 15/15 entradas com HTTP 202 e 3/3 continuações concluídas. p95 do aceite de 102 ms e da primeira resposta persistida de 381,83 ms. Leitura de 36/36 registros Kafka, com par causal para os 18 turnos. Cinco amostras de recursos, nenhuma perda ou duplicação comprovada e limpeza concluída. A tentativa anterior em `dfd4bdb` bloqueou no aquecimento por incompatibilidade de tipos SQL e foi limpa. |
| Smoke após isolar o leitor Kafka | Rodada `f08-smoke-1795206778592-ba23dd-01` em `e099be4`, com Kafka disponível. Aceitou 15/15 iniciais e concluiu 3/3 continuações, com 36/36 registros Kafka. O p95 foi de 109 ms no aceite e 391,30 ms até a primeira resposta persistida. As cinco amostras de lag custaram p50 de 98 ms e p95 de 107 ms, incluindo o novo processo e sua conexão. A captura final levou 104 ms. Limpeza concluída. |
| Referência, aumento progressivo, humano e chat | Execuções reservadas ao chat central. A capacidade e o comportamento sob interrupção dependem da pilha real. |

**Exercício.** Depois de um smoke real ou da referência, escolha um caso aceito durante a interrupção. Compare `request_ms` com `ai_persisted_timestamp_ms - sent_ms` na reconciliação. Se o segundo tempo estiver indisponível, use o estado da linha e as amostras de outbox/lag para identificar se o trabalho ainda estava pendente ou se uma falha foi registrada.
