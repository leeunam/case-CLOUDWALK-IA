# C06/C07 · correções da revisão final

[Parecer amplo](final-review.md) · [Revisão focal](final-fix-review.md).

Os cinco achados receberam correção e verificação na worktree `.worktrees/c06-sidecar`, branch `feat/setfit-sidecar`. Base `882e1e596959fb192eb15f152eeed19da49a1942`. HEAD `977ec3f21096d66c6b462d3cc94880e4a94eb490`. A revisão focal pode consumir o intervalo BASE..HEAD. A publicação e sua repetição em ambiente real ficam com o integrador.

| Achado | Mudança | Verificação executada |
| --- | --- | --- |
| P2 · repetição de publish | Com túnel já ativo, o comando consulta separadamente os seletores em execução na API e no worker, preserva compatibilidade com imagens fixture legadas e exige o modo solicitado nos dois serviços. Em seguida chama a verificação da pilha e do endpoint privado de prontidão do SetFit. Ambos os passos precedem qualquer reconfiguração ou anúncio de sucesso. Uma divergência orienta usar `unpublish` no modo vigente. O diagnóstico identifica o serviço, sem reproduzir o ambiente. | Simulação de `Stack.publish` com túnel ativo e HTTPS saudável, usando o shell real para interpretar os seletores sintéticos. SetFit indisponível, troca fixture→SetFit, troca SetFit→fixture, worker divergente e API em modo desabilitado produziram erro, zero mutações Compose e zero anúncios. Repetições saudáveis em ambos os modos atualizaram API e web e anunciaram a URL simulada. |
| P3 · schema versionado | A versão passa a `20261126000001`; o snapshot recebe `classification_attempts.snapshot`, `lease_expires_at`, `classification_requests.provider` e `provider_mode`. O diff desse arquivo tem uma substituição de versão e quatro linhas de coluna. | `db:schema:load:primary` em PostgreSQL 17 descartável. As quatro linhas de catálogo lidas após o carregamento coincidiram com as quatro recriadas pela migração real, inclusive precisões, defaults e nulabilidade. |
| P3 · passagem direta | A classificação recebida pela API no caso direto agora exige `terminal/advanced` e `channel/channel`. A comparação existente com o PostgreSQL e a verificação de zero pedidos/tentativas seguem no mesmo fluxo. | Os dois positivos arquivados passaram. Para cada modo, a troca sintética individual da categoria, prioridade ou uma das duas origens foi recusada, totalizando oito controles negativos. |
| P3 · versões dos pedidos Kafka | O verificador compara o ID e a versão de **cada** pedido da captura com o turno/outbox. | Os dez pares arquivados dos dois modos passaram com uma cópia idêntica do evento. A alteração da versão só da segunda cópia foi recusada em cada um dos dez pares. |
| P3 · Python otimizado | O comando C06 recusa a execução otimizada no ponto de entrada, antes de processar credenciais, chamar serviços ou gravar o JSON. | Duas invocações reais em subprocessos, com `python -O` e com `PYTHONOPTIMIZE=1`, saíram com código 2 e a indicação `Use Python sem otimização`. Um audit hook teria interrompido qualquer conexão, resolução de endereço ou subprocesso Docker. O arquivo de saída ficou ausente nos dois cenários. |

## Testes e comandos

Executados a partir da worktree de C.

```text
rtk proxy python3 -B -m unittest discover -s script -p test_publish.py -v
Ran 7 tests in 0.090s
OK

rtk proxy python3 -B -m unittest discover -s script -p test_setfit_config.py -v
Ran 3 tests in 0.985s
OK

rtk proxy python3 -B -m unittest script.c06.test_aceite_integrado -v
Ran 3 tests in 1.111s
OK

rtk proxy ruff check script/c06/aceite_integrado.py script/c06/test_aceite_integrado.py script/publish.py script/test_publish.py
All checks passed!
```

O segundo grupo confere a configuração renderizada pelo Compose sem iniciar serviços e ensaia encerramento com o modelo removido usando um duplo de execução. Os sete cenários de repetição da publicação estão dentro de um dos sete testes do primeiro grupo.

## Carregamento do schema no PostgreSQL

Somente o contêiner descartável `c06-final-schema-882e1e5` e os comandos Rails temporários participaram. O PostgreSQL usou dados em tmpfs, rede `none` e nenhuma porta publicada. O Rails compartilhou apenas o namespace de rede privado desse PostgreSQL. A imagem Rails existente veio da pilha isolada C06; o schema e a migração foram montados individualmente em leitura a partir da worktree. Imagens locais PostgreSQL `sha256:6b75136145ddabf3d9a4b69660402082de7c56b734cfe50555b0674774dd742a` e Rails `sha256:2f78f7d5df56b5e5b74b850129469e36f10b88209e5d629f5579bdd96b3bcb71`.

