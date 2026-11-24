# F09-A · Relatório da demonstração local

- Base `53c60a844006b47a97276e3f6b560d8920bb9c93`.
- Branch `feat/demo-reproduzivel`, em `.worktrees/f09-demo`.
- Commit `973fe469dccbf4e1991dae198bdee820dd3c3e4a`.
- Verificação em 24/11/2026, Linux amd64, Docker Engine 29.3.0, Docker Compose 5.1.0.
- Projeto de aceite `cloudwalk_demo_f09b`, encerrado com os dois volumes preservados.

## Implementação

`compose.demo.yml` complementa o Compose de desenvolvimento com o outbox, o
mock e as duas direções da ponte, reaproveitando scripts, contratos e callback
assinado. A rede interna concentra Kafka, PostgreSQL e integração. Uma segunda
rede do mesmo projeto habilita somente as portas de API e Vite em loopback.
O classificador padrão é fixture e pode ser desabilitado explicitamente.
O worker recusa outros modos, e o React usa a API pelo proxy de mesma origem.

`script/demo.py` oferece `init`, `config`, `up`, `status`, `logs`, `down`,
`check` e `login`. As credenciais sintéticas são geradas em `.env.demo.local`
com modo `0600`, instalação atômica e preservação do arquivo existente.
A configuração é validada silenciosamente. O teste `check` cria um caso
pelo verificador canônico de F02 e consulta o broker. O login é exibido por
comando explícito, sem imprimir a configuração do Compose.

