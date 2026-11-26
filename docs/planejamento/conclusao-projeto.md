# Conclusão do projeto — execução autorizada

**Fechamento em 26/11/2026.** O recorte do MVP foi concluído com o
classificador SetFit R1 local e o atendente simulado via Kafka.
[Estado da entrega](../estado-entrega.md) · [Aceite público SetFit](../c07-publicacao-setfit.md).

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
Na abertura deste plano, o fechamento dependia das provas acima.

### Resultado da frente real

A R2 de desenvolvimento foi executada e interrompida: 5/8 alvos corretos,
uma conclusão indevida, p95 4.995,002 ms e timeout no sexto caso. O final não
foi enviado. A auditoria conferiu os registros, e a conciliação conservadora
da cobrança tardia preservou a interrupção. Acumulado conservador
US$ 0,02687405, sem reservas pendentes. O [resultado](../c05-r2-resultado.md)
registra origem, custo exato indisponível no último caso e limitações.
O responsável decidiu que a classificação real continua necessária antes do
fechamento e aprovou D — GPT-5.6 Luna, uma chamada — para preparação offline,
conforme a [proposta R3](classificacao-comparativa/rodada-3-proposta.md).
O trabalho independente F09/F10 continua; novas chamadas pagas só serão
propostas após a revisão do executor. Não encerrar C06/C07 por simples
substituição do modo real por fixture.

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

## Estado verificado em 24/11/2026

| Frente | Situação | Evidência |
| --- | --- | --- |
| C05-R2 real | Interrompida; final bloqueado, sem adoção. | [Resultado R2](../c05-r2-resultado.md). |
| F09 preparação | Completa e integrada, CLI e conversa no navegador verificadas. | [Roteiro](../f09.md) e provas em `docs/evidencias/f09/`. |
| F10 demonstração | Publicada em HTTPS com fixture; reinício e restauração real passaram. Responsável confirmou acesso pelo celular em dados móveis. | [Resultado e URL temporária](../f10-resultado.md). |
| C05-R3 offline | Candidata congelada, executor integrado e revisão ampla aprovada após correção `aafc8ce`. | [Guia e pré-voo](../c05-luna.md). |
| C05-R3 real | Seis chamadas autorizadas e executadas, 7/8 alvos, gate reprovado. As 44 finais ficaram bloqueadas; sem adoção. | [Resultado auditado](../c05-luna-resultado.md), acumulado US$ 0,02869232, sem pendências. |
| C06 e C07/F09 final | Aguardam qualificação real e decisão de adoção. | Contratos e classificação humana existentes preservados. |
| E01 | Trabalho posterior à conclusão e publicação, se houver tempo e desenho aprovado. | Atendente conversacional real continua separado do classificador. |

A preparação offline está concluída. O projeto inteiro permanece em andamento.
A publicação fixture não foi tratada como conclusão da classificação real.

### Resultado R3 real e decisão seguinte

A autorização de até seis chamadas reais e 44 finais condicionais foi registrada
em `e8434bb`. Foram feitas exatamente seis chamadas, sem sondagem ou repetição.
A Luna atingiu 7/8 alvos, com uma conclusão indevida em caso de revisão, p95
2.635,459 ms e custo US$ 0,00181827. A auditoria confirmou os resultados e os
recibos. O gate reprovou e as 44 finais não foram enviadas. Evidências em
[resultado Luna](../c05-luna-resultado.md), integrado a partir de `5c23d04`.

A continuação proposta é discutir uma revisão da instrução de suficiência,
com pares novos de desenvolvimento e rótulos independentes antes do ajuste.
Exigir evidência e veto verificável é uma alternativa de maior mudança.
Nenhuma nova candidata foi implementada, nenhum gabarito foi alterado e
nenhum consumo extra foi autorizado ou executado após a reprovação. C06/C07
continuam necessários; a demonstração pública permanece em fixture.

## Continuação autorizada — instrução Luna e frontend

Em 24/11/2026 o responsável escolheu revisar somente a instrução de quando
encaminhar para revisão, mantendo Luna, uma chamada, critérios e gabaritos.
A aprovação cobre preparação offline; não autoriza nova inferência paga.
Preservar integralmente a candidata e as evidências R3. Separar nova instrução
de pares novos de diagnóstico: autores distintos e revisão cega dos rótulos.
Congelar a instrução antes de reunir os pares e não acessar os 36 finais.
O diagnóstico offline confere contratos e desenho; não mede a nova Luna.

