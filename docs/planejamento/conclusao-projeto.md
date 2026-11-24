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

### Resultado da frente real

A R2 de desenvolvimento foi executada e interrompida: 5/8 alvos corretos,
uma conclusão indevida, p95 4.995,002 ms e timeout no sexto caso. O final não
foi enviado. A auditoria conferiu os registros, e a conciliação conservadora
da cobrança tardia preservou a interrupção. Acumulado conservador
US$ 0,02687405, sem reservas pendentes. O [resultado](../c05-r2-resultado.md)
registra origem, custo exato indisponível no último caso e limitações.
Uma pergunta de escopo foi enviada ao responsável: concluir a demonstração
com fixture identificada e evolução real pendente, ou preparar outra estratégia
antes do fechamento. O trabalho independente F09/F10 continua enquanto isso.

## Destino gratuito confirmado — F10

O responsável informou não ter servidor e autorizou uma opção gratuita em
24/11/2026. A demonstração usará Cloudflare Quick Tunnel sobre a instância
local isolada. Não exige conta/domínio e não cria servidor pago. A URL é
temporária, muda ao recriar o túnel e depende do computador/processo ligados;
o serviço não garante disponibilidade e limita a 200 requisições em voo.
Essas condições estão na [documentação oficial](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
Isso é publicação de demonstração, sem alegação de hospedagem permanente.

Preparar uma composição própria: mesmos serviços do aplicativo, frontend
compilado servido pelo Caddy, proxy para API e `/cable` na mesma origem e
Cloudflare terminando HTTPS. Banco, Kafka, ponte e API ficam sem portas
públicas; apenas o frontend HTTP de origem fica em loopback para teste e
conexão do túnel. Volumes novos exclusivos preservam dados sintéticos.
O Caddy suporta o [proxy e fallback SPA](https://caddyserver.com/docs/caddyfile/patterns)
e o [upgrade WebSocket](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).

O Rails opera em production, com cookies seguros e origem pública exata para
WebSocket. A configuração de proxy deve tratar a terminação de SSL sem ciclo
de redirecionamento, seguindo [assume_ssl](https://guides.rubyonrails.org/configuring.html#config-assume-ssl),
com acesso direto ao backend limitado à rede interna. O login sintético em
production exige habilitação explícita e credenciais privadas geradas, sem
habilitar valores de desenvolvimento por padrão. Não criar outro sistema de
identidade. Preservar CSRF, isolamento e revogação.

A configuração publicada permanece em fixture, sem chave de fornecedor, até
uma decisão válida para o classificador. A R2 real de desenvolvimento foi
interrompida e não liberou o final; publicar a demonstração não libera C06.
Preparar/testar localmente antes de iniciar o túnel público. O integrador
verifica HTTPS externo, login, WebSocket, fluxo Kafka/handoff e persistência,
registrando o período de disponibilidade e como parar/reabrir a URL.
