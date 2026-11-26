# SF2-03/04 · Relatório do aceite combinado da onda 2

**DONE · aceite combinado aprovado com fixtures na base corrigida.** O pré-voo íntegro passou. As quatro sondas de divergência entre os 17 membros produziram oito recusas específicas, uma na coleta e outra no congelamento por membro, mantendo fixos índice e argv. A restauração do espelho reproduziu o pré-voo original.

## Correção do roteiro de reuso · espelho validado antes da cópia

**DONE.** Correção focal do achado P2 na branch `feat/sf2-integracao`, worktree `.worktrees/sf2-integracao`. Base de revisão `4f219583d9895332ce5511ca4d5c8b41250dd2bd`, entrega `9507887152b86a76901621fc38838e088ae2af82`. O diff desta correção possui exclusivamente o roteiro, seus controles de recusa e as instruções de reprodução em `docs/evidencias/c05/sf2/integracao-onda2/`.

O reuso lê o recibo histórico autenticado e exige o hash correto do índice e do manifesto do pacote antes de interpretar suas chaves. A configuração completa precisa corresponder aos papéis, argumentos e caminhos definidos pela factory de QA. Os caminhos dos membros do modelo são derivados de seu manifesto autenticado. O histórico liga os bytes da política, catálogo, validação, pacote e argv. Como ele não fornece um digest do documento inteiro de configuração, os campos restantes só podem ter os valores fixos autorizados pela factory. Nenhum desses campos amplia a lista de arquivos copiados.

O roteiro confere por hash o protocolo que autoriza os caminhos de metadados públicos. O único arquivo de inicialização do avaliador fora dos papéis da captura tem caminho e hash fixos da base aceita. A lista completa de origens e destinos exige nomes relativos canônicos e arquivos regulares de origem. Os caminhos resolvidos precisam coincidir com os locais autorizados na worktree e no espelho. Qualquer redirecionamento por link ou destino já existente impede a cópia. O novo recibo de pré-voo deve coincidir com o histórico salvo a transição exata de `evaluation/workflow.py`, entre os dois SHA aceitos. Somente então o roteiro cria os diretórios do espelho e copia. O diretório de saída é novo e privado ao usuário; a execução pressupõe a worktree e arquivos da fixture sob sua custódia.

**Verificação executada na worktree.**

```sh
sf2_python=../sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python
qa=docs/evidencias/c05/sf2/integracao-onda2
rtk proxy env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "$sf2_python" -B "$qa/test_espelho.py" -v
rtk proxy env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "$sf2_python" -B "$qa/verificar.py" \
  /tmp/sf2-onda2-qa-fix2-4f21958 --fixture-anterior /tmp/sf2-onda2-integracao-237df80-b
```

Os seis testes focais passaram. Cada um exigiu o motivo específico de recusa, zero chamadas a `shutil.copyfile` e preservação do marcador inofensivo. As situações foram índice trocado, caminho de configuração trocado, diferença no papel argv da captura, componente de subida, link de origem externo e destino resolvido fora do espelho. Todos os arquivos de controle foram criados em diretórios temporários. O log está em `/tmp/sf2-onda2-qa-fix2-controles.log`, SHA-256 `be11b9d0cfe205bd9820c0f722604456850c546968b29ec0a937616a198208d4`.

A rechecagem normal reutilizou a fixture numérica original, sem iniciar worker ou fazer inferência. O roteiro produziu `passed/0`, os dois pré-voos íntegros e as oito recusas esperadas. O recibo em `/tmp/sf2-onda2-qa-fix2-4f21958/recibo.json` é idêntico byte a byte a `recibo-custodia.json`, SHA-256 `0141eb2db83b00fcb8cb06a8398e8c37c26155aa1b4b246e2ae16f9ca3288e49`. O SHA do primeiro recibo permanece `ce8d97b3a51109e11830ba9aeb0c7edbc9c643ea710628535bd155f000fb1297`.

**Autorrevisão.** Os dois arquivos Python foram analisados sintaticamente. Conferi a ordem das validações, a lista integral antes da primeira cópia, os seis controles, a comparação binária com o recibo anterior e o alcance do commit. `git diff --check 4f21958 HEAD` passou e a worktree terminou limpa, sem merge ou push.

## Rechecagem focal após a correção SF2-04

