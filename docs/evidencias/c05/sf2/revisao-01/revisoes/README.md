# SF2-R1 — decisões e revisões

A emenda e a execução do intervalo `9bb5214..53e3e87` passaram por revisão
independente de SPEC e QUALITY. A aprovação limita-se à validação pública.
O teste final continua fechado, sem adoção ou liberação da aplicação.

- [Implementação e testes por fixtures](implementacao.md).
- [Primeira revisão](revisao-implementacao.md) e [correção aprovada](revisao-correcao.md).
- [Execução única](execucao.md) e [revisão final global](revisao-final.md).

Os relatórios foram copiados integralmente. Referências de caminho e linha
apontam para as worktrees e commits descritos, não para esta pasta.

## Decisões de coordenação

1. Interpretar “boa, prossiga” como aprovação da extensão offline recomendada,
   sem novo treino, inferência ou final. Se a interpretação estivesse errada,
   o custo seria o replay local de 45 combinações, sem gasto de API ou
   exposição dos 120 casos.
2. Registrar emenda e cards para manter o fluxo SDD solicitado. O custo é
   manter documentação adicional, sem mudança de produto.
3. Extrair o replay puro preservando a API original e atestar separadamente
   fontes históricas e atuais. O risco seria regressão de avaliação; a
   paridade integral das 225 e as revisões verificaram essa fronteira.

A correção do consumo de bytes autenticados ocorreu antes da rodada real.
Os desvios de pré-voo e leitura incidental registrados na execução não
alteraram seus insumos ou o resultado, conforme o parecer final.
