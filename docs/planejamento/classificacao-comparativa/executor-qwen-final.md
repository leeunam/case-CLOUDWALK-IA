# C05-E · Executor final e orçamento cumulativo

O responsável autorizou adaptar o executor e o controle de custo com testes
simulados, mantendo o teto total de US$ 10. Autorizou separadamente **uma**
nova chamada real de desenvolvimento para conferir disponibilidade. Essa
exceção não autoriza executar o lote final. A referência normativa continua
[CLASS-SPEC-001](especificacao.md), com a emenda de foco Qwen e o
[plano de qualificação](qualificacao-qwen.md).

## Restrições globais

- Perfil `observed-total-1.1`, protocolo de qualidade 1.1, relatório 1.2,
  IPC 1.1; os 36 IDs finais e 13 controles congelados, até 44 POSTs,
  concorrência 1 e uma tentativa por caso. Preservar bytes de protocolo,
  dataset, divisão, catálogo, rubrica, prompt, política e resultados históricos.
- Reutilizar projeção, decisão, cronômetro, diário e relatório da C02 e a
  requisição/interpretação Qwen existentes. Não criar uma régua concorrente.
- A implementação e todos os testes desta tarefa são offline. Não carregar
  chave, abrir o arquivo local da chave, chamar fornecedor ou executar GLiClass.
  A chamada real única fica exclusivamente com o integrador, pelo executor
  histórico já revisado e com autorização própria e proteção de execução única.
- Manter US$ 10 como teto **global**, incluindo gasto anterior e reservas
  desconhecidas. Não considerar estimativa como débito observado ou confirmar
  unidade monetária por presunção. Não aumentar teto para acomodar a reserva.
- Preservar a distinção entre código pronto, teste simulado, limite financeiro
  declarado/documentado e qualidade real. Sem manifestação própria de execução
  final, o caminho real fica bloqueado antes da credencial ou do despacho.

## Task 1: Executor final com contabilidade persistente

Implementar em `script/classification_comparison/c05/`, com novos módulos
pequenos para CLI/adaptador e orçamento. Não modificar o contrato público Rails
nem o protocolo/IPC. O caminho do piloto antigo permanece reproduzível.
Atualizar `docs/c05.md` com comandos offline, configuração e limitações.

1. Consumir o pré-voo confiável da C02 no perfil novo e gerar o plano completo
   de 36 relatos/13 controles. `--dry-run` não inicia adaptador, não consulta
   credencial e não cria/altera contabilidade. Registrar a revisão e os hashes.
2. A execução final exige confirmação explícita de execução e manifesto
   habilitado, vinculado ao perfil/protocolo, identidade, configuração, conjunto
   e hashes de entrada, prompt/política e conta persistente de orçamento.
   Rejeitar manifesto do piloto, IDs extras/de desenvolvimento, adulterações,
   concorrência/retentativa, teto maior que US$ 10 e limite monetário inválido
   antes da credencial. Exemplos versionados ficam desabilitados.
3. O novo adaptador reutiliza a classe Qwen existente e explicita sua versão.
   Envia `max_tokens=128` e `reasoning={"enabled":false}` como no piloto real;
   o envio não comprova por si só o limite de todos os tokens faturáveis.
   Pré-voo exige tarifa, limites faturáveis e suas referências declaradas;
   exemplos reais usam os limites conservadores conhecidos, não limites menores
   inventados para caber no orçamento. O uso de simulação fica inequívoco.
4. A conta financeira é persistente, compartilhada entre processos/execuções
   por caminho explícito e identidade vinculada ao manifesto. Não iniciar
   automaticamente uma conta vazia a cada lote. Preferir SQLite da biblioteca
   padrão, com inicialização explícita que recusa sobrescrever estado existente,
   teto até US$ 10 e gasto anterior obrigatório. Usar Decimal exato, sem floats
   para reservas e saldo. Conta ausente, corrompida ou incompatível bloqueia.
5. Reservar e persistir atomicamente o pior custo declarado **antes** do envio.
   A soma de gasto anterior, custos conciliados e reservas pendentes não pode
   ultrapassar o teto. Serialização cobre disputa entre dois processos pela
   última reserva. Reinício não restaura saldo nem permite repetir o mesmo
   manifesto/caso. Registrar a configuração da execução e o caso de cada reserva.
6. Custo USD observado e validado pode substituir a reserva e liberar apenas
   o excedente comprovado. Sem unidade/usage, timeout ou processo encerrado,
   manter a reserva. Estimativa não libera saldo. Conciliação posterior precisa
   de recibo/atribuição explícitos e não pode liquidar duas vezes ou ocultar
   custo acima do reservado. Violação congela próximos despachos e fica visível.
   Como alternativa pequena, aceitar `usage.credits` com fonte, confirmação e
   conversão explícitas: a página oficial documenta esse campo e informa que
   um crédito equivale a US$ 0,01. Não inferir daí a unidade de `usage.cost`.
   Converter com Decimal, preservar a evidência original e, se duas fontes
   monetárias verificadas existirem, contabilizar o maior valor. Créditos
   ausentes/inválidos não viram custo zero. A conversão fica desligada no
   exemplo real até confirmação no manifesto. Cobrir essas condições nos testes.
7. Não exigir reservar antecipadamente o pior custo das 44 chamadas juntas.
   Aplicar a guarda antes de cada despacho; saldo insuficiente interrompe com
   prefixo auditável da C02 e motivo financeiro, sem inferir o restante nem
   declarar aprovação. Sem custo conciliável, a reserva histórica pode permitir
   apenas um prefixo: documentar essa limitação e não prometer lote completo.
8. O CLI não pode executar novamente o mesmo manifesto para completar ou
   repetir casos silenciosamente. Um lote interrompido fica inconclusivo.
   Retomada de inferência/novo ensaio não faz parte desta mudança. Não transformar
   observações antigas em medições novas com um cronômetro de replay.
9. Testar comportamentos relevantes: plano final e versões, todos os casos com
   transporte simulado, campos válidos/abstenção preservados, rejeição antes de
   chave/rede, custo conhecido/desconhecido/estimado, timeout/crash, processo
   concorrente pela última reserva, persistência após reinício, repetição de
   manifesto/caso, moeda inválida/NaN/negativo, gasto anterior, teto excedido e
   interrupção financeira com prefixo. Não criar testes que apenas espelham código.

Não adicionar serviço de billing, painel de custos, agentes de atendimento
reais, autorização automática de chamadas ou ajustes de modelo. Inicialização
da conta real e investigação da cobrança ficam com o integrador; os testes
usam somente diretórios temporários e valores sintéticos.

## Task 2: Revisar e integrar a implementação offline

Revisão independente de especificação e qualidade, correções dirigidas e uma
revisão ampla final. Conferir contratos e regressões pertinentes C02/Qwen,
fontes congeladas e 17 históricos. Registrar resultados efetivos, pendências,
comandos, branch/worktree/base e exercício. Integrar somente após os aceites.
Não converter a autorização de um único reteste em autorização do lote final.
