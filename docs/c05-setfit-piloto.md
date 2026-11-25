# C05-SF1 — piloto local de categoria com SetFit

O piloto usa 16 relatos sintéticos do desenvolvimento R2 2.0.0 com categoria
ausente. Os rótulos passaram por revisão exploratória com IA. Os três assuntos são
`pix`, `payouts` e `terminal`. A saída `informacao_insuficiente` encaminha
o caso para revisão.

## Como o piloto funciona

Em cada divisão, o SetFit ajusta o encoder MiniLM multilíngue usando pares
de relatos do treino. Pares com o mesmo rótulo orientam o modelo a aproximar
suas representações. A regressão logística aprende a decidir a partir dessas
representações ajustadas. Na validação, o modelo recebe apenas o texto e
escolhe a saída com maior score da cabeça. Os scores ficam no registro como
valores não calibrados, sem limiar.

A validação cruzada usa quatro divisões estratificadas com semente 42. Cada
divisão começa com os mesmos pesos originais, treina em 12 relatos e valida
em quatro. Cada ID é avaliado uma vez. A conferência de duplicatas normaliza
Unicode, caixa e espaços. O texto enviado ao modelo preserva a fonte. O
piloto trabalha só com IDs do desenvolvimento e só com categoria.

O encoder recebe uma época, cinco iterações de amostragem de pares, batch
oito e taxa de aprendizado `2e-5`. O executor usa `TrainingArguments` do
SetFit, registra os argumentos aplicados e verifica o número de passos, a
alteração de um peso do encoder e as classes da cabeça treinada. Os textos
tinham de 18 a 45 tokens com os tokens especiais. Todos cabiam no limite
de 128 sem truncamento.

## Resultado de 25/11/2026

O SetFit acertou **15 de 16 decisões (93,75%)**, com F1 macro de **0,9365**.
Acertou os 12 relatos com categoria definida e enviou para revisão três dos
quatro que precisavam dela. O relato `jev-013` recebeu `terminal` quando
deveria ir para revisão.

| Saída esperada | Casos | Precisão | Revocação | F1 |
| --- | ---: | ---: | ---: | ---: |
| Pix | 4 | 100% | 100% | 1,0000 |
| Repasses | 4 | 100% | 100% | 1,0000 |
| Maquininha | 4 | 80% | 100% | 0,8889 |
| Revisão | 4 | 100% | 75% | 0,8571 |

O modelo atribuiu categoria a 13 de 16 relatos (81,25%), incluindo os 12
classificáveis e um que precisava de revisão. Cada divisão treinou com
120 pares amostrados e concluiu 15 passos de otimização. Os quatro encoders
começaram com o mesmo peso original monitorado e o ajustaram no treino. As
quatro cabeças aprenderam as saídas previstas.

| Etapa | Tempo observado |
| --- | ---: |
| Download e verificação do snapshot público | 415,71 s |
| Carregamento dos quatro modelos | 4,10 s |
| Treino do encoder e da cabeça nas quatro divisões | 62,43 s |
| Tempo registrado pelo executor | 70,59 s |
| Inferência por texto, p50 | 15,188 ms |
| Inferência por texto, p95 | 21,078 ms |

O tempo de inferência inclui a classificação e a extração da saída com o
modelo em memória, em um Intel Core i5-1345U. Cada divisão usou o primeiro
texto de treino como aquecimento. Os percentis usam as 16 inferências de
validação pelo posto mais próximo. Nesse tamanho de amostra, p95 é o maior
valor medido.

A amostra sintética tem três exemplos por saída em cada treino. O resultado
permite investigar como o modelo trata os relatos já disponíveis. A adoção,
a calibração, a comparação sob o protocolo de atendimento e a integração
seguem em espera.