| Referência | Valor |
| --- | --- |
| Base desta revisão | `8da95a7a6852da01d15c6dc04a677f2055e6d046` |
| Head da nova evidência | `4f219583d9895332ce5511ca4d5c8b41250dd2bd` |
| Branch e worktree | `feat/sf2-integracao` em `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-integracao` |
| Recibo focal | [recibo-custodia.json](../integracao-onda2/recibo-custodia.json) · `0141eb2db83b00fcb8cb06a8398e8c37c26155aa1b4b246e2ae16f9ca3288e49` |
| Comando de QA | `verificar.py /tmp/sf2-onda2-custodia-8da95a7-final --fixture-anterior /tmp/sf2-onda2-integracao-237df80-b`, Python 3.11.13 pinado de 03 com `-B`, ambiente limpo e modo offline |
| Mudança de runtime em relação à primeira rodada | `evaluation/workflow.py` · SHA-256 observado `951feaf647ba124c3559f3b46da9da559bfc4d2cfa8fc139fa60d0d3e35e3f09` |

**Reexecutado.** Antes das sondas, a QA conferiu o SHA-256 do recibo histórico e os bytes de sua captura, frames, journal e controles. O pré-voo do espelho íntegro coincidiu com o do checkout corrigido. Entre esse pré-voo atual e o recibo da coleta histórica, o único papel com digest diferente foi o próprio código do fluxo de conferência. O SHA-256 do índice foi `60b16a6772f648055f572c9a8f96ca8e654972ae6bddee2ec4050304bc18ae69` e o do argv, `deb5c98a40813b81f6001ba5aee0b58bee2920118d6f429b769366858ccd7066`. Ambos permaneceram fixos durante as quatro sondas. Cada verificação iniciou em processo que carregou os módulos do espelho.

| Sonda individual | `validate` | `freeze` |
| --- | --- | --- |
| `adapter/decide.py` | Saída 1 pelo SHA do membro | Saída 1 pelo SHA do membro |
| `adapter/__main__.py` | Saída 1 pelo SHA do membro | Saída 1 pelo SHA do membro |
| `contracts/__init__.py` | Saída 1 pelo SHA do membro | Saída 1 pelo SHA do membro |
| `contracts/ipc.py`, controle positivo obrigatório | Saída 1 pelo SHA do membro | Saída 1 pelo SHA do membro |

Cada chamada exigiu a mensagem de divergência com o caminho exato. Nenhuma criou execução do worker ou liberação. A prova também exigiu retorno ao recibo íntegro após restaurar os arquivos. O roteiro gravou `passed`, código 0 e o motivo antes de terminar. Na autorrevisão, suprimiu-se deliberadamente a recusa na coleta do último controle e simulou-se saída `eligible`. O roteiro gravou `failed`, código 1 e motivo identificando `contracts/ipc.py` e essa saída inesperada. O recibo de diagnóstico desse teste está em `/tmp/sf2-onda2-custodia-8da95a7-falha-positivo/recibo.json`.

**Reaproveitado.** Os fontes do worker, do supervisor de transporte, das regras e contratos de decisão, do extrator de scores e do replay conservaram as versões aceitas na primeira rodada. Permanecem válidas as observações históricas de READY, ausência de aquecimento, projeção, veto integral, 90 IDs, 120 vetores idênticos, cinco controles, 0/225 políticas elegíveis e sentinela fechada. O novo parecer de custódia reutilizou a configuração e o pacote sintéticos e dispensou uma nova coleta. As durações e os hashes antigos continuam no seu recibo original, preservado byte a byte.

**Alcance.** Ambos os testes usam código local, intérprete e argv sob custódia do operador. Este aceite das implementações é independente de qualificação de modelo e de autorização para SF2-05. O final reservado permaneceu fechado. A autorrevisão conferiu o parse do roteiro, os links, o conteúdo dos dois recibos, os oito diagnósticos e `git diff --check 8da95a7 HEAD`. O commit contém três arquivos de QA, a worktree está limpa e a integração Git cabe ao integrador.

**Exercício.** Compare o erro de `contracts/ipc.py` entre os dois recibos. Identifique por que a recusa na coleta evita que a medição comece com código diferente do aceito.


## Rodada histórica na base 237df80

**BLOCKED naquela base.** A captura, a extração de scores, o replay e o bloqueio do final funcionaram com fixtures. A comparação de fontes no congelamento não identifica alterações no adaptador efetivamente invocado. Devolver a SF2-04 para correção, acordando com 03 o formato verificável do artefato. A SF2-05 depende da aprovação desse vínculo.

