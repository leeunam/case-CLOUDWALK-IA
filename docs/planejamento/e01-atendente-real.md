# E01 — atendente real com conhecimento por marca

## Estado e autorização

Iniciada em 26/11/2026, sobre a main publicada
`343d073caa447d467209977ae5d464329658d128`.
Branch `feat/atendente-real`, worktree `.worktrees/e01-atendente`.
Esta primeira etapa registra o desenho; ainda não implementa nem qualifica o atendente.

O responsável aprovou GPT-5.6 Luna pela Feita, conhecimento fictício por marca
e teto **acumulado de US$ 1 para o piloto E01**. A autorização cobre o piloto;
não libera consumo contínuo na URL pública. Não renovar automaticamente esse
orçamento ao reiniciar, trocar de processo ou refazer um ensaio.

O MVP permanece concluído com SetFit real e atendente simulado. A E01 não
reabre a seleção ou o teste final do classificador. O mock permanece disponível.
[Estado do MVP](../estado-entrega.md) ·
[Card E01](https://github.com/leeunam/case-CLOUDWALK-IA/issues/11).

**Confirmado:** provedor, modelo, conhecimento fictício e teto do piloto,
além do fluxo geral aprovado na conversa: uma chamada por turno, propostas
validadas pelo Rails e resposta salva antes da publicação.
**Proposto nesta etapa:** ontologia leve, formato da base, interfaces internas,
regras detalhadas de resposta e matriz do piloto. A pergunta sobre ontologia
foi apresentada ao responsável; não há decisão de adotar RDF/OWL ou banco de grafos.

## Objetivo observável

Um cliente envia uma solicitação sintética por um dos três canais. Após a
classificação válida, a Luna recebe histórico e orientações da marca,
responde de forma útil, mantém a continuidade e encaminha ao humano quando
necessário. A resposta aparece no histórico existente. O atendente não
consulta contas reais nem executa pagamentos, estornos ou alterações bancárias.

## Ontologia proposta: um mapa de conceitos e relações

O vocabulário operacional já existe em [CONTEXT.md](../../CONTEXT.md).
Marca e categoria serão reutilizadas; prioridade continua significando
urgência/impacto e não vira complexidade ou procedimento.

| Conceito | Significado | Relação principal |
| --- | --- | --- |
| Assunto | Tema tratado, associado a `pix`, `payouts` ou `terminal`. | Associa-se à categoria operacional. |
| Intenção | O que o cliente quer fazer ou esclarecer. | Pertence a um assunto e tem termos equivalentes. |
| Condição de aplicação | Fato necessário para uma orientação ser aplicável. | Restringe um procedimento; fato ausente exige pergunta. |
| Procedimento | Orientação com passos e limites explícitos. | Atende uma intenção e tem fonte e escopo de marca. |
| Regra de encaminhamento | Circunstância que exige atendimento humano. | Interrompe a orientação e registra um motivo. |
| Fonte de conhecimento | Registro que fundamenta a orientação. | Identifica conteúdo, marca, versão, vigência e caráter fictício. |

Exemplo fictício: `Aurora → terminal → não consegue ligar → verificar
condições de alimentação → selecionar procedimento aplicável`. Os termos
“maquininha”, “terminal” e “máquina de cartão” podem recuperar o mesmo assunto.
Um visor apagado, sozinho, não comprova falta de energia ou defeito. Sem a
condição necessária, o atendente pergunta; sem procedimento aplicável,
encaminha. Orientação da Horizonte não pode fundamentar uma resposta da Aurora.

### Onde cada parte ficará

- **Vocabulário humano:** `CONTEXT.md`, apenas definições de domínio, após
  consolidar os termos. Esta especificação registra as relações e o alcance.
- **Dados utilizados pelo produto:** proposta de
  `integration/knowledge/ontology.json` para conceitos e relações, e
  `integration/knowledge/brands/{aurora,horizonte}.json` para orientações
  fictícias, vinculadas aos IDs das marcas do seed.
- **Busca:** módulo do atendente na integração Python. Primeiro restringe a
  marca autorizada, depois procura por categoria, termos equivalentes e
  condições. A Luna recebe somente os candidatos da marca daquela solicitação.
- **Auditoria:** execução persistida no PostgreSQL, com IDs/versões das fontes
  selecionadas, modelo, versão da instrução, uso e resultado. Evitar cópia
  desnecessária do histórico e nunca registrar credenciais.

JSON versionado permite revisar conteúdo e relações sem adicionar um serviço.
PostgreSQL para editar a base pela interface seria uma evolução, com API e
auditoria próprias. RDF/OWL permitiria semântica formal/interoperabilidade,
mas requer uma necessidade específica para justificar essa etapa. Este JSON
não será apresentado como implementação compatível com SKOS ou OWL.
[Referência de organização de conceitos](https://www.w3.org/TR/skos-primer/).

A ontologia organiza o conhecimento. A autorização por marca é aplicada em
código; referências válidas não provam, sozinhas, que uma resposta é correta.

## Integração proposta

O fluxo atual é preservado:

    Rails + outbox → agent.requests → atendente Python → Feita/Luna
                                                   → agent.events → Rails

O pedido já inclui marca, classificação, rodada, geração e histórico ordenado.
O consumidor aceita pedidos 1.0 e 1.1. As respostas usam as propostas
`agent.reply.proposed`, `agent.handoff.proposed` e `agent.resolve.proposed`
do contrato existente. O modelo não define IDs de marca, caso ou rodada.

1. Selecionar um backend explícito, `mock` ou `luna`, no serviço de atendente.
   Os Compose de demonstração e publicação já possuem esse serviço e as pontes.
   O piloto usa projeto e volumes próprios. Não colocar mock e Luna em grupos
   diferentes consumindo os mesmos pedidos, nem misturá-los no mesmo grupo.
2. Recuperar conhecimento da marca, construir contexto limitado e pedir saída
   estruturada. O modelo propõe uma ação e indica fontes; o executor valida
   formato, referências, condições e limites antes de montar `AgentResult`.
3. Manter no Rails a autoridade sobre estados, permissões, geração, referências
   do handoff e descarte de respostas atrasadas. A E01 não reclassifica o caso.
4. Preservar o mock sem chave e sem rede para testes. A opção Luna é explícita
   e não altera a publicação existente nesta preparação.

## Execução durável e custo

O Rails será o dono da persistência e das reservas no PostgreSQL. Proposta:
um registro de execução por `request_event_id`, com unicidade no banco e
operações internas autenticadas para claim, início e conclusão. A integração
Python não recebe acesso SQL direto. O contrato dessas operações precisa
ser fixado antes de dividir a implementação entre agentes.

Fluxo esperado: `reserved → started → result_saved → published`.
Falha após possível despacho sem confirmação termina em `unknown`.
Snapshot de modelo, tarifas, versões do conhecimento e política acompanha
a execução. Resultado salvo é imutável e tem ID estável derivado do pedido.

- Reservar custo em USD com aritmética decimal e bloqueio transacional antes
  do despacho. Custo conciliado mais reservas pendentes não pode exceder US$ 1.
- Fazer somente um despacho ao provedor por pedido. A política atual de três
  tentativas gerais do consumidor não pode repetir a inferência paga.
- Salvar proposta e uso antes de publicar. Se a publicação falhar, repetir
  os mesmos bytes salvos, sem chamar a Luna novamente.
- Timeout ou encerramento após possível envio conserva a reserva e impede
  repetição automática. Não prometer cobrança exatamente uma vez: isso depende
  de idempotência do fornecedor, ainda não comprovada.
- Conciliar e liberar excedente somente com evidência de custo utilizável.
  Sem conciliação, manter a reserva e interromper novos despachos do piloto.
- Usar uma inferência em voo por vez no piloto. Reinício preserva orçamento
  e execução. Worker antigo não pode concluir execução já invalidada.

Persistir `started`, token de posse e expiração antes do POST ao fornecedor.
Se um processo morrer ou perder a posse nesse estado, a recuperação do Rails
detecta a expiração e faz uma transição condicional para `unknown`, retendo
a reserva. Não existe retomada automática da inferência nessa situação.
Se a rodada ainda estiver vigente, registrar falha de integração recuperável
pela supervisão; caso já tenha mudado, apenas auditar a ocorrência. Conclusão
tardia com token antigo ou execução terminal não pode salvar nem publicar
uma nova proposta. O aceite de 02 deve simular esse crash e verificar estado
terminal, reserva preservada e zero segundo POST após reinício/reentrega.

A consulta pública da Feita em 26/11 informou Luna
`openai/gpt-5.6-luna`, entrada US$ 0,20/Mtoken, saída US$ 1,20/Mtoken e
leitura de cache US$ 0,02/Mtoken. São referências a reconfirmar no pré-voo,
não preços eternos. A reserva não depende de desconto de cache.
[Modelo e tarifa pública](https://feita.ai/models/openai/gpt-5.6-luna).

O pré-voo deve fixar limites faturáveis comprováveis e uma reserva
conservadora. Um limite local de tamanho do texto, sozinho, não comprova
o total de tokens cobráveis. A primeira chamada real só ocorre depois dos
testes sem rede e da revisão do controle financeiro. O teto de US$ 1 já
está autorizado; não pedir essa autorização novamente.

## Comportamento a validar

- Responder com base nos procedimentos aplicáveis da marca e no histórico.
- Perguntar pelo dado que falta; não tratar hipótese como fato observado.
- Encaminhar por pedido explícito de humano, ausência de orientação aplicável
  ou regra documentada. Resumo deve referenciar mensagens reais do caso.
- Propor resolução somente após confirmação explícita do cliente. Duas
  mensagens ou o fim de uma resposta não significam resolução.
- Registrar falha técnica/orçamento e permitir recuperação pela operação;
  não substituir silenciosamente uma falha da Luna por resposta do mock.
- Tratar instruções do cliente como conteúdo do atendimento, sem permitir
  que alterem a política, a marca ou as permissões do executor.

Os prazos internos precisam caber na validade atual da rodada (60 segundos
após publicação confirmada do pedido). A medição será fim a fim: entrada do
cliente até resposta persistida. A meta de três segundos do classificador
não é automaticamente uma meta para o atendente conversacional.

## Etapas e entregáveis verificáveis

| Etapa | Entrega | Dependência e verificação |
| --- | --- | --- |
| E01-00 | Esta especificação, relações de conhecimento e contrato interno de execução/orçamento. | Reutilizar tipos e rotas atuais; separar confirmação de proposta; revisar ambiguidades antes dos consumidores. |
| E01-01 | Base fictícia validada e busca por marca. | Após escolha da representação. Testar sinônimos, condição ausente, fonte inválida e isolamento antes de qualquer chamada paga. |
| E01-02 | Ledger Rails, reserva e execução idempotente. | Após contrato 00. PostgreSQL real: disputa pelo mesmo pedido e pelo último saldo; reinício e reserva ambígua. |
| E01-03 | Backend Luna e mock selecionáveis, transporte e saída estruturada. | Após contrato 00; pode avançar em paralelo a 02 com cliente de ledger simulado. Nenhuma chamada paga nos testes. |
| E01-04 | Integração Kafka e recuperação em projeto isolado. | Após 01–03. Reentrega, falha de publicação, resultado atrasado e perda de associação sem novo despacho ao modelo. |
| E01-05 | Piloto real limitado e avaliação das conversas. | Após aceite offline e pré-voo financeiro; uso total <= US$ 1. Publicar resultados por cenário, custo e tempo, inclusive falhas. |
| E01-06 | Aceite da interface, documentação de operação e revisão final. | Após piloto aprovado. Dois canais assíncronos e chat, duas marcas, histórico, handoff e resolução. Decidir separadamente habilitação pública e limite contínuo. |

O piloto começa com uma conversa curta e só amplia se contrato, procedência,
uso e reserva puderem ser conferidos. O tamanho da matriz será fixado em 00
antes das chamadas; conversa de piloto não equivale a estimativa de qualidade
em produção. Casos e expectativas não podem ser ajustados para aprovar
respostas já observadas. Não haverá LLM avaliando a si mesma como único aceite.

## O que permanece fora desta evolução

Dados reais, operações financeiras, integrações reais de WhatsApp/e-mail,
edição da ontologia pela supervisão e motor formal de inferência não fazem
parte do piloto aprovado. Publicação permanente, nova matriz F08 e dez mil
conexões seguem evoluções separadas, sem capacidade presumida.

