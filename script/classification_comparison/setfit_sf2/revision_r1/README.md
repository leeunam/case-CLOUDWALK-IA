# SF2-R1 · Replay de validação

O executor compara os mesmos vetores da captura SF2 sob 225 políticas originais e uma extensão de 45. O schema `sf2-r1.schema.json` define as candidatas offline de categoria 0,95. A prioridade continua na grade histórica. O identificador `unionPolicy` referencia esse tipo e a política original `sf2-ipc/1.0`.

## Testes por fixture

Na raiz da worktree, execute com o Python do ambiente de verificação SF2, com `jsonschema` instalado.

```sh
rtk proxy "$PYTHON_SF2" -B -m unittest -v \
  script.classification_comparison.setfit_sf2.revision_r1.test_replay \
  script.classification_comparison.setfit_sf2.evaluation.test_evaluation.MathTest
```

O teste usa 90 relatos sintéticos e cinco controles. A grade e a baseline de referência da fixture têm hashes obtidos na versão histórica de `selection.py`. O harness abre um processo isolado para observar a CLI e bloqueia rede, subprocessos, importação de modelos e acesso a pesos ou dados finais durante o replay.

**Exercício.** Na fixture `sample()`, siga o vetor em que Pix recebe 0,92 e repasse recebe 0,08. Com delta zero, anote o campo aceito em tau 0,90 e o resultado do caso em tau 0,95. Para uma solicitação com as duas lacunas, confira se a prioridade seria aplicada após o veto de categoria.

## Rodada autorizada da Task 2

Use uma worktree exclusiva, o inicializador do commit aceito em revisão e os SHA-256 da emenda e de `revision_r1/sources.json` obtidos independentemente desse commit. O comando abaixo é a interface reservada ao executor. O destino `script/classification_comparison/setfit_sf2/.cache/revisao-01` deve estar ausente.

```sh
rtk proxy "$PYTHON_SF2" -I -B script/classification_comparison/setfit_sf2/revision_r1/cli.py \
  --historical-root "$WORKTREE_QUALIFICACAO" \
  --amendment-sha256 "$SHA_EMENDA_ACEITA" \
  --inventory-sha256 "$SHA_INVENTARIO_ACEITO"
```

A raiz histórica deve ser um caminho absoluto canônico. A CLI confere os arquivos públicos por caminhos fixos, o conjunto exato de fontes, os membros do adaptador, o freeze de treinamento, índices públicos do pacote e o selo da captura. A proveniência dos pesos físicos vem da captura original. O inicializador confere a configuração arquivada por digest. Os caminhos históricos registrados nela servem como evidência. Os módulos locais de auditoria e replay são importados a partir dos bytes recém-atestados. A auditoria lê o protocolo, schema, catálogo e demais insumos de uma árvore temporária privada preenchida com esses bytes. A CLI remove essa árvore ao sair da etapa de cálculo. O interpretador e as bibliotecas do ambiente de verificação são pré-requisitos do executor.

Após auditar as decisões, a CLI exige igualdade dos vetores reconstruídos com os scores 03/04. Em seguida exige igualdade de cada política, baseline, seleção e bytes da grade descomprimida das 225. Só então reserva o diretório de saída e calcula as 45. A reserva permanece se houver interrupção após esse ponto, para o integrador poder investigar sem repetir a rodada.

| Código de saída | Significado |
| --- | --- |
| 0 | Há candidata elegível na validação. |
| 1 | Todas as políticas foram vetadas. |
| 2 | Falha de insumo, de execução, de integridade ou destino já reservado. |

O arquivo `result.json` traz a tabela de 270 políticas, matriz por campo, suporte, intervalos de Wilson, gates, motivos de veto e seleção da união. Os hashes `additional_grid_sha256` e `union_sha256` usam as linhas de seleção antes de acrescentar `failed_gates`, na serialização compacta histórica de `runner.encoded`. O tempo medido cobre apenas o cálculo e a montagem do resultado da extensão. O ajuste foi escolhido após observar a validação original. O final, C06/C07, adoção e publicação seguem bloqueados em ambos os resultados.
