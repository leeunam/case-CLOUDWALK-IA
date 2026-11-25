# C05-E · Decisões de implementação e passagem

Componente offline aceito no código `e4ce14c95a4a59737b000bcc8dfa21009a1d566d`.
Base `10dbd6f2ec18f0fc44dd3b4cfe60d79f04fa9e48`, branch
`feat/executor-qwen-final`, worktree `.worktrees/c05-comparacao`.
As decisões abaixo preservam o registro do integrador antes da remoção da área
temporária deste plano. Nenhuma autoriza o lote pago ou a adoção do modelo.

1. **Conta persistente separada do IPC.** Usar SQLite, identidade explícita e
   uma conta compartilhada entre execuções, com gasto anterior obrigatório.
   Isso conserva o teto entre processos sem reescrever contratos ou históricos.
   Se a escolha estiver errada, revisar armazenamento e vínculos do manifesto
   antes do lote real, preservando os débitos e reservas existentes.
2. **Margem para o valor “0015”.** O responsável confirmou dólares, mas a posição
   decimal não foi comprovada por recibo. A autorização do reteste único usou
   margem conservadora de US$ 0,015 além do piloto confirmado. Isso não é uma
   cobrança auditada nem saldo da conta. Se a interpretação estiver errada,
   conciliar pelos comprovantes antes de consolidar o gasto anterior da conta
   real. Os dois registros experimentais observados exibiram US$ 0,000518 cada.
3. **Extensão opcional do avaliador.** Pequenos callbacks antes e depois do
   candidato permitem reservar e interromper sem duplicar o executor C02.
   O comportamento padrão, o relógio canônico, o diário e as decisões são
   preservados. Se a integração se mostrar inadequada, revisar ou remover
   esses callbacks antes do lote real, sem alterar a régua de medição.
4. **Conversão de créditos somente confirmada.** A opção de converter
   `usage.credits` usa Decimal e exige confirmação e referência explícitas de
   US$ 0,01 por crédito. Não infere a unidade de `usage.cost` e permanece
   desativada no exemplo real. Duas fontes verificadas conservam o maior custo.
   Se a premissa estiver errada, desativar a conversão e reconciliar as reservas
   antes do lote real. [Referência arquivada](referencia-uso-creditos-2026-11-23.json).
5. **Expiração financeira independente do motivo da classificação.** O marcador
   é persistido e monotônico; uma divergência de modelo não pode ocultar o prazo
   excedido e liberar a reserva. Se estiver errado, corrigir a retenção antes do
   uso real, preservando o motivo canônico e a evidência original.
6. **Primeira conta suportada: versão 4.** Não existiam contas financeiras reais
   dos protótipos. Recusar versões incompatíveis sem alterar bytes reduz o risco
   de migrar um histórico incompleto. Se contas antigas precisarem ser usadas,
   preparar importação manual auditada de débitos e reservas; não apagar,
   reinicializar ou migrar automaticamente esses arquivos.
7. **Correção residual com escopo limitado.** Após a rodada consolidada da
   revisão final, dois resíduos conhecidos receberam uma correção pontual e
   validação independente: expiração financeira e recusa dos protótipos.
   A decisão concluiu invariantes do escopo já autorizado e não abriu uma nova
   frente. Se a delimitação estiver errada, reabrir o aceite afetado antes do
   lote real; não usar o aceite offline como aprovação de qualidade do modelo.

## Resultado e retomada

- Implementação: `24da473`, correção da tarefa `aee264c`, sincronização da
  documentação `511047d`, correção consolidada `20610ca`, correção residual
  `e4ce14c`. [Relatório de implementação](executor-relatorio-implementacao.md).
- Revisão da tarefa e correção:
  [parecer inicial](executor-revisao-tarefa.md) e
  [aprovação dirigida](executor-revisao-correcao.md).
- Revisão ampla e encerramento:
  [parecer inicial](executor-revisao-final.md),
  [revisão das correções](executor-revisao-final-dirigida.md) e
  [validação residual aprovada](executor-validacao-residual.md).
- [Aceite verificável](executor-aceite.json) e
  [conferência do roteiro por comando](executor-conferencia-cli.json).

A C05 completa continua aberta: os 36 relatos reservados não foram enviados
ao fornecedor. A conta real não foi inicializada. O lote final requer sua
própria autorização, gasto anterior consolidado e fontes financeiras
verificadas. C06 depende de resultados elegíveis e decisão humana de adoção.
Não houve push do código.
