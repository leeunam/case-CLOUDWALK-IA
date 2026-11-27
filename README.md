# Help desk multimarca

Plataforma de atendimento do TAPI Inteli/CloudWalk. Recebe solicitações em
canais simulados de chat, WhatsApp e e-mail, aplica regras de fila por marca
e encaminha ao atendimento automático ou humano. A supervisão configura
marcas, equipes, filas e capacidade, acompanha revisões e consulta a auditoria.

## Rodar a demonstração

Instale Python 3.10+ e Docker com Compose 2.24.4+. Na raiz do projeto, execute:

```sh
python3 script/demo.py up
python3 script/demo.py check
python3 script/demo.py login supervisor@example.test
```

Abra o [simulador](http://127.0.0.1:45179/) ou a
[área de operação](http://127.0.0.1:45179/analista). O último comando
mostra a credencial de demonstração criada nesta instalação. O verificador
envia mensagens sintéticas e confere resposta e reentrega via Kafka.

```sh
python3 script/demo.py status
python3 script/demo.py logs api worker outbox events mock
python3 script/demo.py down
```

O modo padrão usa dados fictícios, classificação por fixture e um atendente
simulado. O [guia de validação](VALIDACAO.md) reúne resultados, limites e
comandos dos ensaios.

### Usar SetFit R1

Obtenha o pacote portátil `setfit-r1-package.tar.gz` com o responsável pela
entrega. Os pesos ficam fora do Git. Em Linux amd64, com Python 3.11:

```sh
python3 -m script.classification_comparison.setfit_sf2.serving.provision \
  /caminho/setfit-r1-package.tar.gz /caminho/novo/setfit-r1
python3 script/demo.py --classifier setfit --model-dir /caminho/novo/setfit-r1 up
```

Na conversa do simulador, escolha **Não informar** para categoria ou
prioridade e envie uma mensagem. O SetFit tenta preencher o campo ausente.
Se a decisão exige revisão, o caso aparece em **Em revisão** na supervisão.
Use os mesmos argumentos `--classifier` e `--model-dir` ao consultar ou parar
essa instalação.

## Navegar no código

| Caminho | Função |
| --- | --- |
| [`frontend/`](frontend/) | React e TypeScript. Em `src/`, `simulator`, `staff` e `configuration` são as áreas do produto. `api`, `components` e `hooks` são compartilhados. |
| [`backend/`](backend/) | Rails API. Controllers recebem comandos, services executam operações, models persistem o domínio e jobs tratam tarefas assíncronas. |
| [`integration/`](integration/) | Ponte Python com Kafka, atendente simulado e piloto conversacional com conhecimento por marca. |
| [`contracts/`](contracts/) | OpenAPI, JSON Schemas e fixtures de API, eventos Kafka, SetFit e piloto conversacional. |
| [`script/`](script/) | Comandos de demonstração, publicação e verificações organizadas por função. |
| [`audit/`](audit/) | Dados versionados usados para reproduzir verificações. |
| [`assets/architecture/`](assets/architecture/) | Diagrama da arquitetura e fonte Mermaid. |

Consulte as [regras de atendimento e os contratos](ARQUITETURA.md) antes de
alterar os fluxos. Em trabalhos paralelos, abra uma branch e uma worktree por
tarefa a partir da mesma base. Preserve as alterações locais de outras
frentes e combine alterações de contrato antes de integrá-las.

## Testes de desenvolvimento

Execute os comandos na raiz. O Compose fornece as versões de Node, Ruby e
PostgreSQL definidas no projeto.

```sh
docker compose run --build --rm --no-deps web npm test
docker compose run --rm --no-deps web npm run build
docker compose up -d --wait db
docker compose run --build --rm --no-deps -e RAILS_ENV=test api bundle exec rails db:prepare test
docker compose run --rm --no-deps api bundle exec ruby /workspace/script/check_contracts.rb
python3 -m unittest discover -s contracts/classification-http
```

A suíte Python de contratos usa `jsonschema`. Os arquivos remanescentes em `docs/` são insumos versionados de avaliações
anteriores. Alguns scripts de classificação mantêm caminhos e hashes
fixados pela avaliação do SetFit. O [guia de validação](VALIDACAO.md) aponta
para os relatórios históricos.