O responsável também pediu melhoria do frontend com referências Chatwoot,
Zammad e painel Web do Sidekiq. As orientações locais de interface já estão
disponíveis. A análise usa padrões operacionais das referências, sem copiar
marca ou inventar funções/indicadores. O escopo visual proposto cobre analista,
supervisão, login e simulador; a reorganização foi apresentada para escolha.
Rails, Kafka, contratos, autenticação e o orçamento do classificador permanecem
fora desta mudança de interface. As frentes usam branches/worktrees separadas.

### Entregas aceitas desta continuação

O responsável aprovou a reorganização completa do frontend. A UX01 foi integrada
em `3c00691` após revisões por tarefa e ampla, incluindo as correções `0da3897`
e `88d80be`. São 34 testes frontend aprovados, build com runtime e lock fixados,
aceite de operação/supervisão pela API real e inspeção móvel/desktop. A nova
interface foi publicada no mesmo túnel, preservando dados e conversa anterior.
[Guia e evidências UX01](../ux01.md).

A preparação R4 está concluída e revisada: instrução congelada, 16 diagnósticos
separados com duas rotulações por IA concordantes e executor dedicado à nova
candidata. O integrador reproduziu as duas etapas sintéticas; revisão ampla e
correções documentais `f6d6b76` foram aprovadas. Zero novas chamadas pagas e
zero medição de qualidade real R4. [Guia R4](../c05-luna-r4.md).

C05 real, decisão de adoção, C06 e C07/F09 final permanecem pendentes.
Um novo ensaio R4 exige pré-voo e autorização de consumo próprios. A publicação
fixture e o aceite visual não encerram o projeto nem habilitam o modelo real.

### UX02 — linguagem visual CloudWalk

Por pedido explícito do responsável, o tema da UX01 passou a usar preto/grafite,
branco quente e tipografia geométrica, sem logo CloudWalk. Gabarito OFL local é
uma aproximação gratuita da Cera Pro licenciada do site de referência. A organização
dos painéis, as funções e os contratos foram preservados.

Entrega `1adc941..8ac8a00`, branch `feat/estilo-cloudwalk`, aceita nas revisões
por tarefa e ampla, com 34 testes, build e inspeção desktop/móvel. A publicação
foi reaberta em novo endereço temporário. O endereço daquela publicação, as
provas, os limites e o roteiro constam no [registro UX02](../ux02.md).
C05 real/C06/C07 continuam pendentes e independentes.

## Retomada da conclusão — 24/11/2026

Após a UX02, o responsável pediu «termine o que falta do projeto». O integrador
retoma a sequência pendente e interpreta a continuidade dentro do teto de
US$ 10 já autorizado, com minimização de requisições. Não é uma nova fala
numérica do responsável nem autorização para hospedar com custo, mudar os
critérios ou repetir um candidato reprovado.

Executar a candidata R4 já congelada após revalidar preços, limites, conta e
executor. Até seis requisições de desenvolvimento; até 44 finais somente se
o gate real e seu selo passarem. Sem sondagem, retry, dados novos no final ou
consumo dos 16 diagnósticos adicionais. A aprovação anterior apenas offline
permanece como registro histórico; este pedido de conclusão é a nova base de
continuidade. O resultado pode reprovar, o que impede adoção e integração.

C06 depende de resultado elegível e decisão de adoção; C07/F09 final fecha os
fluxos e a reprodução. E01 permanece posterior/opcional. O pedido não autoriza
inferências ilimitadas na demonstração pública nem uso do teto experimental
como orçamento recorrente do aplicativo.

### Resultado R4 e estratégia seguinte

A R4 real fez seis chamadas, sem sondagem ou repetição. Conexão, formato e
tempo passaram: zero erros técnicos e p95 de 1.762,223 ms. O gate reprovou
com 7/8 alvos e 2/3 revisões integrais: no caso de desenvolvimento `jev-013`,
a categoria foi escolhida apesar da insuficiência de informação. As 44
finais não foram enviadas. O custo foi US$ 0,00224280 e o acumulado conservador
é US$ 0,03093512, com 62 reservas liquidadas e zero pendências na mesma conta.
[Resultado e evidências R4](../c05-luna-r4-resultado.md).

O responsável escolheu «Luna com evidência verificável: manter o modelo e
acrescentar validação conservadora; exige mudar o contrato e mais código».
Preparar essa estratégia em ambiente isolado, preservando históricos,
gabaritos, critérios, modelo e uma chamada por caso. Validar a origem dos
trechos e definir um veto conservador para suporte insuficiente; não
confundir citação literal com prova semântica. A nova candidata deve ser
congelada antes de usar o conjunto final. A preparação não faz chamadas
pagas nem altera a publicação fixture. C06/C07 continuam condicionadas à
qualificação real e à decisão de adoção.