A imagem Python 3.13.18 Trixie foi fixada no digest oficial
`sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90`.
O SDK Kafka e o JSON Schema conservaram os pins existentes e os 18 pacotes
transitivos que estavam na imagem da integração R01 foram registrados.
O Docker instalou 20 pacotes com `pip install --no-cache-dir -r requirements.txt`
e retornou `No broken requirements found.` no `pip check`.
[Imagem oficial Python](https://hub.docker.com/_/python)

## Verificações executadas

| Comando ou cenário | Saída observada |
| --- | --- |
| `docker buildx imagetools inspect docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90` | Índice OCI oficial, digest correspondente ao pin e manifesto linux/amd64 com Python 3.13.18-slim-trixie. |
| `python3 -B script/demo.py --project cloudwalk_demo_f09b up` | Volumes Kafka/PostgreSQL criados. Preparações de banco e Kafka saíram com código 0; nove serviços ativos. |
| `docker compose --env-file .env.demo.local -f compose.yml -f compose.demo.yml -p cloudwalk_demo_f09b config --quiet` | Código 0 e saída vazia. Testes auxiliares confirmaram onze serviços, isolamento das duas redes, porta loopback, portas alternativas, descarte de variáveis externas e execução fora da raiz. |
| Geração e recuperação das credenciais via módulo e `login` | 12 inicializações concorrentes em diretório temporário deixaram um arquivo de modo 0600. Nova inicialização preservou todos os bytes. Modo 0644 foi rejeitado. Login retornou a credencial solicitada. Logs amostrados de setup, ponte, mock, outbox, worker, API e verificador livres dos segredos gerados. |
| Saúde e entrada do frontend | `curl` retornou `{"status":"ok","database":"ok"}` no Rails em 43109 e pelo Vite em 45179. `/` e `/analista` retornaram HTTP 200. |
| `python3 -B script/demo.py --project cloudwalk_demo_f09b check` | Dois pedidos e dois resultados correlacionados em Kafka, mesmo recibo para entrada repetida, conflito para bytes diferentes na mesma chave, quatro mensagens em ordem e callbacks assinados repetidos com `duplicate`. Atendimento resolvido. |
| Roteiro complementar por HTTP via Vite | A sessão do simulador recebeu seis canais (dois por tipo). Chat Aurora completou dois turnos, com bypass e reentrega sem duplicar. E-mail Horizonte complementou somente a categoria no fixture, preservando prioridade recebida, e confirmou abstenção e correção com motivo auditado. WhatsApp Aurora encaminhou o histórico ao responsável, registrou resposta humana, espera, retomada com o mesmo responsável e resolução. |
| `demo.py down` e nova subida por Docker direto com `DEMO_CLASSIFIER_MODE=disabled` | Mesmo caso WhatsApp resolvido com cinco mensagens idênticas e auditoria preservada. Entrada incompleta foi para revisão com `classifier_disabled`, e uma completa recebeu resposta pelo Kafka. |
| `bundle exec ruby /workspace/script/check_contracts.rb` dentro do Rails | OpenAPI, JSON Schema e 47 fixtures verificados, com uma inválida esperada. |
| `python -B -m unittest discover -s /workspace/integration` em contêiner da imagem nova, contratos e fontes somente leitura | 20 testes aprovados. |
| `npm test` e `npm run build` dentro do frontend | 27 testes aprovados, zero falhas, e compilação TypeScript/Vite bem-sucedida. |
| `git diff --cached --check` e `git status --short --branch` | Diff sem erros de espaços e worktree limpa após o commit. |

O caso canônico `406cc641-2ac8-4531-bb05-d68910a9c4ca` usou a correlação
`87a853e5-b23f-4292-a095-29394e6a4a5c`. O primeiro par de eventos no Kafka
foi pedido `3f3653e2-5957-4b74-8671-ad1f7539e37d` e resultado
`0d1a063c-bf32-5863-abeb-b4764b4ede41`. O caso WhatsApp que sobreviveu à
recriação dos contêineres foi `5d408bc0-dbd4-4e55-bfce-6886ed19c0b7`,
correlação `db30c6ae-b156-4a89-a8b1-8788fac9aa92`.

## Limites e reprodução

A primeira tentativa de subida com rede exclusivamente interna bloqueou as
portas no host apesar de os serviços iniciarem. O complemento foi corrigido
e revalidado com volumes novos no projeto `cloudwalk_demo_f09b`. A primeira
montagem usada para os testes Python divergia do caminho esperado das
fixtures. A repetição preservou no contêiner a estrutura de diretórios do
repositório e aprovou todos os 20 testes. Os acessos Python a loopback e ao
daemon precisaram de permissão gerenciada nesta sessão.

Os fluxos foram verificados pelas rotas HTTP de cliente e operação no proxy do
frontend. A sequência manual no navegador está documentada em `docs/f09.md`.
O roteiro anterior de navegador está em `docs/integracao-f04-f05.md`. Esta
rodada não repetiu a matriz F08, chamadas pagas, C06, C07 ou publicação F10.
O resultado histórico F08 continua em cinco de seis, com correções R01 e R02
verificadas nos seus relatórios. Os contêineres dos dois projetos de teste
foram encerrados preservando seus volumes.

Para reproduzir, rode `python3 script/demo.py up` e `python3 script/demo.py check`.
Anote o `correlation_id`, siga os pares pedido/resultado no Kafka mostrados pelo
check e compare com o campo de mesmo nome na resposta de auditoria do mesmo
caso. O exercício completo, o acesso local e os passos de classificação,
handoff e reinício estão em `docs/f09.md`.

## Revisão dirigida · Docker direto e volumes por checkout

Correção sobre `973fe469dccbf4e1991dae198bdee820dd3c3e4a`, commit
`aa3911e5d8d25c288b6a92920583c7c531c75939` na mesma branch e worktree.
O README e o roteiro orientam a reservar um nome de projeto distinto por
checkout ou worktree, inclusive após `down`. Para retomar a demo, mantenha
o checkout, o arquivo privado e o nome que seleciona os volumes. A função
Docker direto recebe esse nome, limpa as variáveis conflitantes num subshell
e mantém as três opções de portas e modo.

| Verificação dirigida | Resultado |
| --- | --- |
| `rtk proxy python3 -B /tmp/cloudwalk-f09-fix-1.py` | Extraiu a função do Markdown e a executou em Bash e Zsh. Com marcadores exportados, `demo_compose cloudwalk_demo config --quiet` e a configuração personalizada com portas 43110/45180 e modo `disabled` saíram com código 0 e sem saída. |
| Comparação em memória de `config --format json` | Nos dois shells, o modelo completo do Docker direto coincidiu com o do wrapper nas duas configurações. O PostgreSQL recebeu o valor do arquivo privado e a API manteve Aurora e Horizonte. Nenhuma credencial foi exibida. |
| Configuração estática em dois checkouts temporários | O mesmo nome de projeto calculou os mesmos nomes de volume nos dois diretórios. Com nomes distintos, os conjuntos de volumes ficaram disjuntos. Destinos locais do README, do roteiro e a âncora do guia conferidos. |
| `rtk git diff --cached --check` e `rtk git status --short --branch` | Diff sem erros e worktree limpa após o commit. |

A revisão foi documental e usou Compose 5.1.0 sem subir serviços ou repetir
as suítes da implementação.
