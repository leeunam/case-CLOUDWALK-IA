# Aceite combinado SF2-03/04 com fixtures

**Aceite de integração aprovado na base `8da95a7a6852da01d15c6dc04a677f2055e6d046`.** Com índice e comando idênticos aos da primeira rodada, a coleta e o congelamento recusaram cada uma das quatro alterações de fonte. O pré-voo aceitou a cópia íntegra e voltou a aceitá-la depois da restauração. Os 17 arquivos do índice entraram na conferência de bytes e quatro deles receberam sondas individuais.

A branch de QA é `feat/sf2-integracao`, na worktree `.worktrees/sf2-integracao`. O [recibo de custódia](recibo-custodia.json) registra status, código, motivo e os oito diagnósticos da nova prova. O [recibo histórico](recibo.json) conserva suas medidas e a falha original, no mesmo arquivo do commit `eef5c148`, SHA-256 `ce8d97b3a51109e11830ba9aeb0c7edbc9c643ea710628535bd155f000fb1297`.

## Rechecagem da custódia

A configuração preservada aponta para o pacote de microencoder e as linhas numéricas da primeira rodada. O roteiro conferiu o digest do recibo anterior, sua captura e os hashes de frames, journal e controles. Comparou o pré-voo da correção com o histórico. Só mudou o papel `evaluation/workflow.py`. O runner JSONL, o worker, os contratos, o extrator de scores e o replay conservaram as versões examinadas. Isso permitiu reutilizar os resultados dos 90 IDs sem coletar previsões novamente.

Para cada sonda, o roteiro inicia os comandos de coleta e congelamento no espelho temporário. A prova exige saída 1 nas duas etapas, mensagem de divergência SHA-256 com o membro exato e ausência de execução e de liberação. Um observador impede iniciar o worker, mesmo se uma alteração deixar de ser detectada. O controle positivo obrigatório é `contracts/ipc.py`. Na autorrevisão, simulou-se a aceitação indevida desse controle na coleta e a prova gravou `failed` com saída 1.

| Fonte modificada no espelho | Coleta | Congelamento |
| --- | --- | --- |
| `adapter/decide.py` | Recusada | Recusado |
| `adapter/__main__.py` | Recusada | Recusado |
| `contracts/__init__.py` | Recusada | Recusado |
| `contracts/ipc.py` | Recusada | Recusado |

A conferência presume o diretório de execução aprovado, o intérprete sob custódia do operador e um comando local confiável. Os resultados abaixo continuam específicos das fixtures.

## Resultados da coleta histórica na base `237df80`

| Verificação | Observação |
| --- | --- |
| Transporte | O executor 04 recebeu READY do processo de controle 03 antes da primeira entrada e da primeira chamada. Os seis envios continham somente versão, ID, texto, canal recebido, máscara e catálogo. |
| Seleção dos especialistas | Canal completo e valor inválido produziram zero chamadas. A categoria em branco chamou apenas categoria. A prioridade nula chamou apenas prioridade. A máscara dupla chamou ambos. O canal recebido foi preservado. |
| Veto integral | Com corte de categoria 0,90 exclusivo do controle, o escore 0,80 causou revisão. O campo prioridade reteve a escolha bruta `urgent` e o caso publicou `applied={}`. |
| Inicialização do pacote | Um processo adicional carregou o microencoder e os dois especialistas, emitiu READY e encerrou em EOF com zero chamadas observadas em PyTorch, `SentenceTransformer.encode` e `SetFitModel.predict_proba`. |
| Extrações 03 e 04 | CLI de coleta com worker 03 de produção e pacote de fixture recarregável. Todos os 90 IDs produziram um frame e a coleta registrou cinco controles adicionais. Os dois pacotes de scores coincidiram em todos os campos. Cada um dos 120 vetores também coincidiu com o do respectivo frame original. |
| Seleção offline | O replay das 225 políticas usou os vetores selados. Nenhuma combinação foi elegível com as cabeças constantes. A validação retornou `failed`, o congelamento recusou a liberação e a tentativa de execução parou na ausência de `release.json`. A sentinela temporária permaneceu sem leitura. |
| Integridade dos registros | O selo identificou frames, journal, controles e stderr. Foram 95 entradas de journal e 90 observações de latência. Mudanças isoladas nos bytes de argv, política, journal e previsões impediram o congelamento. Um corte de coleta diferente do mínimo foi recusado antes do início do worker. |

