# SF2-03 · Instalação, treino e extração

Execute da raiz da worktree. O módulo usa o [protocolo
aprovado](../../../../docs/planejamento/classificacao-comparativa/sf2/protocolo.json)
e os [contratos SF2](../../../../docs/planejamento/classificacao-comparativa/sf2/contratos/README.md).

## Instalação e conferência

O lock mantém os pins SF1 e acrescenta os do validador do projeto e os seus
transitivos. O supervisor limita a 30 minutos a criação do ambiente, instalação
dos wheels declarados, `pip check`, imports e cópia conferida do snapshot local.
Use um diretório novo em `.cache/`. Passe o diretório da cópia pública SF1 do
snapshot, já baixada. O comando confere os 10 arquivos contra o lock antes e
depois da cópia e registra versões e hashes em `environment.json`.

```sh
sf2=script.classification_comparison.setfit_sf2
dir=script/classification_comparison/setfit_sf2/.cache
env_dir="$dir/install-01"
rtk proxy python3.11 -B -m "$sf2.training" install \
  --snapshot "$snapshot_sf1" --output "$env_dir"
python="$env_dir/.venv/bin/python"
```

Se já houver um ambiente com todos os pins, é possível conferi-lo com
`"$python" -B -m "$sf2.training" check --snapshot "$snapshot_sf1" --output "$dir/environment.json"`.
O verificador exige Python 3.11, PyTorch CPU, os 73 pins e a origem e SHA-256
declarados no recibo de instalação do wheel Torch. Mantenha ambientes,
snapshots e saídas volumosas na pasta ignorada `.cache/`.

## Treino autorizado em SF2-05

Antes de selar o pré-treino, gere `training_code` com
`"$python" -B -m "$sf2.training" code-manifest --output "$dir/training-code.json"`.
Vincule seus bytes ao `trainingFreeze`. O papel `arguments` contém a seção
`training` do protocolo. Use os caminhos do manifesto público aceito e dos
recibos, incluindo somente o **selo público** do final.

```sh
rtk proxy "$python" -B -m "$sf2.training" train \
  --snapshot "$env_dir/model" --training-freeze "$freeze" \
  --arguments "$arguments" --training-code "$dir/training-code.json" \
  --train "$dados/train.jsonl" --validation "$dados/validation.jsonl" \
  --annotations "$dados/annotations-public.jsonl" --public-manifest "$public_manifest" \
  --review-receipt "$review_receipt" --token-lengths "$token_lengths" \
  --final-seal "$final_seal" --output "$dir/training-01"
```

Antes do primeiro ajuste, o runner verifica o congelamento e repete a
tokenização sem truncagem do treino e da validação. Ele cria um encoder por
campo a partir do mesmo snapshot, com duas threads intra/inter-op. Cada
`Trainer.train()` inclui o ajuste do encoder e da cabeça. O supervisor
contabiliza o total dos dois ajustes e encerra o grupo em caso de prazo ou
cancelamento. Logs e desfecho ficam em `commands.log` e `status.json`.

O pacote é publicado após os dois ajustes e o reload. `evidence.json`
registra pares, passos, classes, iterações da cabeça, alteração do peso
monitorado, versões, recursos e comparação de reload em três exemplos
de treino. Tolerância absoluta `1e-6` para scores, com argmax e razões
por corte preservados. Para usar o pacote, obtenha `package_sha256` do
`status.json` concluído e forneça esse hash pelo canal do ensaio. A verificação
compara o manifesto a esse valor antes de desserializar a cabeça local.

`package/manifest.json` inventaria os bytes gravados. Os papéis
`training_freeze` e `arguments` correspondem aos JSON na raiz do pacote.
Cada campo tem `<campo>/manifest.json` e cinco índices
`<campo>/<componente>.json`. Em `encoder` e `tokenizer`, os membros ficam
juntos em `<campo>/body/`, onde são usados por SentenceTransformer. Nos
demais componentes, ficam em `<campo>/<componente>/`. O índice do encoder
base referencia um recibo com os SHA-256 dos arquivos do snapshot original.
O índice do ajustado contém o Safetensors e as configurações da arquitetura.

## Extração a partir da coleta de validação

O executor SF2-04 chama o worker com a política fixa de coleta
(`tau=0.50` e `delta=0.00` nos dois campos). Depois de selar o JSONL de decisões
originais, extraia seus vetores para um arquivo novo. O comando confere hashes,
ordem de IDs, contratos, política da coleta e identidade do pacote. O journal
de tempos externos permanece com a avaliação SF2-04.

```sh
rtk proxy "$python" -B -m "$sf2.training" scores \
  --package "$dir/training-01/package" --package-sha256 "$package_sha256" \
  --validation "$dados/validation.jsonl" --policy "$collection_policy" \
  --predictions "$validation_predictions" --predictions-sha256 "$predictions_sha256" \
  --output "$dir/validation-scores.json"
```

O extrator reaproveita os vetores das decisões armazenadas antes do replay
dos 225 cortes. A leitura e a auditoria dos frames dispensam carregar o
modelo. A extração guarda o motivo dos campos que tiveram erro de inferência.

## Controles de implementação

```sh
rtk proxy "$python" -B -m unittest -v \
  "$sf2.adapter.test_decide" "$sf2.training.test_supervise" "$sf2.training.test_package"
```

O teste de artefatos usa um microencoder BERT de fixture, inicializado
localmente, e cabeças logísticas de fixture com parâmetros determinísticos.
O teste usa bibliotecas reais e não ajusta pesos. Para a atividade do card,
rode somente `"$sf2.adapter.test_decide.AdapterTests.test_exercicio_retirar_prioridade_sem_chamar_categoria"`.
O primeiro envio tem categoria e prioridade. O segundo envia o mesmo
texto e categoria, omite prioridade e registra uma chamada exclusiva ao
especialista de prioridade.