[Seleção, divisões e tokens](evidencias/c05/setfit-piloto-01/data.json) ·
[Revisão e hashes do modelo](evidencias/c05/setfit-piloto-01/model.json) ·
[Decisões e scores por relato](evidencias/c05/setfit-piloto-01/predictions.jsonl) ·
[Ambiente, tempos, treino e matriz de confusão](evidencias/c05/setfit-piloto-01/run.json)

## Reprodução

Na raiz do checkout, com Python 3.11 em Linux x86-64:

```sh
rtk proxy sh script/classification_comparison/setfit_pilot/install.sh
rtk proxy sh script/classification_comparison/setfit_pilot/run.sh \
  --output script/classification_comparison/setfit_pilot/.cache/reproducao
```

O instalador usa o conjunto congelado de dependências e PyTorch CPU. Ele baixa
uma lista fechada de arquivos públicos do
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` na revisão
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. O modelo é carregado localmente
com Safetensors. A execução roda offline em CPU com duas threads configuradas.
Informe um diretório novo para cada execução.

O instalador tem 30 minutos e registra cada tentativa no caminho
`.cache/installs/attempt-*` dentro de `setfit_pilot`. O `status.json`
indica a etapa, o resultado e o código de saída. O `commands.log` reúne as
mensagens dos comandos. Uma falha pode ser localizada na preparação do
ambiente, na instalação e checagem das dependências, no download ou na
verificação do modelo. Cada tentativa mantém seu próprio registro.

Um processo separado controla os 15 minutos acumulados das quatro chamadas
de treino. A carga dos modelos e as inferências ficam fora desse relógio.
Se o prazo vencer ou houver cancelamento, esse processo encerra o grupo
do executor e grava a interrupção em `run.json`, preservando as divisões e
previsões já gravadas. O vencimento do prazo tem código `124` e o
cancelamento por Ctrl+C tem código `130`.

Na execução registrada, pip e o provisionador rodaram em processos separados
na worktree do piloto. Depois da instalação, as versões observadas foram
congeladas em `requirements.txt`. O `pip check`, os imports e a checagem
de sintaxe passaram. Uma conferência independente recalculou as métricas
e os percentis a partir das 16 decisões, validou os hashes das fontes e
confirmou a separação de treino e validação. A instalação limpa com o
script agregado segue pendente. Os controles de interrupção foram
verificados separadamente com subprocessos locais simulados.

```sh
rtk proxy python3 -B script/classification_comparison/setfit_pilot/test_supervise.py -v
```

### Conferência das evidências registradas

O código do commit `bfa67b45a40afa09a9ff2eb29089b1841045e87a` gerou os
quatro arquivos de evidências. A versão atual inclui a correção dos
controles de interrupção. Confira os hashes do executor registrado
contra o conteúdo do commit histórico.

```sh
rtk proxy python3 -B - <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import subprocess

commit = "bfa67b45a40afa09a9ff2eb29089b1841045e87a"
runner = "script/classification_comparison/setfit_pilot"
evidence = Path("docs/evidencias/c05/setfit-piloto-01/run.json")
recorded = json.loads(evidence.read_bytes())["runner_sha256"]
for name, expected in recorded.items():
    source = subprocess.check_output(["rtk", "proxy", "git", "show", f"{commit}:{runner}/{name}"])
    if sha256(source).hexdigest() != expected:
        raise SystemExit(f"Hash histórico divergente: {name}")
print(f"OK: {len(recorded)} hashes históricos conferem")
PY
rtk proxy git diff --exit-code bfa67b4 -- docs/evidencias/c05/setfit-piloto-01
```

[Especificação do experimento](planejamento/classificacao-comparativa/setfit-piloto.md) ·
[Lista congelada de arquivos](../script/classification_comparison/setfit_pilot/model-lock.json) ·
[Dependências](../script/classification_comparison/setfit_pilot/requirements.txt)

## Exercício

Abra a previsão de `jev-013`. Localize sua divisão em `data.json` e confirme
que o relato aparece na validação, fora dos IDs de treino daquela divisão.
Compare os quatro scores e encontre na matriz de confusão a célula que
registra esse erro.