O [subplano R5](classificacao-comparativa/rodada-5-implementacao.md) fixa o contrato privado e o veto local auditável. A frente candidata é isolada do final até o congelamento e não altera bytes históricos R3/R4. A preparação não mede qualidade do fornecedor nem faz chamadas pagas.

A R5-A foi implementada e aprovada na revisão por tarefa em `53b1131`, com 29 testes offline e 57 propostas sintéticas dirigidas do revisor. As fontes semânticas foram [congeladas](../evidencias/c05/r5-candidata/candidate-freeze.json). O veto projeta abstenção no IPC e mantém a proposta original na auditoria; mede-se a candidata Luna com a política, sem atribuir o veto a um acerto do modelo puro. Perfil/executor B, revisão ampla, avaliação real e C06/C07 continuam pendentes. Zero novas chamadas ao fornecedor nessa preparação.

O executor encontrou falta de cobertura em quatro alvos claros de desenvolvimento na política 2.0.0, antes de qualquer inferência R5. A candidata foi reaberta por essa evidência pública de desenvolvimento, com autores novos sem acesso ao final, e passou à política 2.1.0. Os 33 testes e a revisão dirigida passaram, incluindo a disponibilidade de outra forma de pagamento. O [novo congelamento](../evidencias/c05/r5-candidata-v2/candidate-freeze.json) preserva o anterior e registra que B já acessara o pacote final, sem fornecer seus exemplos ou resultados aos autores da candidata. A qualidade real ainda não foi medida.

A preparação R5 A+B está integrada após revisão ampla aprovada em `a949f52`. O controle público e os selos verificam diário, envelopes, custos e vínculos nas duas etapas. A reprodução fixture percorreu 6+44 chamadas sintéticas, sem medir a Luna real. O integrador retoma o ensaio limitado dentro do teto global de US$ 10 e da estratégia escolhida, conforme o [registro operacional](../evidencias/c05/luna-r5-preflight-2026-11-25/autorizacao-continuacao.json). Essa interpretação não substitui as aprovações históricas apenas offline por falas novas do usuário. A conta foi conferida antes da etapa, com US$ 0,03093512 contabilizados e zero pendências. O final depende do gate e selo reais da própria candidata. Nenhuma chamada diagnóstica, repetição, orçamento recorrente ou inferência paga pública é habilitada.

### Resultado R5 real — 25/11/2026

O desenvolvimento passou em 8/8 alvos, com seis chamadas, p95 de 2.886,371 ms
e selo conferido. O final foi interrompido na tentativa 30 das até 44
planejadas: erro de transporte sem custo conciliável. Não houve repetição
ou envio das 14 restantes. O prefixo oficial permanece inconclusivo, com
1/26 conclusões em casos classificáveis, 0/4 urgentes reconhecidos após o
veto e p95 de 3.269,135 ms. A candidata Luna com política 2.1.0 não será
adotada. [Resultado e auditoria R5](../c05-luna-r5-resultado.md).

A auditoria separou o modelo do filtro. Das 33 propostas válidas, 30 foram
corretas; a Luna completou indevidamente os três campos ambíguos. O filtro
vetou 28 propostas corretas junto com as três indevidas. As quatro urgências
tinham propostas corretas, mas foram vetadas. Assim, nem manter o filtro
estreito nem simplesmente removê-lo resolve o aceite. O desenvolvimento
aprovado não demonstrou generalização para o conjunto maior.

Os 35 recibos R5 somam US$ 0,00992557. A tentativa sem custo informado
mantém reserva interna de US$ 1,239, sem cobrança confirmada. O total
conservador global é US$ 1,27986069 incluindo a reserva, com US$ 8,72013931
disponíveis sob o teto; não é saldo consultado na Feita. Nenhuma liquidação
fictícia ou nova conta foi criada. Novas chamadas estão suspensas.

C06/C07 continuam bloqueadas por qualificação e decisão de adoção. Outra
estratégia exige desenho e avaliação independente: não ajustar usando o
final consumido e reapresentá-lo como teste cego. Conciliar a tentativa
interrompida exige evidência real de cobrança, sem repetir a inferência.
A demonstração pública segue em fixture, e E01 permanece posterior/opcional.

