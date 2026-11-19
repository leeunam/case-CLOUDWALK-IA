# Rodada paralela · conclusão F04 e conexão F05

Preparação do integrador em 2026-11-19 sobre a base de código `6036fec`.
Este documento fixa as responsabilidades e os contratos da próxima rodada.
As extensões de catálogo e WebSocket descritas aqui foram entregues na rodada.
O aceite integrado e suas limitações estão em [integração F04/F05](../integracao-f04-f05.md).

## Responsabilidade por frente

| Frente | Responsabilidade nesta rodada |
| --- | --- |
| F04 + suporte backend F05 | Única dona do Rails, migrations/schema, jobs, endpoints, Action Cable, contratos compartilhados, configuração de execução e testes backend. Concluir a classificação e fornecer o backend que o simulador e a caixa precisam. |
| F05 React | Única dona de `frontend/`, incluindo cliente HTTP/WebSocket, tipos, cópia local de fixtures e testes/build. Conectar simulador, login, caixa e conversa às APIs. |
| Integrador | Revisar commits e evidências, integrar as frentes e verificar os dois fluxos completos. Mudanças fora dos limites acima retornam a este chat. |

Retomar os chats e ambientes existentes da mesma tarefa, conforme AGENTS.md.
Buscar a nova base no repositório principal e atualizar a branch por fast-forward
somente com estado local limpo e preservando as alterações alheias. Não continuar
da base antiga da primeira entrega. Se o fast-forward não for possível, relatar
a divergência com commits concretos, sem descartar trabalho ou reescrever histórico.

F05 pode começar pelas APIs de sessão e atendimento já implementadas. O adaptador
do simulador pode ser desenvolvido contra os contratos abaixo enquanto F04 fornece
os endpoints. O aceite final da F05 exige integração real após unir as frentes.

## REST e nomes de marca

O OpenAPI v1, os schemas e as fixtures atuais continuam sendo a referência,
com esta extensão coordenada: `Channel` passa a conter `brand_name` obrigatório,
uma string não vazia obtida de `channel.brand.name` no backend.

- F04 atualiza o schema Channel, o exemplo `channel-list.json` e a documentação
  de contrato, e implementa `GET /api/v1/channels` com o escopo da sessão.
- F05 atualiza seus tipos/fixtures e deriva a lista de marcas distintas a partir
  de `(brand_id, brand_name)` desses canais, mantendo paginação quando houver.
- Não usar a listagem administrativa `GET /api/v1/brands` para o simulador nem
  fixar nomes de marca no cliente da API real. Um canal não autorizado também
  não deve expor o nome da sua marca.

Backend a fornecer nesta rodada, além das APIs humanas já presentes:

- `POST /api/v1/simulator/session` e o catálogo de canais autorizado.
- `GET /api/v1/simulator/cases`, detalhe e mensagens do próprio cliente.
- `POST /api/v1/simulator/channels/{channel_id}/messages`, passando pelo mesmo
  serviço canônico de entrada dos webhooks, com reentrega e identidade sob
  controle do servidor. O navegador não assina webhooks com segredo.
- Correção de classificação por supervisor em
  `POST /api/v1/cases/{id}/classification`, conforme contrato existente.

Preservar cookies, CSRF, recibos, paginação e os formatos de erro previstos.
A identidade do simulador tem escopo próprio de conversas; não deriva permissão
de IDs de cliente/conversa escolhidos pelo navegador. Sessões e audiências de
simulador e equipe operacional devem permanecer separadas nas verificações.

## Avisos de atualização · Action Cable

Contrato fixado para ambas as frentes:

- Endpoint WebSocket na mesma origem: `/cable`.
- Canal: `CaseUpdatesChannel`.
- Parâmetros de assinatura: `{ channel: "CaseUpdatesChannel", case_id: UUID,
  audience: "simulator" | "staff" }`.
- Mensagem de aplicação: `{ type: "case.updated", case_id: UUID }`.
  Os envelopes de controle são os do protocolo Action Cable.

`audience` seleciona qual identidade da sessão deve ser verificada; nunca concede
um papel ou acesso por si só. `simulator` pode acompanhar somente conversa própria;
`staff` exige visibilidade vigente do caso para analista/supervisor. O backend
autentica a conexão, autoriza a assinatura e revalida o acesso antes de transmitir
cada aviso. Revogação, logout e encerramento de sessão não podem manter acesso.
Não emitir um stream global de marcas/casos para os navegadores.

Os avisos só saem após commit e funcionam tanto para mudanças da API quanto dos
workers. O adapter PostgreSQL configurado no projeto deve comunicar os processos.
O aviso contém apenas o identificador: o cliente consulta a API autorizada para
obter dados. F04 registra os dois formatos em schemas/fixtures/documentação
compartilhada; F05 implementa exatamente esses campos.

Na confirmação da assinatura, após reconectar e após um aviso, F05 consulta o
estado atual. Isso cobre eventos ocorridos entre o recibo REST e a assinatura.
Consultas periódicas podem servir de recuperação/fallback e atualizar a caixa;
o chat deve também receber avisos reais pelo WebSocket, sem depender apenas delas.

## Conclusão da F04

- Usar o adaptador integrado, com modo fixture reproduzível e modo HTTP explícito.
  Campos válidos seguem ao atendente sem chamar Jev. Somente ausentes geram perguntas;
  entrada inválida vai para revisão sem inferência.
- Executar complemento em Solid Queue depois da persistência; guardar tentativas,
  motivos, evidências e versão da classificação. A chamada HTTP não deve manter
  bloqueios do atendimento durante a espera de rede.
- Aplicar resultado sob transação/revalidação de estado e versão. Correção humana
  invalida resultado pendente; reentrega não duplica classificação ou rodada.
- Respeitar prazo/tentativas da especificação e `Retry-After`, com agendamento
  persistido, recuperação de pendências e revisão após falha definitiva.
- Correção autorizada exige motivo, versão esperada, idempotência e auditoria;
  preserva histórico e dispara o encaminhamento uma vez quando elegível.
- Preservar contratos/invariantes de F02/F03 e validar as restrições do catálogo
  do adaptador, inclusive a opção de abstenção reservada.
- Chamada real com dado sintético exige `TYPESAFE_API_KEY`. Se faltar credencial,
  entregar o código e evidências locais com o aceite real explicitamente pendente.

## Aceite conjunto e entrega

F04 verifica Rails no runtime fixado, concorrência/correção tardia, retentativas,
CSRF, idempotência, isolamento REST/WebSocket e notificação entre processos.
F05 verifica instalação do lockfile, testes pertinentes, build e navegador:
três canais/duas marcas, login operacional, handoff com contexto, resposta humana,
espera/retomada/resolução, recarga/reconexão e conflitos de versão.

As fixtures permanecem úteis em testes e modo de demonstração explícito; o caminho
da API real não pode cair silenciosamente em respostas locais quando o servidor
falhar. Cada frente informa commit-base, branch, diretório, commits, comandos e
resultados reais, falhas e pendências. Mudanças de contrato além das acima são
coordenadas com o integrador antes de o outro agente consumi-las.

## Ajuste da integração · audiência do catálogo

A revisão central aprovou `GET /api/v1/channels?audience=simulator`.
Essa indicação exige a identidade sintética vigente e responde `401` quando
ela não existe, mesmo se houver identidade operacional no mesmo navegador.
O simulador envia esse parâmetro em todas as páginas. Isso elimina a corrida
em que a expiração sintética entre leituras faria o catálogo usar o escopo staff.
A consulta sem esse parâmetro preserva o comportamento operacional anterior.
O OpenAPI e o contrato de acesso registram a extensão.
