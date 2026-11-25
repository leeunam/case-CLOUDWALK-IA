# Complemento da referência

Quatro rodadas executadas em 2026-11-20, revisão
`dfbcc79f4ced07e5460eb73d06e956d94799d453`. As três primeiras foram aprovadas;
a quarta foi reprovada porque os consumidores encerraram após a perda de
associação ao grupo Kafka. A coleta final foi completa nas quatro rodadas.

Este lote complementa as rodadas 01 e 02 da primeira tentativa. O conjunto
final contém três rodadas por condição e publica uma tentativa adicional
bloqueada por falta de evidência, sem substituir seu veredito original.
[Resultados conjuntos](../referencia.json) · [Comparabilidade](../comparabilidade.json) ·
[Diagnóstico da falha](../../../f08-incidente-consumo.md).

`dados-brutos.tar.gz` preserva os 95 arquivos originais do lote. Os
relatórios, manifestos e diagnósticos também estão expostos para leitura
direta. `inventario.json` lista tamanho e SHA-256 de cada arquivo; confira
o arquivo compactado com `SHA256SUMS` antes de extraí-lo em uma pasta vazia.
Os dados são sintéticos e não incluem credenciais ou cookies.

As leituras de diagnóstico dos dois consumidores foram adicionadas durante
a última rodada, depois da falha observada e antes da limpeza. Não houve
reinício assistido nem correção do produto. Os dados brutos permitem distinguir
entradas aceitas, respostas presentes, falhas e continuações não enviadas.
