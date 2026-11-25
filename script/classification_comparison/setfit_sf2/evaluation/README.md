# Avaliação independente SF2

O módulo executa o contrato `sf2-ipc/1.0` em Python 3.11 no Linux. Em SF2-04, os testes usam somente contadores e um worker de fixture. A execução em dados da pesquisa pertence à SF2-05, após aceite e integração de 00–04. O responsável decide a adoção após o parecer. O projeto mantém a demonstração F10 em fixture.

## Configuração para o executor independente

Da raiz da worktree, use o nome de módulo abaixo. Os argumentos de arquivos podem ser absolutos ou relativos ao diretório de execução. Use caminhos absolutos nos inventários e nos comandos do worker para reproduzir a execução em outro shell.

```sh
mod=script.classification_comparison.setfit_sf2.evaluation
rtk proxy python3 -B -m "$mod" --help
```

O JSON público de configuração contém exatamente as seguintes propriedades.

| Propriedade | Conteúdo |
| --- | --- |
| `training_files` | Objeto de caminhos explícitos por papel para o validador `trainingFreeze` de 00, incluindo `final_seal` público, recibo de revisão e tokenização |
| `model_files` | Objeto de caminhos explícitos por papel para `modelManifest`, incluindo `training_freeze`, descritores, índices e membros |
| `model_manifest`, `versions` | Caminhos do manifesto geral e do JSON de versões que contém as versões do manifesto |
| `adapter` | Caminho de um JSON `componentIndex`. O mapa `files` associa cada caminho POSIX relativo à raiz da worktree ao SHA-256 dos bytes do membro |
| `capture_policy` | Caminho de um documento `policy` com `tau=0.5` e `delta=0` nos dois campos |
| `capture_command`, `final_command` | Caminhos de arquivos JSON, cada um contendo o argv completo de um worker local de confiança. O segundo aponta para a política que será gravada em `VALIDACAO/policy.json`. Não se usa shell para executar esses argumentos |
| `costs` | Caminho do recibo JSON com `download_ms`, `training_ms` e `classifier_api_calls`. O operador fornece as medições das etapas anteriores e atesta zero chamadas externas do classificador. Valores ausentes de tempo podem ser nulos e impedem conclusão |
| `startup_seconds` | Prazo operacional explícito para receber READY do novo processo. O prazo fixo de cada caso é 5.000 ms |

Para montar o índice do adaptador, comece pelo `files` de `training.fit.code_manifest()` de 03 e acrescente `script/classification_comparison/setfit_sf2/adapter/__main__.py` com seu SHA-256. Nesta base são 17 membros. A captura e o congelamento vinculam o digest do índice. O avaliador confere a cobertura contra o inventário congelado do treino e o código local de 03, relendo os membros e o ponto de entrada antes da coleta e da liberação do final. Os caminhos devem resolver dentro da worktree. O operador deve usar um argv e um intérprete confiáveis que importem o worker dessa worktree.

Os inventários de arquivos e o recibo de exposição dependem da custódia pelo operador. A igualdade de hashes verifica bytes e permite reprodução. Reserve um diretório de saída novo por etapa e mantenha o recibo de freeze aprovado sob custódia independente.

## Sequência de execução

```sh
rtk proxy python3 -B -m "$mod" validate CONFIG.json VALIDACAO
rtk proxy python3 -B -m "$mod" freeze CONFIG.json VALIDACAO LIBERACAO
```

1. `validate` confere a cadeia de dados públicos e modelo e fixa a política de coleta em `capture.json`. Um único processo recebe as 90 entradas projetadas e, depois, controles adicionais. Cada linha preserva o frame original em `run/predictions.jsonl`. Os tempos externos ficam em `run/timings.jsonl` e o selo dos bytes em `run/seal.json`. O módulo audita originais e controles antes de extrair scores. Para conferir a extração de 03, use o comando `training scores` sobre esse JSONL selado e compare os objetos JSON resultantes. Serializações distintas podem ter SHA-256 distintos.
2. A grade em `grid.json` contém a linha de base argmax e todas as 225 combinações calculadas dos mesmos vetores. Em cada política, `eligible` exige todos os gates de qualidade. A ordem de desempate está no protocolo. A linha de base usa o rótulo bruto, o catálogo e o veto atômico, sem cortes de score ou margem. `selection.json` liga a vencedora, a política de coleta, a tabela, os scores, os frames e a origem da latência. Se nenhuma política cumprir os gates, o relatório preserva o diagnóstico da coleta e o final permanece fechado.
3. `freeze` recalcula a seleção e as métricas, verifica os hashes de todos os produtos e grava `freeze.json`, `command.json` e `release.json`. O descritor do comando liga o argv definitivo às fontes do avaliador, ao contrato, à política de coleta e aos bytes de cada evidência da seleção. O SHA-256 de `release.json` impresso pelo comando deve ser registrado pelo integrador antes de liberar o acesso ao final.
4. O executor independente usa o digest previamente aprovado. O inventário reservado é um arquivo JSON com caminhos para `final`, `annotations`, `review_receipt` e `token_lengths`. Somente `execute` e `audit` aceitam esse argumento. O primeiro acesso ocorre após verificar a liberação e criar exclusivamente o recibo `LIBERACAO/exposure.json`, com o horário UTC e o destino. O processo é novo, sem aquecimento, com uma tentativa por ID. O recibo bloqueia nova execução no mesmo diretório de liberação, inclusive após interrupção.
5. `execute` sela os frames, as durações e a interrupção observada antes do cálculo das métricas finais. O SHA-256 retornado identifica `FINAL/execution.json`. O operador registra esse hash antes de `audit`. O auditor confere também o pacote reservado inteiro contra o selo e recalcula a partir dos originais. Pode repetir a auditoria, sem chamar o modelo. O operador arquiva o pacote aberto, as anotações e o recibo de exposição na entrega de 05.

