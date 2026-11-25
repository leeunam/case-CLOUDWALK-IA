# Aceite combinado SF2-03/04 com fixtures

**Bloqueado na base `237df80b4d27229fe79456f943cc11dc2b31f066`.** O executor e o worker concordaram sobre as decisões, os vetores e o bloqueio do final. A conferência do código do adaptador deixou passar alterações em três arquivos que participam da execução.

A branch de QA é `feat/sf2-integracao`, na worktree `.worktrees/sf2-integracao`. A evidência contém o roteiro e o [recibo observado](recibo.json). Os comandos completos, hashes, durações e versões estão no recibo. Pesos sintéticos, jornais e saídas intermediárias ficam no diretório temporário da reprodução.

## Resultados

| Verificação | Observação |
| --- | --- |
| Transporte | O executor 04 recebeu READY do processo de controle 03 antes da primeira entrada e da primeira chamada. Os seis envios continham somente versão, ID, texto, canal recebido, máscara e catálogo. |
| Seleção dos especialistas | Canal completo e valor inválido produziram zero chamadas. A categoria em branco chamou apenas categoria. A prioridade nula chamou apenas prioridade. A máscara dupla chamou ambos. O canal recebido foi preservado. |
| Veto integral | Com corte de categoria 0,90 exclusivo do controle, o escore 0,80 causou revisão. O campo prioridade reteve a escolha bruta `urgent` e o caso publicou `applied={}`. |
| Inicialização do pacote | Um processo adicional carregou o microencoder e os dois especialistas, emitiu READY e encerrou em EOF com zero chamadas observadas em PyTorch, `SentenceTransformer.encode` e `SetFitModel.predict_proba`. |
| Extrações 03 e 04 | CLI de coleta com worker 03 de produção e pacote de fixture recarregável. Todos os 90 IDs produziram um frame e a coleta registrou cinco controles adicionais. Os dois pacotes de scores coincidiram em todos os campos. Cada um dos 120 vetores também coincidiu com o do respectivo frame original. |
| Seleção offline | O replay das 225 políticas usou os vetores selados. Nenhuma combinação foi elegível com as cabeças constantes. A validação retornou `failed`, o congelamento recusou a liberação e a tentativa de execução parou na ausência de `release.json`. A sentinela temporária permaneceu sem leitura. |
| Integridade dos registros | O selo identificou frames, journal, controles e stderr. Foram 95 entradas de journal e 90 observações de latência. Mudanças isoladas nos bytes de argv, política, journal e previsões impediram o congelamento. Um corte de coleta diferente do mínimo foi recusado antes do início do worker. |

A factory de 03 inicializa um BERT de dimensão 8, com uma camada, e duas cabeças logísticas de parâmetros constantes. Na preparação, a própria factory avalia um exemplo de teste por cabeça. Depois, o roteiro sela os especialistas exportados com o manifesto e o freeze das linhas numéricas. A coleta usa o comando normal do worker e as identidades dos artefatos gerados. As chamadas preparatórias e o controle separado de startup antecedem ou estão fora da medição dos 90 casos. O extrator lê os frames selados. Cada execução do roteiro produz sua própria coleta e suas próprias medidas de fixture.

## Falha de proveniência

A seção 7, passos 3 e 5, da [especificação SF2](../../../../planejamento/classificacao-comparativa/sf2/especificacao.md) exige congelar fontes e, após a validação, o adaptador e o comando. A configuração deste ensaio entrega a 04 um arquivo JSON que lista os 16 membros do inventário de código de 03 e acrescenta o ponto de entrada `adapter/__main__.py`. Esse conjunto inclui o código dos contratos compartilhados. O worker foi invocado pela opção Python `-m` na worktree de integração.

Para testar a ligação, o roteiro cria um espelho temporário de fontes e metadados, confere que seu recibo inicial coincide com a coleta e acrescenta um comentário a um único arquivo por vez. Cada tentativa inicia Python no espelho, com o mesmo argv, o mesmo índice e os mesmos pesos. Executa os verificadores públicos de configuração e da captura que 04 repete no congelamento. O ensaio não depende de a grade ser elegível.

| Membro alterado no espelho | Efeito no recibo de captura |
| --- | --- |
| `adapter/decide.py` | Nenhum. O pré-voo aceitou os bytes divergentes. |
| `adapter/__main__.py` | Nenhum. O pré-voo aceitou os bytes divergentes. |
| `contracts/__init__.py` | Nenhum. O pré-voo aceitou os bytes divergentes. |
| `contracts/ipc.py` | Mudou o hash específico do contrato. A comparação com a captura original detecta a divergência. |

Na base examinada, `evaluation/workflow.py`, funções `sources` e `capture_receipt`, calcula o hash do **arquivo do índice** e de uma lista de fontes do avaliador e dos contratos. O pré-voo deixa de conferir os bytes dos membros do índice contra o código local utilizado. `checked_development` compara o recibo obtido por esse mesmo processo com o da coleta. Portanto uma coleta inelegível prova o bloqueio de qualidade, mas a cadeia atual não estabelece a identidade de todo o adaptador para liberar uma coleta elegível.

**Dono da correção** — SF2-04, com a interface do artefato de fontes acordada com 03. O aceite precisa de uma configuração verificável do worker e de seus arquivos locais, inclusive o ponto de entrada e a inicialização dos contratos. A divergência deve impedir o início da coleta ou, se ocorrer depois, impedir a liberação. A custódia do intérprete, do diretório de execução e do comando local autorizado continua a cargo do operador. A operação real da SF2-05 segue pendente.

## Reprodução

Na raiz da worktree de integração, use um diretório de saída novo. O intérprete abaixo é o ambiente pinado de 03 disponibilizado para este aceite. `env -i` inicia o roteiro com ambiente vazio e as duas variáveis mostradas. O roteiro ativa o modo offline e dirige os caches para a saída temporária.

```sh
sf2_python=../sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python
qa=docs/evidencias/c05/sf2/integracao-onda2/verificar.py
rtk proxy env -i PATH=/usr/bin:/bin LANG=C.UTF-8 "$sf2_python" -B "$qa" /tmp/sf2-aceite-reproducao
```

O roteiro final retorna **2** quando a prova termina e detecta os membros divergentes sem mudança do recibo. O arquivo `recibo.json` da saída lista os resultados, o argv do worker, os comandos das CLIs com os respectivos códigos e hashes SHA-256. Os hashes de artefatos que incorporam tempos, caminhos ou metadados da serialização podem variar entre execuções.

**Exercício.** No recibo, compare `transport.cases` para `sf2-control-complete`, `sf2-control-null-priority` e `controle-duplo`. Identifique qual especialista foi chamado e confira o que o atendimento efetivamente recebeu em `applied`.