| Referência | Valor |
| --- | --- |
| Base com as duas implementações aceitas individualmente | `237df80b4d27229fe79456f943cc11dc2b31f066` |
| Head da evidência de QA | `eef5c148faf62d5986abe1f13194bc90e6cc8e68` |
| Branch e worktree | `feat/sf2-integracao` em `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-integracao` |
| Evidência versionada | [Roteiro e instruções](../integracao-onda2/README.md) e [recibo](../integracao-onda2/recibo.json) |
| SHA-256 do recibo de QA | `ce8d97b3a51109e11830ba9aeb0c7edbc9c643ea710628535bd155f000fb1297` |

## O que foi executado

O processo recebeu um ambiente limpo, HF offline e o Python 3.11.13 disponibilizado em leitura por 03. O roteiro redirecionou HF_HOME e XDG_CACHE_HOME para a saída temporária. O loader do encoder indicou explicitamente .cache/transformers da worktree de integração. A QA não mediu escritas no cache. O comando `training check` conferiu 73 pins e os dez arquivos do snapshot na revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. SetFit 1.2.0, PyTorch 2.12.0+cpu e Transformers 5.8.1. O snapshot de pesquisa participou apenas da conferência de integridade. A inferência usou o BERT sintético de uma camada e oito dimensões criado pela factory `training/test_package.py`, com as duas cabeças constantes e sem ajuste de parâmetros.

Os 150 identificadores numéricos de treino serviram ao manifesto contratual de fixture. Os 90 textos passados ao worker durante a coleta foram `validation-0` a `validation-89`, gerados pelos helpers dos contratos. A construção do pacote selou os componentes da factory com os identificadores da nova validação e o freeze dela. Todo componente executado pelo worker veio desse pacote. O controle fixo `_fixture_worker` e seus hashes convencionais foram usados apenas na medição de transporte separada. Não houve treino, API de classificador, instalação, acesso a credenciais, acesso às narrativas do estudo ou abertura da partição reservada.

1. O supervisor de 04 executou o harness de 03, com observadores que delegam às streams e ao método de score reais da fixture. Registrou READY antes do primeiro envio e de qualquer forward. Em seis decisões, o conjunto de chaves de cada entrada ficou restrito à versão, ID, texto, canal, máscara e catálogo. Canal completo e valor inválido produziram zero chamadas. Categoria em branco e prioridade nula chamaram apenas o alvo correspondente. Com ambos ausentes e corte de controle 0,90 em categoria, a categoria revisou, a prioridade conservou a escolha bruta `urgent` e o complemento aplicado ficou vazio.
2. Em um processo separado, o ponto de entrada normal de 03 carregou o pacote, emitiu somente READY e recebeu EOF. Foram observadas zero invocações de módulo Torch, `SentenceTransformer.encode` e `SetFitModel.predict_proba` durante esse controle de inicialização. A coleta cronometrada usou o worker normal sem observadores.
3. `evaluation validate` iniciou um worker persistente com a política de coleta, com tau 0,50 e delta 0 por campo. Os 90 frames chegaram na ordem exata, seguidos dos cinco controles. Os 95 registros do journal foram válidos, e a captura selou os bytes dos frames e das durações em arquivos separados. `training scores` recebeu os MESMOS frames e seu hash selado. A igualdade de objetos JSON incluiu cabeçalhos, ordem de classes, erros e linhas de scores. Os 120 vetores coincidiram também com os vetores dos frames. A serialização ordenada/indentada de 03 e a compacta de 04 geraram hashes de arquivo distintos, como previsto.
4. O replay da mesma coleta avaliou 225 combinações e a linha de base argmax. Zero políticas elegíveis com o classificador constante, validação `failed`, sem `policy.json`. `evaluation freeze` recusou a grade, e não criou release. A tentativa de `execute` com sentinela de QA encerrou na falta de `release.json`, antes da abertura da sentinela, do registro de exposição e de criar saída final. O caso positivo independente da SF2-04 já havia recebido revisão individual e não foi repetido.
5. Em cópias temporariamente alteradas/restauradas, uma mudança só de bytes no argv ou na política invalidou a captura no congelamento. Uma mudança nos frames ou no journal divergiu do SHA-256 do selo. Trocar o corte de categoria da coleta por 0,60 foi recusado antes da criação do diretório de execução. Todos os ensaios de replay/extração reutilizaram os frames arquivados.

