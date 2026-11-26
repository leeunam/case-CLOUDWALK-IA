# Complemento local com SetFit R1

O modo `setfit` usa o pacote CPU adotado em D018. O Rails envia somente casos com campos ausentes. O serviço valida o snapshot, conta os tokens das cabeças solicitadas, envia uma linha ao adaptador residente e verifica a resposta com o runtime R1. A política de coleta pertence ao processo do modelo. A política R1 decide se os campos podem ser aplicados juntos.

## Instalar o pacote e iniciar

1. Solicite ao custodiante da entrega local `setfit-r1-package.tar.gz` (870.201.575 bytes). A distribuição do projeto fornece esse arquivo, o recibo SHA-256 e a atribuição em `entregas/modelos/`, fora do repositório Git. O operador escolhe o local de instalação. O instalador aceita o arquivo com SHA-256 `a06d4eb0fdf26f06a86b6fe6fa1f8e1bdab49fbed01647a0b8431193473e4f01`. O SHA-256 independente do manifesto aprovado é `224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872`.
2. Partindo da raiz do checkout, use Python 3.11 e um destino novo, cujo diretório pai já exista. Substitua os dois caminhos abaixo pelos seus. O pacote extraído ocupa 975.492.998 bytes de arquivos regulares. Um operador com uma exportação íntegra do diretório `package` já pode usar esse diretório como `MODEL_DIR`.
3. O build usa Docker Compose e a plataforma `linux/amd64`. A primeira construção baixa a imagem de Python por digest e as wheels dos índices públicos PyPI e PyTorch CPU. Os 73 hashes estão em `requirements-linux-amd64.lock`. A rede de inferência é interna e o volume `/model` entra em leitura. Conserve o diretório fornecido estável enquanto o serviço estiver em execução.

```sh
MODEL_ARCHIVE=/caminho/da/entrega/setfit-r1-package.tar.gz
MODEL_DIR=/caminho/da/instalacao/setfit-r1
python3 -B -m script.classification_comparison.setfit_sf2.serving.provision "$MODEL_ARCHIVE" "$MODEL_DIR"
python3 -B script/demo.py --project cloudwalk_demo_setfit --classifier setfit --model-dir "$MODEL_DIR" config
python3 -B script/demo.py --project cloudwalk_demo_setfit --classifier setfit --model-dir "$MODEL_DIR" up
```

Use os mesmos argumentos de projeto, classificador e diretório nas operações seguintes. As portas opcionais são `--api-port` e `--web-port`. O modo padrão de `script/demo.py` e de `script/publish.py` continua sendo `fixture`. O mesmo overlay funciona no roteiro de publicação após o aceite da integração. Para conferir a configuração em um projeto próprio, sem iniciar serviços ou abrir túnel:

```sh
python3 -B script/publish.py --project cloudwalk_publish_setfit init
python3 -B script/publish.py --project cloudwalk_publish_setfit --classifier setfit --model-dir "$MODEL_DIR" config
```

Para uma publicação autorizada, passe esses mesmos argumentos a `up`, `check`, `publish` e `unpublish`. Se o projeto já estiver publicado, encerre o túnel com o modo vigente antes de mudar o classificador e suba o modo escolhido com `up`.

Em modo SetFit, `publish.py check` consulta a prontidão atual do classificador e a saúde da API e do banco. Se o pacote tiver sido movido, use o caminho anterior em `--model-dir` para `down` ou `unpublish`. Para iniciar novamente, indique o diretório onde o pacote está instalado.

## Prontidão e prazos

`GET /live` verifica o supervisor. `GET /ready` retorna o PID do filho e contadores de partidas, escritas, respostas verificadas e recusas. O log `verified` associa o UUID da tentativa às durações do adaptador e da operação verificada. Somente o worker Rails compartilha a rede de inferência com o serviço. O Compose aguarda o healthcheck antes de iniciar esse worker.

Antes do READY, o processo confere os hashes dos 17 arquivos do worker, três do núcleo R1, o contrato, as políticas, o manifesto e todos os membros do pacote. O carregador original ainda confere as versões, as classes e o hash dos bytes que entrega ao Joblib. O supervisor carrega somente os tokenizadores dos dois especialistas. Cada medição usa exclusivamente as cabeças pedidas e o mesmo cálculo congelado, com tokens especiais e sem truncamento.

O serviço reserva um único slot, sem fila de espera interna. O processo principal controla o pipe e interrompe a operação quando o prazo vence, inclusive na verificação R1. Um cliente desconectado perde a resposta, mas o supervisor conclui ou interrompe sua operação antes de liberar o slot. Uma sessão defeituosa perde o READY e seu processo é encerrado e colhido. Duas partidas consecutivas sem uma resposta verificada esgotam o orçamento automático. O operador pode reiniciar o serviço após corrigir a causa. Consulte o [contrato HTTP](../../../../docs/contratos/classification-http/README.md) para os códigos de retorno.

## Verificar

```sh
python3 -B -m unittest script.classification_comparison.setfit_sf2.serving.test_serving
python3 -B -m unittest discover -s script -p test_setfit_config.py
python3 -B -m unittest discover -s docs/contratos/classification-http -p test_vectors.py
```

Na demo SetFit já pronta, este exercício compara 128 e 129 tokens nas duas cabeças e classifica quatro mensagens sintéticas de produto. A saída mostra o PID residente, as escritas no pipe e as decisões atômicas.

```sh
docker exec -i cloudwalk_demo_setfit-setfit-1 python -B - < script/classification_comparison/setfit_sf2/serving/test_product_smoke.py
```
