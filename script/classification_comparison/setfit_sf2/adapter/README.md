# Worker JSONL SF2-03

O executor passa o comando completo como uma lista de argumentos. Use
`--package-sha256` com a identidade registrada na evidência de execução
confiável. O worker verifica todos os membros do pacote e carrega os
especialistas e a política antes de emitir `{"type":"ready"}`.

```sh
sf2=script.classification_comparison.setfit_sf2
rtk proxy "$python" -B -m "$sf2.adapter" \
  --package "$package" --package-sha256 "$package_sha256" --policy "$policy"
```

A partir de READY, envie um `input` por linha em stdin. O worker confirma a
máscara contra o canal e verifica versão, códigos e descrições do catálogo
ativo. Cada especialista solicitado recebe apenas o texto. O worker preserva
os campos recebidos, registra as escolhas brutas e só publica complementos
quando todos os campos solicitados passam. Responde com uma `decision` por
linha e termina em EOF. Logs vão para stderr. Erros que impedem formar uma
decisão conforme o contrato encerram o processo com código diferente de zero.

O `elapsed_ms` do frame mede processamento local. O executor registra a
latência externa, com transporte e validação da resposta, e o tempo até
READY separadamente. O prazo por caso e a interrupção externa pertencem ao
executor SF2-04.

## Controle para integração com SF2-04

Use este processo somente com entradas de **fixture**. Ele executa o mesmo
loop e a mesma política do worker com especialistas fictícios e vetores
determinísticos. Os argmax são `pix` e `urgent` quando os especialistas
correspondentes são chamados.

```sh
rtk proxy python3 -B -m "$sf2.adapter._fixture_worker" --policy "$policy"
```

Identidades da fixture para o auditor:

- `package_sha256` é o dígito `2` repetido 64 vezes.
- `model_sha256.category` e `model_sha256.priority` são o dígito `3` repetido 64 vezes.
- `policy_sha256` é o SHA-256 dos bytes do arquivo indicado.
- A ordem de classes é a ordem das listas `labels.category` e `labels.priority`
  do protocolo, com `informacao_insuficiente` em último lugar.

O controle verifica transporte, seleção dos especialistas e aplicação atômica.
Os resultados são evidência da implementação com fixtures.