## Achado impeditivo · fontes do worker

A especificação SF2, seção 7, exige congelar fontes e o adaptador. O ensaio entregou um índice explícito com hash dos 16 membros do inventário de treino de 03 e do ponto de entrada do worker. O índice contém os módulos de contrato executados. Seu SHA-256 é `60b16a6772f648055f572c9a8f96ca8e654972ae6bddee2ec4050304bc18ae69`.

O formato entregue em `cfg.adapter` é um objeto JSON com a única propriedade `files`. Cada chave desse mapa é um caminho POSIX relativo à raiz da worktree, cada valor é o SHA-256 hexadecimal minúsculo dos bytes do arquivo. Eis os 17 membros e seus valores originais.

```json
{
  "files": {
    "script/classification_comparison/requirements.txt": "7c6580fef88b041c371d415c00d72217714742dd9a1e3059c512cc9090e162ee",
    "script/classification_comparison/setfit_pilot/provision.py": "37a239c64024d4385bcc797f3f9dd51d3805c3f32d8b421c3f8b5383adba53cc",
    "script/classification_comparison/setfit_pilot/requirements.txt": "14bf9aeefaf8e8275de3b014ea63b10dea42246a0e80736220098fa546091b97",
    "script/classification_comparison/setfit_sf2/adapter/__main__.py": "ef4a9da8e08f935886c2b46669d626de758a72f19231053891136fa0b134ec54",
    "script/classification_comparison/setfit_sf2/adapter/decide.py": "6578db6a804d4dcd0bc9f43e5b469b81526ab96a99dcc51cdeda9a92f7970b0d",
    "script/classification_comparison/setfit_sf2/contracts/__init__.py": "01e4ca572a847cc20f7130abb625898c0a28f8daa0f914cd4f13cde30cd8bc32",
    "script/classification_comparison/setfit_sf2/contracts/artifacts.py": "f2272db7a11b3f1d129bdd4564ec6cd952d057e02350a6d963ff16f1373b65ec",
    "script/classification_comparison/setfit_sf2/contracts/core.py": "3a8d307becdc15f3306ab77396055b9f0a35f4f106f465e2d3628132d235e5ea",
    "script/classification_comparison/setfit_sf2/contracts/data.py": "e918a5b5606051d8ded78733d1a95b245a5559cd4c0dc8679556596b20d7cd4b",
    "script/classification_comparison/setfit_sf2/contracts/ipc.py": "d272c56cb4dfaf9738a8e1faa704773fda85bf47260b0e5b0b2b0556367d1e0f",
    "script/classification_comparison/setfit_sf2/training/__main__.py": "06c09b43e11b43da06a26f7655e6d19da6e1c3188abbb0558ee24f9aa73b2760",
    "script/classification_comparison/setfit_sf2/training/environment.py": "3039e2a8c54b7eeac677ad111c5ddf33bd54cb9cc28c942aac22f321bb9690a2",
    "script/classification_comparison/setfit_sf2/training/fit.py": "b53915395051baad60818db550a961c7bd36083e084f09110dcebebbf9d06215",
    "script/classification_comparison/setfit_sf2/training/package.py": "db4af26b02e55ab38c570cd48734e46d857c467ba62e86cb0abe7bcfd15e15c5",
    "script/classification_comparison/setfit_sf2/training/requirements.txt": "223978463b717b847df460499001eb9800eb5f8657326a73506b0fa5677aca66",
    "script/classification_comparison/setfit_sf2/training/scores.py": "6fac00ccf902477489467a136ae2ae09af6a5449ef97322b1c7e3576445cdc5d",
    "script/classification_comparison/setfit_sf2/training/supervise.py": "631ed8958e61c362dce6e341fae7396b46075bf6b61b2f7d0897f38877b7048b"
  }
}
```

O roteiro fez uma cópia isolada **somente das fontes e metadados**, obteve recibo idêntico ao da coleta, e acrescentou um comentário a quatro dos 17 membros do índice, um por vez. Python iniciou em processo novo usando as fontes do espelho. Manteve-se fixo todo arquivo do inventário de configuração. As funções de 04 que preparam a configuração e o recibo aceitam essa configuração após cada mudança. O efeito ao comparar os recibos foi o seguinte.