### Piloto SetFit e pausa da classificação — 25/11/2026

O responsável autorizou testar SetFit em CPU e propôs adiar a categorização
para avançar nas frentes independentes. O C05-SF1 concluiu a avaliação
exploratória de categoria. A escolha e a calibração do classificador, a
integração e a validação do complemento real ficam em espera
até retomada explícita. O requisito de classificação real e seus critérios
de aceite continuam no plano de conclusão. C06 ainda requer qualificação
e decisão de adoção. C07/F09 final requer a integração e a reprodução do
trecho real em instalação limpa.

A demonstração com fixture tem prova de instalação limpa e passou no aceite
externo da F10 com atendente simulado. Na F10-A, o responsável confirmou por
dados móveis a conversa e o histórico na primeira URL e, após a reabertura
do túnel em 25/11, a chegada automática da resposta humana, a persistência
após recarga e o estado “Resolvido”. Na F10-B, confirmou por dados móveis
que Bia abriu Aurora e teve acesso negado a Horizonte, enquanto Cris abriu
o histórico do mesmo caso
Horizonte. A matriz pública passou em 36 de 36 verificações no computador de
origem. O fechamento completo ainda depende do complemento real.
[Aceite integrado F10](../f10-aceite-integrado.md) ·
[Piloto SetFit](classificacao-comparativa/setfit-piloto.md) ·
[Estado da entrega](../estado-entrega.md).

### Retomada SetFit SF2 — 25/11/2026

Após concluir o aceite externo da F10 em fixture, o responsável pediu retomar
a classificação, preparar a especificação SF2 e dividir o trabalho entre agentes.
Aprovou 360 relatos sintéticos novos: 150 para treino, 90 para validação da
regra de revisão e 120 finais independentes. A
[SF2](classificacao-comparativa/sf2/especificacao.md) e seu
[plano de tarefas](classificacao-comparativa/sf2/tarefas.md) explicitam os demais
parâmetros aprovados pelo responsável, que liberou a primeira onda 00/01/02.
Não tratam o piloto 15/16 como adoção,
não reutilizam os finais consumidos e não fazem chamadas pagas.

C05 está retomada em planejamento. C06 e C07/F09 final permanecem condicionadas
à qualificação completa, decisão de adoção e aceites próprios. A publicação
fixture continua aceita; E01 e a escala exploratória ficam fora desta rodada.

### Adoção SetFit R1 para C06 — 26/11/2026

O teste independente dos 120 casos e cinco controles passou nos dez critérios congelados e teve auditoria reproduzida byte a byte. A autorização para integrar após aprovação de todos os critérios passa a valer para o pacote e a política R1 registrados. C06 integra o complemento real ao Rails. C07/F09 final depende da C06 e comprova a instalação limpa. [Decisão de adoção](classificacao-comparativa/sf2/decisao-adocao-r1.md) · [Plano e aceites](classificacao-comparativa/c06-setfit-integracao.md).

### Aceite local do complemento real — 26/11/2026

A C06 comprovou o fluxo da aplicação com SetFit e mock via Kafka. A C07/F09 final reproduziu o pacote portátil em clone novo nas duas marcas e nos três canais, com revisão humana, handoff e persistência após reinício. A atualização HTTPS do modo SetFit tem verificação própria. [Aceite integrado C06](../evidencias/c06/aceite-integrado/README.md) · [Guia C07](../c07.md).

### Publicação SetFit e fechamento — 26/11/2026

Na revisão `977ec3f`, a revisão focal aprovou os cinco ajustes apontados
pelo parecer amplo. O integrador conservou os 15 casos e as 46 mensagens
anteriores ao atualizar a instalação. O aceite pelo HTTPS, WSS e navegador
passou com complemento real e mock via Kafka. O aceite móvel em fixture de
25/11 fica registrado na F10. A URL temporária depende do computador e do
túnel ativos. O modelo rodou localmente, sem chamadas pagas nesta etapa.
[Revisão final](../evidencias/c06/revisao-final/README.md) ·
[Aceite e operação da publicação](../c07-publicacao-setfit.md).

R01 e R02 passaram em reprodução independente. A matriz de referência F08
conserva a rodada reprovada e segue sem repetição após os ajustes. Os ensaios
de maior escala, incluindo dez mil conexões, seguem sem medição. Hospedagem
permanente fica fora do recorte. E01, o atendente conversacional real,
segue como evolução opcional.
[F08](../f08.md) · [Reprodução R01/R02](../evidencias/c07/README.md).
