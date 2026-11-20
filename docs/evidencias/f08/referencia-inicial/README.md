# Primeira tentativa da referência

Executada em 2026-11-20, revisão `10125a57a8d72abd69a646dea0970cca59cf3ce2`.
O lote `f08-reference-1795207088594-f6c560` foi interrompido na terceira
rodada. A matriz preserva as duas aprovações, o bloqueio de medição da terceira
e as três rodadas não executadas. Esta pasta não é uma matriz completa.

Cada rodada ofereceu 1.500 novos casos em cinco minutos e 300 continuações,
com mais 120 segundos de observação. O estado `concluído` de uma entrada no
relatório significa resposta persistida. Na aplicação, os 1.200 casos sem
continuação permanecem em `ai_active`; os 300 com continuação foram resolvidos
pelo mock. Isso não significa 1.500 casos resolvidos por rodada.

Na terceira rodada, a obtenção final do intervalo Kafka falhou com
`KafkaException` após 3.177 ms. Os dados SQL mostram as respostas, mas faltam
os registros Kafka necessários à reconciliação causal. O relatório continua
`bloqueado`; as metas numéricas isoladas não substituem a evidência ausente.
Não foi possível recuperar a captura depois da limpeza da pilha.

`dados-brutos.tar.gz` contém os 64 arquivos originais do lote, incluindo
planos, recibos, amostras SQL/lag/recursos, snapshots, reconciliações, capturas
Kafka disponíveis e relatórios. São dados sintéticos, sem credenciais ou
cookies. `inventario.json` lista caminhos, tamanhos e SHA-256 de cada arquivo;
`SHA256SUMS` identifica o arquivo compactado. Os relatórios e manifestos estão
também expostos nesta pasta para leitura direta.

Para verificar, confira o SHA-256 do arquivo compactado e extraia-o em uma
pasta vazia. Compare os arquivos extraídos com `inventario.json`. O código
registrado no manifesto permite recalcular o relatório com as mesmas entradas.
