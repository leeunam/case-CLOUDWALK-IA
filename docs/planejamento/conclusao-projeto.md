# Conclusão do projeto — execução autorizada

Data: 24/11/2026. Base de partida: `380f45bab5708d344f41bf554452586980c65743`.
O responsável respondeu «autorizo, so prossiga para concluir todo projeto»
à proposta concreta de até seis chamadas R2 e, somente se aprovadas, até
44 chamadas finais, mantendo o teto cumulativo de US$ 10. A continuidade
abrange as tarefas pendentes do projeto; não altera os critérios congelados,
autoriza gastos de hospedagem nem aprova um classificador reprovado.

## Contratos e limites

- Preservar as instruções, os casos, os rótulos, os perfis históricos e os
  limites R2 já revisados. Não ajustar o candidato usando os novos resultados.
- Reutilizar a conta SQLite v4 existente no escopo global. Não inicializar
  outra conta real. Verificar identidade, gastos, reservas e bloqueios antes
  de despachar. A referência anterior era US$ 0,02300927; consultar o estado
  atual, sem presumir saldo do fornecedor.
- Até 50 chamadas novas: development seis, final até 44 apenas com o gate
  real completo aprovado. Concorrência um, uma tentativa, sem retries ou
  retomada de inferência. Não fazer uma chamada extra de sondagem.
- Conferir tarifas e limites publicados antes do ensaio. Reservar considerando
  capacidade máxima faturável; `max_tokens=128` não é tratado como garantia
  de que todo custo estará limitado a 128 tokens.
- Somente o integrador carrega a chave local, sem imprimi-la, copiá-la para
  relatórios ou enviá-la aos agentes. Agentes usam fixtures e exemplos.
- Um gate reprovado impede o final. Registrar o resultado e continuar tarefas
  independentes; não afrouxar critérios nem iniciar B/C automaticamente.
- C06 depende da elegibilidade comprovada e da decisão de adoção; preservar
  contrato de proveniência, correção humana, idempotência e revisão integral.
- Manter monólito modular Rails API + React, Kafka e canais simulados. E01
  (atendente real) continua posterior à conclusão/publicação e sujeito a
  desenho e limite próprios; o classificador não é o atendente.
- Preservar a exclusão preexistente do PDF. Worktree/branch por implementação,
  revisão independente e integração local pelo chat central. Sem push
  incidental, criação de infraestrutura paga ou exposição de credenciais.

## Sequência verificável

| Frente | Entrega e prova | Dependência |
| --- | --- | --- |
| C05-R2 real | Pré-voo atual, manifesto, desenvolvimento, final condicionado, resultados brutos e auditorias de métricas/custos. | Autorização acima e conta/chave existentes. Reutilizar `.worktrees/r2-avaliador`, `feat/r2-avaliador`. |
| F09 preparação | README atual, comando da demonstração completa, roteiro e dependências reproduzíveis. Verificar em ambiente isolado. | Pode preparar em paralelo sem alterar classificação/contratos compartilhados. |
| C06 | Complemento pelo modelo elegível, revisão e correção humana com origem correta. | Resultado real e decisão de adoção; contrato coordenado aqui antes da implementação. |
| C07/F09 aceite | Percorrer três canais, duas marcas, complemento/revisão, broker e handoff, instalação limpa e relatório final com limitações. | Integração aprovada; R01/R02 já aceitas. |
| F10 preparação | Build estático, proxy para Rails e `/cable`, serviços completos, acesso de demonstração, persistência e configuração de publicação. | Pode preparar localmente; destino de hospedagem solicitado ao responsável. |
| F10 publicação | URL acessível, fluxo completo, reinício com dados preservados e verificação externa. | F09 e destino/acesso concretos. Não presumir servidor ou orçamento novos. |

A auditoria inicial é somente leitura. A execução do ensaio não muda código.
Cada implementação posterior recebe uma fatia de escopo e base explícitas,
com requisitos/aceites antes do código e evidência de verificação depois.
Escolhas rotineiras necessárias para cumprir os contratos existentes serão
resolvidas pelo integrador dentro da autorização de continuidade, sem pedir
novamente permissão para o mesmo trabalho. Preferências de hospedagem ou uma
nova estratégia para um modelo reprovado continuam decisões distintas.

## Participação e estado

O responsável quer aprender. Cada passagem mantém explicação curta, arquivos
de referência e um exercício. O chat central informa resultados e barreiras
concretas e continua o trabalho independente quando aguarda informação.
Este plano não declara o projeto concluído: o aceite depende das provas acima.