A factory de 03 inicializa um BERT de dimensão 8, com uma camada, e duas cabeças logísticas de parâmetros constantes. Na preparação, a própria factory avalia um exemplo de teste por cabeça. Depois, o roteiro sela os especialistas exportados com o manifesto e o freeze das linhas numéricas. A coleta usa o comando normal do worker e as identidades dos artefatos gerados. As chamadas preparatórias e o controle separado de startup antecedem ou estão fora da medição dos 90 casos. O extrator lê os frames selados. A reprodução completa da fixture gera sua própria coleta e suas próprias medidas. O modo focal de custódia lê os artefatos preservados.

## Falha de proveniência observada na primeira rodada

A seção 7, passos 3 e 5, da [especificação SF2](../../../../planejamento/classificacao-comparativa/sf2/especificacao.md) exige congelar fontes e, após a validação, o adaptador e o comando. A configuração deste ensaio entrega a 04 um arquivo JSON que lista os 16 membros do inventário de código de 03 e acrescenta o ponto de entrada `adapter/__main__.py`. Esse conjunto inclui o código dos contratos compartilhados. O worker foi invocado pela opção Python `-m` na worktree de integração.

Para testar a ligação, o roteiro cria um espelho temporário de fontes e metadados, confere que seu recibo inicial coincide com a coleta e acrescenta um comentário a um dos quatro arquivos escolhidos por vez. Cada tentativa inicia Python no espelho, com o mesmo argv, o mesmo índice e os mesmos pesos. Executa os verificadores públicos de configuração e da captura que 04 repete no congelamento. O ensaio não depende de a grade ser elegível.

| Membro alterado no espelho | Efeito no recibo de captura |
| --- | --- |
| `adapter/decide.py` | Nenhum. O pré-voo aceitou os bytes divergentes. |
| `adapter/__main__.py` | Nenhum. O pré-voo aceitou os bytes divergentes. |
| `contracts/__init__.py` | Nenhum. O pré-voo aceitou os bytes divergentes. |
| `contracts/ipc.py` | Mudou o hash específico do contrato. A comparação com a captura original detecta a divergência. |

Na base examinada, `evaluation/workflow.py`, funções `sources` e `capture_receipt`, calcula o hash do **arquivo do índice** e de uma lista de fontes do avaliador e dos contratos. O pré-voo deixa de conferir os bytes dos membros do índice contra o código local utilizado. `checked_development` compara o recibo obtido por esse mesmo processo com o da coleta. Na primeira rodada, o congelamento recusou a qualidade da fixture. A cadeia daquela base deixou de identificar três alterações nas fontes do adaptador.

A SF2-04 entregou a correção de custódia conferida na rechecagem acima.

## Reprodução

Na raiz da worktree de integração, use o intérprete pinado de 03 e um diretório de saída novo. `env -i` inicia o processo com as variáveis abaixo. O roteiro ativa o modo offline e redireciona `HF_HOME` e `XDG_CACHE_HOME` para a saída temporária. No modo de coleta, o loader do encoder também recebe explicitamente `.cache/transformers` da própria worktree de integração. A QA não mede escritas no cache.

```sh
sf2_python=../sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python
qa=docs/evidencias/c05/sf2/integracao-onda2/verificar.py
rtk proxy env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "$sf2_python" -B "$qa" \
  /tmp/sf2-aceite-reproducao --fixture-anterior /tmp/sf2-onda2-integracao-237df80-b
```

A opção `--fixture-anterior` identifica a saída confiável preservada da primeira rodada. Se ela estiver indisponível, omita a opção para gerar um novo pacote de fixture e executar a coleta e as sondas em diretório novo. As medidas históricas permanecem no Git. O roteiro atual grava `status`, `exit_code` e `reason` em `recibo.json` antes de encerrar a prova. Saída 0 exige as quatro recusas nas duas etapas e os pré-voos íntegros. Falha em qualquer controle retorna 1. O roteiro histórico do commit `eef5c148` retornou 2 pelo bloqueador então existente.

**Exercício.** Compare o controle `contracts/ipc.py` na seção `source_checks` de cada um dos dois recibos. Na primeira rodada, a diferença apareceu ao comparar os recibos. Na segunda, identifique em qual etapa o hash passou a impedir uma nova captura.