Comandos do ensaio com a raiz da worktree em `$PWD`. Para repetir, exporte
`POSTGRES_PASSWORD` com uma senha exclusiva do PostgreSQL descartável.

```sh
rtk proxy docker run --pull=never --rm -d --name c06-final-schema-882e1e5 --network none --tmpfs /var/lib/postgresql/data -e POSTGRES_USER=cloudwalk -e POSTGRES_PASSWORD postgres:17-alpine@sha256:a77aa70e641402a21411b92b721c58d10f23b50ae5fdd2333efd22d166e1e5f7
rtk proxy docker run --rm --pull=never --network container:c06-final-schema-882e1e5 -e POSTGRES_HOST=127.0.0.1 -e POSTGRES_PASSWORD -e RAILS_ENV=test --mount type=bind,src="$PWD/backend/db/schema.rb",dst=/app/db/schema.rb,readonly cloudwalk_demo_c06i-api:latest bundle exec rails db:create:primary db:schema:load:primary
```

Saída do Rails: `Created database 'cloudwalk_test'`. A verificação seguinte rodou no mesmo banco.

```sh
rtk proxy docker run -i --rm --pull=never --network container:c06-final-schema-882e1e5 -e POSTGRES_HOST=127.0.0.1 -e POSTGRES_PASSWORD -e RAILS_ENV=test --mount type=bind,src="$PWD/backend/db/migrate/20261126000001_pin_classification_attempts.rb",dst=/app/db/migrate/20261126000001_pin_classification_attempts.rb,readonly cloudwalk_demo_c06i-api:latest bundle exec rails runner - <<'RUBY'
require "/app/db/migrate/20261126000001_pin_classification_attempts"
db = ActiveRecord::Base.connection
version = db.select_value("SELECT max(version) FROM schema_migrations")
abort "Versão do schema inesperada" unless version == "20261126000001"
sql = <<~SQL
  SELECT table_name, column_name, data_type, column_default, is_nullable, datetime_precision
  FROM information_schema.columns
  WHERE table_schema = 'public' AND
    ((table_name = 'classification_attempts' AND column_name IN ('snapshot','lease_expires_at'))
    OR (table_name = 'classification_requests' AND column_name IN ('provider','provider_mode')))
  ORDER BY table_name, column_name
SQL
before = db.select_rows(sql)
abort "Número de colunas inesperado" unless before.size == 4
ActiveRecord::Migration.suppress_messages { PinClassificationAttempts.migrate(:down) }
abort "Rollback não removeu as quatro colunas" unless db.select_rows(sql).empty?
ActiveRecord::Migration.suppress_messages { PinClassificationAttempts.migrate(:up) }
abort "Schema e migração divergiram" unless before == db.select_rows(sql)
puts "version=#{version}; schema:load == migrate:up; quatro colunas conferidas"
before.each { |row| puts row.map { |value| value.nil? ? 'NULL' : value }.join(" | ") }
RUBY
```

```text
version=20261126000001; schema:load == migrate:up; quatro colunas conferidas
classification_attempts | lease_expires_at | timestamp without time zone | NULL | YES | 6
classification_attempts | snapshot | jsonb | '{}'::jsonb | NO | NULL
classification_requests | provider | character varying | NULL | YES | NULL
classification_requests | provider_mode | character varying | NULL | YES | NULL
```

`rtk proxy docker stop c06-final-schema-882e1e5` retornou o nome do contêiner. A consulta posterior `docker ps -a --filter name=c06-final-schema-882e1e5` em formato de nomes retornou zero linhas.

## Entrega para integração

1. `f19e3e1ac11e1405395793b99776168eca7623dd` — publicação repetida e testes simulados.
2. `6de564ede91a49de91bc7f308ad82a76c88caecf` — alteração isolada do snapshot versionado da worktree. O integrador pode incorporar este commit preservando as alterações locais do usuário por três vias.
3. `977ec3f21096d66c6b462d3cc94880e4a94eb490` — verificações do aceite C06, recusa da otimização e controles focais.

`git diff --check 882e1e596959fb192eb15f152eeed19da49a1942..HEAD` retornou sem saída, e `git status --short --branch` retornou apenas `## feat/setfit-sidecar`. As evidências da matriz anterior mantêm seus hashes SHA-256 `ab25fe3ff6f618846d463a8dd2649e70ec17f91955989c99d3fc6e16937e246d` (fixture) e `6bdd2abbd2ab7ebd8137c783f99537477d9f8ec8c5417869c6442778f4326be5` (SetFit). O ensaio desta onda cobriu lógica de publicação simulada, verificações do aceite e schema real. A abertura de túnel e a repetição saudável em publicação real são os passos operacionais seguintes à re-review.