| Fonte alterada | Comparação com recibo original |
| --- | --- |
| `adapter/decide.py` | Idêntico |
| `adapter/__main__.py` | Idêntico |
| `contracts/__init__.py` | Idêntico |
| `contracts/ipc.py` | Divergência em `contracts/ipc.py`, o controle positivo |

Na base ensaiada, `evaluation/workflow.py:93` lista seis arquivos do avaliador e quatro dos contratos. A função da linha 100 calcula o hash de `cfg["adapter"]` como arquivo opaco. A linha 122 reaplica essa mesma conferência no congelamento. Mesmo um inventário íntegro e completo entregue pelo operador não permite à cadeia atual atestar que seus membros ainda correspondem ao checkout. O argv autorizado e o hash dos pesos permitem identificar a invocação e o pacote. Eles próprios não congelam o código resolvido por Python. Essa falha independe das escolhas de corte.

**Aceite da correção.** SF2-04 verifica a lista e os bytes dos membros contra o diretório efetivo do worker na coleta e antes da exposição. A interface precisa ligar de modo verificável o ponto de entrada, a política de decisão, as demais dependências locais realmente carregadas e os contratos compartilhados. Repetir a prova de mudança individual preservando índice/argv, com um caso de base íntegra. Seguem sob custódia do operador o comando local de confiança, a instalação do intérprete e o recibo de liberação. A QA não modificou arquivos de produto.

## Identidades e medidas da execução arquivada

| Artefato | SHA-256 |
| --- | --- |
| Manifesto do pacote recarregado | `fe1b2fbab91125eb91ed82bd49ef15c608ea332bad8cb002601276fc05d682ba` |
| Frames originais | `7ea3da2e4e436c34d1dfca50f0754084b06c0e52891b795bcab9b33746259490` |
| Journal | `373a1870632f125732611bb0f6655b6461323341b225d13f675ffa654aac3a3c` |
| Scores 03 | `77798479067b064a4d23d8613647ac64fb648908234fc2d035563f36fe3b0fe7` |
| Scores 04 | `98e81cfdf7e8829970f9082980177a31713d3dcfce0d8fb3452677de6ff7ae2f` |
| Grade | `a365ef9dabd890a8c952a0b1157fad9c377fbc894bb872f770cf9fed9337c80d` |
| Recibo de seleção | `9d5d3120526fa6daf25d2e8f16389ebbf4f4f58b4799101ce60421fd6e585ac9` |

No preparo do roteiro houve uma coleta numérica e, na autorrevisão, uma execução independente do roteiro completo. Os dados desta tabela provêm integralmente da segunda. Para as 90 observações cronometradas da fixture, startup de 4.329,24 ms, p50 de 3,99 ms, p95 de 5,76 ms e máximo de 9,78 ms. O ensaio não estima a qualidade ou latência do modelo da pesquisa.

## Reprodução e autorrevisão

A saída integral permanece em `/tmp/sf2-onda2-integracao-237df80-b/` nesta máquina, com o índice, o pacote de fixture, a configuração, os frames, o journal e o espelho de fontes. O recibo de verificação do ambiente e snapshot está em `/tmp/sf2-onda2-integracao-237df80-a/pins.json`.

Na worktree de QA, com um caminho de saída novo, executar o comando documentado no README. O recibo registra argv e resultados de cada CLI. O comando efetivo da execução arquivada foi o seguinte.

```sh
sf2_python=../sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python
rtk proxy env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "$sf2_python" -B \
  docs/evidencias/c05/sf2/integracao-onda2/verificar.py /tmp/sf2-onda2-integracao-237df80-b
```

Código 2 do roteiro identifica o bloqueador de fontes. O extrator retornou 0, a validação inelegível e o congelamento recusado retornaram 1. Na autorrevisão foram conferidos o parse do roteiro, a igualdade entre o recibo versionado e o produzido, os links, as cinco recusas por divergência de política/comando/journal/frames e a detecção diferencial dos quatro membros. `git diff --check 237df80 HEAD` passou, a worktree terminou limpa, com três arquivos de QA no commit. Sem merge ou publicação remota.

**Exercício.** Compare no recibo as chamadas e `applied` dos controles completo, prioridade nula e máscara dupla. Depois confira qual dos quatro comentários inseridos no espelho alterou o recibo de fontes e explique por que os outros três impedem certificar a identidade do adaptador.
