# C07 · Reprodução independente em clone novo

| Item | Registro de 26/11/2026 |
| --- | --- |
| Código da aplicação | `89b9e68f6473c16da898d7021b5d18be211942cb`. Clone Git local com `--no-local`, sem alterações rastreadas. |
| Ambiente do operador | Clone `/tmp/cloudwalk-c07-vx5C5Ntk/clone`; modelo instalado em `/tmp/cloudwalk-c07-vx5C5Ntk/model`. A entrega do custodiante forneceu o arquivo externo. |
| SetFit | Projeto `cloudwalk_demo_c07vx`, portas de loopback 43347 e 45347. [Três casos e mensagens Kafka](setfit.json) · [Releitura após recriar a pilha](reinicio.json). |
| Fixture | Projeto `cloudwalk_demo_c07vxfixture`, portas 43348 e 45348, volumes distintos. [Repetição dos três casos](fixture.json) · [Verificador de dois turnos](fixture-check.txt). |
| Recuperação Kafka | Projeto `cloudwalk_r01_afa77dd8c00f`. O mock retomou em 12,360 s e a ponte de resultados em 12,060 s, ambos dentro de 120 s. [Observações e resultado R01](r01.jsonl). |
| Analisador F08 | 49/49 testes em 7,809 s. A reanálise dos sete históricos e das 12.600 linhas produziu bytes idênticos ao arquivo de referência. SHA-256 `371465c899d71f6616d9b53e65905e1ae2d7b28b12d17d13f1f9a1d59b63957a`. [Referência comparada](../r02/comparacao-revisao-1.json). |

## Da abertura à resposta

Os três casos entraram pela página do simulador real usando Chrome 158.0.8127.88 e Playwright 1.61.0. O verificador selecionou os dois campos e conferiu no POST que cada **Não informar** omitiu a chave correspondente. Observou HTTP 202, consultou a API do cliente com o cookie do navegador e leu os tópicos Kafka e o PostgreSQL. A correção, a resposta e a resolução humanas usaram a API operacional. As contas Bia e Alex conferiram lista, detalhe e histórico nas duas marcas.

No e-mail da Horizonte, o canal informou Pix e o serviço inferiu Urgente em uma tentativa. O especialista de categoria recebeu zero chamadas e o de prioridade, uma. A espera na fila foi 447,619 ms, a chamada HTTP levou 217,640 ms, e o resultado Kafka foi persistido 1.084,955 ms após a criação do caso. No WhatsApp da Aurora, a entrada completa passou sem tentativa de classificação, Bia recebeu o handoff e resolveu o caso após responder. No chat, os dois especialistas pediram revisão, a supervisão corrigiu ambos e o atendente respondeu. O processo SetFit manteve PID 46, uma partida, duas escritas e duas respostas verificadas nesses casos.

| E-mail Horizonte | Identificador |
| --- | --- |
| Caso | `4134e6e6-4545-4210-b83e-894619cf6530` |
| Correlação desde o recibo | `dca3e8fd-4a6f-4f33-899d-659c6d0a83a7` |
| Tentativa do classificador | `4ca129b0-d59b-43fb-9107-634943f1e7a7` |
| Pedido em agent.requests, versão 1.1 | `c231130b-7dcd-479c-bda7-ac154dfbe2a8` |
| Resultado em agent.events, versão 1.0 | `eb1c38a4-6de2-5c05-a3f9-b66912660d06` |

A verificação usou `down` e `up` com as mesmas credenciais e volumes. A API da supervisão devolveu o mesmo estado e os mesmos IDs de mensagens em cada caso, com contagens de 3, 2 e 2. No PostgreSQL coincidiu o conjunto de campos selecionados pela [consulta do ensaio](../../../script/c06/case_snapshot.sql), incluindo classificação, tentativas, eventos Kafka, campos da auditoria e, para cada mensagem, ID, tipo de autor e sequência. [Resultado do reinício](reinicio.json).

O controle com diretório inexistente terminou em código 1 antes de iniciar os serviços. A imagem da própria C07, iniciada sem pacote e sem acesso à rede externa, respondeu à consulta de prontidão com `503 {"ready":false,"worker_pid":null,"counts":{"session_failures":2}}`. O processo com o pacote aprovado informou `ready: true`, com manifesto igual ao pin e montagem de `/model` com `RW=false`. O build desta instalação utilizou camadas já existentes no Docker do host.

## Repetir os verificadores

O [guia de instalação](../../c07.md) funciona com o código da aplicação da base registrada. O [verificador C07](../../../script/c07/reproduzir.py) acompanha esta entrega documental posterior. Para a prova automatizada, instale `requests`, `playwright` e um navegador no Python de trabalho. O ensaio usou requests 2.32.5 e Playwright 1.61.0 com Chrome. Sem Chrome instalado, use o Chromium do Playwright.

