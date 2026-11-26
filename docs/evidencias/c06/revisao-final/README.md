# Revisão final de C06/C07

O [parecer amplo](final-review.md) aceitou o fluxo local e apontou um P2 de
publicação e quatro P3 no schema e no verificador. O
[relatório de correções](final-fix-report.md) registra os testes executados.
A [revisão focal](final-fix-review.md) aprovou os cinco ajustes em
`977ec3f21096d66c6b462d3cc94880e4a94eb490`. Os três textos registram seu
momento na sequência. A integração do schema e o aceite público em SetFit
foram concluídos na sequência pelo integrador.
[Publicação e evidências](../../../c07-publicacao-setfit.md).

- O serviço Python privado executa a inferência. As regras de domínio,
  transições e persistência ficam no monólito Rails.
- C06-B e C06-C avançaram em paralelo após o contrato de C06-A, com
  arquivos sob responsabilidade de cada frente. O aceite integrado juntou
  o cliente Rails, o serviço residente e os consumidores Kafka.
- O pacote, os pesos e as políticas aprovadas conservaram suas identidades
  e ficaram em montagem somente leitura. [Decisão D018 e identidades](../../../planejamento/classificacao-comparativa/sf2/decisao-adocao-r1.md).
- Após a interrupção do leitor Kafka no aceite C06, a leitura retomou
  os mesmos eventos persistidos. [Aceite integrado C06](../aceite-integrado/README.md).
- O integrador incorporou o schema versionado com aplicação por três vias
  para preservar o patch local do responsável.
