# C05 · Registro de resultado e decisão pendente

Data: 24/11/2026. Fonte executada:
`19a56fe3dc4fb80a48122182fcc6bcdf1d9855d7`.

**Estado:** resultado técnico informado ao responsável, que em 24/11/2026
autorizou prosseguir com o planejamento da melhoria de abstenção e de um novo
teste. Depois escolheu A, liberando sua implementação offline. A autorização
de consumo futuro continua pendente. Não há aprovação de adoção do candidato
reprovado.

## Contexto

O responsável autorizou um lote final Qwen sob os critérios congelados da
CLASS-SPEC-001 e perfil `observed-total-1.1`. O lote concluiu os 36 relatos e
13 controles, com 44 chamadas, sem repetição. GLiClass estava fora da etapa
final por decisão anterior; não se trata de uma comparação pareada final.

## Resultado vinculante dos critérios

**Não elegível nesta configuração (`fail`).** Falharam a exigência de zero
conclusões em casos de revisão obrigatória (resultado 3/7) e o acerto mínimo
de 90% da categoria aplicada (19/22 = 86,36%). O p95 de 2.493,510 ms e o
reconhecimento de 6/6 urgentes passam, mas não eliminam esses dois vetos.
[Relatório e evidências](../../c05-resultado.md).

## Consequências

- C06 continua bloqueada; nenhuma mudança no classificador do produto Rails.
- O teste final fica consumido e preservado, sem ajustes de rótulos ou repetição.
- Teto financeiro continua US$ 10 cumulativos. Lote conciliado em US$ 0,02197127;
  total com os pilotos conservadores US$ 0,02300927, sem reserva pendente.
- Uma nova rodada requer decisão explícita de escopo, dados de desenvolvimento
  e novo teste independente. Nenhum modelo foi escolhido automaticamente.

O planejamento autorizado foi registrado na
[proposta C05-R2](rodada-2-proposta.md). O responsável escolheu instruções mais
conservadoras de uma chamada, com avaliação independente, preservando este
resultado negativo e o teto financeiro cumulativo.
[Implementação offline](rodada-2-implementacao.md), sem adoção ou nova inferência.
