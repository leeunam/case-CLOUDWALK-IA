# C05-R2 · Desenvolvimento real interrompido

Em 24/11/2026 foram feitas as seis chamadas de desenvolvimento autorizadas,
uma tentativa por caso, em série. O resultado **não libera o teste final**:
cinco respostas chegaram e o último caso terminou em timeout local. Houve
também uma conclusão indevida e tempos acima da meta. Os 36 novos finais e
13 controles não foram executados. O relatório de prefixo registra
`inconclusive` para elegibilidade; não existe gate aprovado ou selo desta
execução. Não houve repetição, ajuste do candidato ou adoção no Rails.

Fonte executada: `4d94094672f7170248ca083bbf0572c21c3494f5`.
Branch `feat/r2-avaliador`, worktree `.worktrees/r2-avaliador`.
O [plano de conclusão](planejamento/conclusao-projeto.md) registra a autorização
de continuar o projeto e a separação entre teste, adoção e publicação.

## Resultado dos seis casos

| Condição | Medido | Exigido para liberar o final |
| --- | ---: | ---: |
| Alvos corretos, incluindo abstenção explícita | 5/8 | 8/8 |
| Campos válidos do canal preservados | 4/4 | 4/4 |
| Conclusões corretas nos classificáveis | 3/3 | 3/3 |
| Revisões integrais nos casos esperados em revisão | 2/3 | 3/3 |
| Urgente reconhecido | 1/1 | 1/1 |
| Casos com erro ou timeout | 1/6 | 0 |
| p95 total, nearest-rank, seis amostras | 4.995,002 ms | até 3.000 ms |

O caso `jev-013` exigia abstenção na categoria, mas recebeu `payouts` e
conclusão automática. `jev-039` teve timeout nos dois campos. Entre os cinco
casos sem timeout, o p95 descritivo já seria 4.234,344 ms. Portanto resolver
somente o custo tardio ou o timeout não faria este desenvolvimento passar.
Essa amostra pequena não mede a qualidade nos 36 casos finais nem comprova
uma taxa de erro em produção. O primeiro final anterior continua intacto.

## Custos e conciliação

As cinco respostas tiveram US$ 0,00318878 informados e conciliados. O timeout
manteve inicialmente US$ 1,7837 de reserva conservadora, sem tratar esse valor
como cobrança real. O registro autenticado da Feita mostrou seis chamadas
novas na janela correspondente, com a sexta concluída no fornecedor e custo
exibido de US$ 0,000675, arredondado a seis casas. A atribuição foi conferida
pela sequência, horários, tokens e custos das cinco respostas anteriores.

Após [auditoria independente](evidencias/c05/r2-ensaio-real-01/auditoria-independent-development.md),
o integrador conciliou o último caso em **US$ 0,000676 como limite superior
conservador**, sem afirmar custo exato. A conta existente ficou com:

- Desenvolvimento R2 contabilizado conservadoramente: **US$ 0,00386478**.
- Acumulado com os experimentos anteriores: **US$ 0,02687405**, sob o teto
  cumulativo de US$ 10. Isso não representa saldo comercial do fornecedor.
- Seis reservas novas liquidadas e nenhuma pendente. O marcador de expiração
  financeira e o estado `interrupted` foram preservados.

A [exportação inicial](evidencias/c05/r2-ensaio-real-01/financeiro-apos-development.json)
preserva a reserva antes da conciliação; o [registro final](evidencias/c05/r2-ensaio-real-01/financeiro-conciliado.json)
e o [recibo conservador](evidencias/c05/r2-ensaio-real-01/recibo-conservador-timeout.json)
registram a alteração contábil. A observação original de timeout, o relatório
e a decisão local não foram reescritos como resposta bem-sucedida. Nenhuma
conta real nova foi aberta e nenhuma chamada adicional foi feita.

## Verificação e continuidade

O checker `observed-total-r2` aprovou a consistência do prefixo. A auditoria
independente refez os oito alvos, denominadores, tempos, hashes e custos.
O estado privado foi conferido pelo integrador após `Account.reconcile`:
seis novas reservas `settled`, `financial_expired=1` em `jev-039`, execução
`interrupted`, sem bloqueio financeiro e acumulado US$ 0,02687405.
Os comandos de inferência não devem ser repetidos para reproduzir a análise.
Para conferir os artefatos sem fornecedor:

```sh
rtk proxy env -u FEITA_API_KEY -u TYPESAFE_API_KEY python3 -B script/check_classification_contracts.py --profile observed-total-r2 --report docs/evidencias/c05/r2-ensaio-real-01/development/prefix-report.json
```

C06/C07 continuam bloqueados por ausência de classificador real elegível e
decisão de adoção. A alternativa A foi testada e não será ajustada/repetida
automaticamente. Uma nova estratégia exige decisão de escopo própria. F09 e
a demonstração pública podem ser preparadas com classificação fixture
explicitamente identificada e atendimento simulado, conforme o MVP, sem
atribuir qualidade ou respostas reais ao Qwen.

**Exercício.** Compare `jev-013` no gabarito e na decisão local. Explique por
que um código válido pode estar errado e por que a cobrança tardia de
`jev-039` não permite substituir seu timeout no relatório.