```sh
rtk proxy python3 -B -m "$mod" execute CONFIG.json VALIDACAO LIBERACAO SHA_RELEASE INVENTARIO_RESERVADO.json FINAL
rtk proxy python3 -B -m "$mod" audit CONFIG.json VALIDACAO LIBERACAO SHA_RELEASE INVENTARIO_RESERVADO.json FINAL SHA_EXECUCAO
```

A CLI devolve código 1 para recusa de contrato e para parecer `failed` ou `inconclusive`. Uma execução interrompida após abrir o worker também produz um recibo de execução e seu digest. `audit` usa esse recibo para relatar a interrupção; `run/seal.json` conserva o motivo e o último frame recebido, quando disponível. Em falha de integridade do pacote reservado antes de iniciar o worker, ficam o recibo de exposição e `interruption.json`.

## Como ler as medidas

- O denominador de acerto por campo inclui todos os complementos efetivamente aplicados ao campo. Um denominador zero reprova o gate. A matriz e as métricas por classe usam o rótulo bruto de cada alvo, incluindo coluna de erro se faltar vetor. O intervalo de Wilson de 95% acompanha cada proporção com denominador positivo.
- Revisão por campo conta vetos e falhas do próprio especialista. Revisão por caso conta toda conclusão impedida por algum veto ou falha. A decisão original preserva o motivo e o resultado de cada campo, inclusive quando outro campo veta a aplicação. Os controles de canal completo e inválido exigem zero chamadas. Controles adicionais exercitam campo nulo, em branco e omitido.
- Na validação, a qualidade reportada corresponde à vencedora, quando existe, e os tempos correspondem à política de coleta. A duração externa começa antes da projeção e validação da entrada e termina após validar a decisão original. O `elapsed_ms` enviado pelo modelo permanece intacto. Controles e replay ficam fora dos percentis. No final, o p95 é a 114ª duração das 120 ordenadas.
- Em interrupção, `counts.observed` inclui a tentativa falha com duração observada. `unexecuted_ids` inclui os IDs nunca tentados. O ID tentado sem resposta válida fica em `failure.attempt` e em `timings.jsonl` com `valid=false`. O prefixo efetivamente aceito fica em `predictions.jsonl` e, se incompleto, em `partial-scores.json`. Esse último é um inventário parcial, sem validade de pacote de scores completo.
- O tempo de partida vai da criação do processo até o READY. Os picos de memória e CPU são observados para o PID do worker no Linux. A memória vem de `VmHWM` e a CPU usa diferenças dos ticks do processo, amostradas a cada 50 ms. O uso pode exceder 100% em várias threads. Pulsos curtos entre amostras podem escapar. Coleta, treino e download são medidas locais distintas.
- Antes da coleta e na reauditoria, o avaliador confere o catálogo dos contratos contra os bytes aprovados do inventário. A projeção e a grade recebem o catálogo decodificado desses bytes.
- Se já houver bytes de saída antes do envio de uma entrada completa, o supervisor interrompe o ensaio. Se uma interrupção ocorrer ao gravar uma decisão validada, o executor completa apenas os bytes faltantes do frame e do journal com a duração já medida. A auditoria registra o prefixo observado e emite parecer inconclusivo.

## Reprodução da implementação

```sh
sf2=script.classification_comparison.setfit_sf2
rtk proxy python3 -B -m unittest -v "$sf2.contracts.test_contracts" "$sf2.contracts.test_artifacts" \
  "$sf2.evaluation.test_evaluation" "$sf2.evaluation.test_workflow"
```

O teste de fluxo monta todas as quotas e selos em diretório temporário com textos que são identificadores numéricos. **Exercício.** Em `test_applied_and_raw_urgent_have_distinct_numerators`, localize a fixture com categoria insuficiente e prioridade `urgent` na máscara dupla. Confira que o alvo entra no numerador de urgentes brutos e que `applied` fica vazio. A diferença esperada na fixture numérica final é 17 urgentes brutos reconhecidos e 16 efetivamente aplicados.