A coleta automática de memória e CPU requer **cgroup v2** no daemon Docker. Confira se `docker info --format '{{.CgroupVersion}}'` mostra `2`. Os contêineres da demo precisam expor `memory.current`, `memory.peak` e `cpu.stat` com `usage_usec` em `/sys/fs/cgroup`. Depois da subida, é possível conferir, por exemplo, com `docker exec "$PROJETO-worker-1" cat /sys/fs/cgroup/memory.current /sys/fs/cgroup/memory.peak /sys/fs/cgroup/cpu.stat`. Esse requisito se aplica ao verificador que produz o relatório de recursos.

Para preparar essas dependências em um Python isolado, use os comandos abaixo. A linha de instalação do Chromium serve para hosts sem Chrome.

```sh
python3 -m venv /caminho/novo/venv-c07
. /caminho/novo/venv-c07/bin/activate
python -m pip install requests==2.32.5 playwright==1.61.0
python -m playwright install chromium
```

Na raiz do clone da aplicação, use a mesma sessão de shell do guia de instalação. Escolha **uma** das duas fontes abaixo.

**Arquivo externo.** Indique a cópia recebida do custodiante. A função apenas lê o arquivo.

```sh
VERIFICADOR=/caminho/recebido/reproduzir.py
obter_verificador() { cat -- "$VERIFICADOR"; }
```

**Arquivo no Git.** Use o repositório da entrega e uma revisão que contenha `script/c07/reproduzir.py`. Se o arquivo veio de um squash ou cherry-pick, use a revisão que o incorporou. O clone da aplicação pode conter somente a revisão antiga.

```sh
REPO_VERIFICADOR=/caminho/do/repositorio/da/entrega
REVISAO_VERIFICADOR=5b7d1325829151dc561e9a72074a97a5993f0014
obter_verificador() { git -C "$REPO_VERIFICADOR" show "${REVISAO_VERIFICADOR}:script/c07/reproduzir.py"; }
```

Execute o bloco comum inteiro. Ele mostra o diretório novo dos resultados e encerra a sequência ao primeiro erro. A cópia para execução só recebe seu nome definitivo após a leitura e a conferência do tamanho.

```sh
(
set -eu
SAIDA=$(mktemp -d)
printf 'Diretório dos resultados: %s\n' "$SAIDA"
obter_verificador > "$SAIDA/verificador.tmp"
test -s "$SAIDA/verificador.tmp" || { echo 'Arquivo do verificador vazio.' >&2; exit 1; }
mv "$SAIDA/verificador.tmp" "$SAIDA/reproduzir.py"

verificar_casos() {
  relatorio="$SAIDA/$1"
  shift
  PYTHONPATH="$PWD" python3 -B "$SAIDA/reproduzir.py" "$@" --output "$relatorio"
  python3 -c '
import json, sys
from pathlib import Path
arquivo = Path(sys.argv[1])
if not arquivo.is_file() or not arquivo.stat().st_size:
    sys.exit(f"Relatório ausente ou vazio: {arquivo}")
casos = json.loads(arquivo.read_text())["cases"]
if not isinstance(casos, dict) or set(casos) != {"direto", "complemento", "revisao"}:
    sys.exit(f"Relatório sem os três casos esperados: {arquivo}")
' "$relatorio"
}

demo_real up
verificar_casos setfit.json --project "$PROJETO" --classifier setfit
demo_real down
demo_real up
verificar_casos reinicio.json --project "$PROJETO" --classifier setfit --after-restart "$SAIDA/setfit.json"
demo_real down

FIXTURE=cloudwalk_demo_minhafixture
demo_fixture() {
  python3 -B script/demo.py --project "$FIXTURE" --api-port 43348 --web-port 45348 --classifier fixture "$@"
}
demo_fixture up
verificar_casos fixture.json --project "$FIXTURE" --classifier fixture
demo_fixture check
demo_fixture down

python3 -B script/r01/run.py > "$SAIDA/r01.jsonl" 2> "$SAIDA/r01.log"
python3 -B -m unittest discover -s script/f08/load -v
python3 -B script/f08/load/reanalyze_r02.py > "$SAIDA/r02.json"
cmp "$SAIDA/r02.json" docs/evidencias/r02/comparacao-revisao-1.json
)
```

Cada execução do verificador cria novos casos. A etapa de reinício apenas lê os registrados no arquivo anterior. O runner R01 cria um projeto próprio e libera seus volumes ao final. Na C07, o veredito foi aprovado e o processo terminou com código 0. O caso de retomada descartou o resultado expirado e aplicou a nova resposta uma vez. O caso de handoff descartou o resultado expirado e preservou o humano. A R02 usa os arquivos de carga arquivados. O F08 mantém cinco aprovações e uma reprovação na referência selecionada e um registro histórico bloqueado por falta de captura final. A hipótese de dez mil conexões simultâneas segue sem medição. [Referência de carga](../../f08.md) · [Método de recuperação](../../r01.md) · [Método de reanálise](../../r02.md).
