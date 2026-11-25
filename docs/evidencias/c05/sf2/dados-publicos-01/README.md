# SF2-01 — trilha de revisão dos dados públicos

Esta pasta preserva os insumos e pareceres da revisão dos 150 relatos de
treino e 90 de validação. Não contém o teste final SF2 reservado, pesos,
previsões, métricas do SetFit ou chamadas a fornecedores.

## Versões e anotações

- `50ee50a583c5c6e359ac075919fcb3a2944c805c`: autoria A inicial de 240 relatos.
- `bce33eeadd262b91a7f85883ce50df86b8eebcd2`: 82 substituições após a auditoria
  semântica e a adjudicação dos pares incertos.
- `e68577d84b3b9aa29b93d0e155f9d289a65f6cc8`: quatro substituições pontuais
  após a segunda revisão. Os textos desta versão receberam parecer de novidade
  favorável. `review.md` registra a aprovação independente da conciliação;
  o commit do manifesto materializa esse aceite sem alterar os textos.

Cada pasta `public-b*` contém a projeção cega e as respostas originais do
anotador B. O anotador não recebeu os rótulos A, as quotas ou o final reservado.
Na última rodada, B foi selado antes de o mesmo agente começar a revisão de
novidade. `conciliation-bindings.json` vincula cada texto atual à versão que B
efetivamente leu: 158 respostas da primeira anotação, 78 da segunda e quatro da
terceira. Houve concordância nos 480 campos de categoria e prioridade; isso
mede concordância dos anotadores, não acerto de um classificador.

## Novidade e comprimentos

`novidade/` preserva o primeiro parecer, a adjudicação e as duas reavaliações.
As fontes históricas e seus hashes estão nos relatórios. A revisão combinou
vizinhos lexicais com leitura dos eventos: ausência de duplicata normalizada ou
Jaccard de 0,80 não foi suficiente para aceitar os primeiros rascunhos.

A revisão final documenta 622 pares obrigatórios, 170 complementares e sete
comparações adicionais dentro da mesma partição. Pareceres anteriores foram
reutilizados somente quando os dois textos conservaram os mesmos hashes.
Não restaram substituições pendentes na projeção pública e nos históricos
declarados. Esse exame não demonstra independência de todos os textos possíveis.

`token-lengths.json` registra os 240 comprimentos com o tokenizer pinado,
incluindo tokens especiais e sem truncamento. O maior comprimento foi 78;
o limite aprovado é 128. O recibo vincula os bytes de treino e validação.

## Aceite reproduzível

O aceite completo exige o manifesto público, as duas anotações conciliadas,
o recibo de revisão independente e os comprimentos reais vinculados aos dados.
A validação de estrutura das anotações, isoladamente, não substitui esse aceite.
`review.md` registra SPEC e QUALITY aprovadas. O recibo independente está em
`review-receipt.json`, SHA-256
`11b65d96576176808d7262a2ed917f52a1bb4f8b55e453a48dc42ec778005ef4`.
O manifesto aceito vincula esse recibo e os comprimentos aos mesmos dados.

Na raiz do repositório integrado:

```sh
rtk proxy python3 -B -m script.classification_comparison.setfit_sf2.contracts \
  manifest publicManifest docs/planejamento/classificacao-comparativa/sf2/dados/manifest-public.json \
  --file train=docs/planejamento/classificacao-comparativa/sf2/dados/train.jsonl \
  --file validation=docs/planejamento/classificacao-comparativa/sf2/dados/validation.jsonl \
  --file annotations=docs/planejamento/classificacao-comparativa/sf2/dados/annotations-public.jsonl \
  --file review_receipt=docs/evidencias/c05/sf2/dados-publicos-01/review-receipt.json \
  --file token_lengths=docs/evidencias/c05/sf2/dados-publicos-01/token-lengths.json
```

Resultado esperado do pacote completo: `valid: true`, `stage: accepted`,
`accepted: true`, com 150 registros de treino e 90 de validação. Isso autoriza
o uso futuro desses dados; não representa treinamento ou qualificação SF2.

## Limitações

Os relatos são sintéticos e balanceados por desenho. Autoria, anotações e
auditorias foram realizadas por agentes de IA; modelos da mesma família podem
compartilhar erros. Não houve validação humana de todos os rótulos nem
comparação com uma amostra real de atendimentos. A concordância dos anotadores
e o parecer de novidade não antecipam qualidade, cobertura ou latência do SetFit.
