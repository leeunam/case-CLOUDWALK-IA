# F10-A · Preparação local da publicação temporária

- Base `ad1d1bd0160b26ca49e52c1076f49fdbcac4c257`.
- Branch `feat/publicacao-demo` e commit `7b30c4eb868a01d1b4d4d85a0b3e1126c51e6015`.
- Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/f10-publicacao`.
- Ambiente de prova `cloudwalk_publish_f10`. Portas exclusivas da frente em `127.0.0.1:18080` (HTTP da sonda/origem) e `127.0.0.1:18443` (HTTPS local para testar cookies e origens).
- Situação da F10-A. Código e ensaio local concluídos. O túnel público é a etapa seguinte do integrador.

## Entregas e interfaces

- `compose.publish.yml` é independente do Compose local. Inicializa PostgreSQL, Kafka e tópicos, Rails em production, worker, outbox, ponte de ida/volta, mock e web estático. Configura classificação em fixture e chaves vazias, três volumes nomeados do projeto e rede interna para os backends. A rede de borda conecta Caddy e cloudflared.
- `frontend/Dockerfile.production` compila com `npm ci` e copia `dist` para a imagem Caddy. `deploy/Caddyfile` serve fallback da SPA, cache de bundles e proxy da API, webhooks e WebSocket. O HTTP roteia a aplicação somente para o hostname configurado e fornece uma sonda na origem de loopback. O HTTPS em loopback usa uma CA local exportável como certificado público para cada teste, sem alteração da confiança do sistema.
- Rails preserva `force_ssl` e o cookie seguro. O modo de proxy assume HTTPS na rede privada e fixa o host e as origens permitidas. `CLOUDWALK_PUBLISH_DEMO_LOGIN=1` habilita o login com mapa de credenciais existente em production. O caminho de sessão, papéis e comparação segura continua compartilhado com development/test.
- `script/publish.py` oferece `init`, `credentials`, `up`, `check`, `status`, `logs`, `down`, `ca`, `prepare`, `publish` e `unpublish`. Gera segredos sintéticos uma vez em arquivo privado ignorado, valida os valores e isola a interpolação do Compose. `prepare` configura e baixa a imagem de túnel. `publish` é a ação explícita que inicia o perfil opcional e usa a origem HTTPS extraída dos logs privados. O endereço exige confirmar a resposta HTTPS antes de ser mostrado.
- `script/check_publish.py` testa o frontend e login via HTTPS local, cria um caso sintético assinado e acompanha a classificação e o handoff. A opção `--case-id` relê um caso existente após reinício. O guia `docs/f10.md` cobre operação, recuperação, atualização, cópia offline, restauração e exercício.

## Verificações executadas

| Verificação | Comando ou método | Resultado observado |
| --- | --- | --- |
| Imagens oficiais | `rtk docker buildx imagetools inspect caddy:2.11.9-alpine` e `rtk docker buildx imagetools inspect cloudflare/cloudflared:2026.11.2` | Digests de índice coincidem com as referências fixadas. |
| Provisionamento e isolamento | `rtk proxy python3 -B script/publish.py --project cloudwalk_publish_f10 init`, `up`, `status`, `prepare` e inspeção dos vínculos de portas | Arquivo ignorado `0600`. Serviços healthy/running, processos de migração/tópicos concluídos e apenas as portas Caddy publicadas em loopback. `prepare` baixou cloudflared oficial, validou o perfil e não o iniciou. O binário aceitou `tunnel --no-autoupdate --help` em contêiner com `--network none`. |
| Validação do operador | `rtk proxy python3 -B -m unittest discover -s script -p test_publish.py -v` | 5 testes aprovados. Permissão, preservação do arquivo, rejeição de configuração inválida, domínio permitido, saída de logs conflitante e perfil de túnel desativado no início local. |
| Regressão Rails | Preparação dos bancos de teste no contêiner API e `rtk docker exec -e RAILS_ENV=test -e CLOUDWALK_JEV_MODE=disabled -e CLOUDWALK_PUBLISH_DEMO_LOGIN= cloudwalk_publish_f10-api-1 bundle exec rails test` | 89 testes, 1.077 asserções, 0 falhas e 0 erros, 1 teste Jev real saltado. A primeira tentativa da suíte mostrou 15 erros por fixtures de teste ausentes no runtime production, que monta só o schema. Copiei `docs/contratos/fixtures` para o contêiner temporário e repeti com sucesso. O contêiner foi recriado depois. Os testes novos conferem a trava de production, valor de opt-in exato, configuração inválida/ausente/sem senha e a semântica de dev/test. |
| Produção local | `rtk proxy python3 -B script/check_publish.py --project cloudwalk_publish_f10` | SPA `/analista`, cache, separação das rotas da API/webhook, arquivo privado inacessível, login com Bia, JSON e credenciais inválidos recusados, CSRF ausente e origem incorreta recusados, cookie `Secure; HttpOnly; SameSite=Lax`, WebSocket `101` com origem autorizada e rejeição com outra origem. |
| Origem candidata | Ensaio local com `Stack.configure_web` para `https://f10-local-check.trycloudflare.com`, requisições somente a `127.0.0.1:18080` com `Host` fixo e leitura da configuração Rails em `rails runner` | Host candidato obteve SPA e API, cookie permaneceu seguro. Outro host e sufixo adulterado receberam `421`. ActionCable apresentou exatamente o HTTPS local e a origem HTTPS candidata. Ao voltar à configuração local, o candidato recebeu `421`. Nenhum DNS público ou túnel foi usado nesse teste. |
| Entrada assinada, Kafka e handoff | Smoke de production e leitura de `agent.requests` e `agent.events` com `kafka-console-consumer.sh --from-beginning --max-messages 1` no Kafka isolado | Caso `79d2bf37-bd80-4016-9d8d-9eeee247fe13`, correlação `2ca368bd-5950-4982-830d-b0b6dd423ee2`. Fixture classificou `terminal/advanced` e gerou pedido `bae1ce27-5061-4049-a129-79fc34d2e5ed`. Mock gerou `agent.handoff.proposed` `0e80f10d-3f3a-580b-baaa-b2729e6bc0d8` para o mesmo pedido. O Rails aplicou o retorno assinado e o worker levou o caso a `human_active`. |
| Persistência e recuperação | `rtk proxy python3 -B script/publish.py --project cloudwalk_publish_f10 down` e `up`, depois `rtk proxy python3 -B script/check_publish.py --project cloudwalk_publish_f10 --case-id 79d2bf37-bd80-4016-9d8d-9eeee247fe13` | Manteve o mesmo caso, estado `human_active`, relato do cliente e encaminhamento do mock. O evento original continuou disponível no tópico após reiniciar. `unpublish` em operação local preservou a pilha e o `down` final preserva seus volumes. |
| Higiene | `rtk git diff HEAD^ HEAD --check` e `rtk git status --short --branch` na worktree | Diff sem erros e worktree limpa. |

O primeiro bring-up acusou falha no handshake local porque clientes HTTPS com
o IP do loopback não enviam SNI. O `default_sni` do Caddy corrigiu o handshake
com verificação do certificado e do endereço. A confiança do sistema não foi
alterada. [Documentação Caddy](https://caddyserver.com/docs/caddyfile/options#default-sni)

## Reprodução e próximos aceites

Após integração com F09, use `script/publish.py init`, `up`, `check` e
`script/check_publish.py` no checkout final. A prova acima usa o
`integration/Dockerfile` da base atribuída, cuja pinagem Python está na frente
F09. `script/publish.py prepare` é a prova sem exposição.

A etapa pública requer `publish`, HTTPS e navegador em outra rede, login
sintético, verificação de WebSocket, fluxo de handoff e persistência da
instância da demonstração. O prazo de disponibilidade depende da operação do
computador local e a URL muda quando o túnel é recriado. A F10-A não executou
`publish`, uso de fornecedor de IA, ensaio de carga ou restauração do backup.
A cópia offline e a restauração foram documentadas. Os três volumes do projeto
de teste permanecem disponíveis para conferência. [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)

## Correção da revisão independente

- Base `7b30c4eb868a01d1b4d4d85a0b3e1126c51e6015`. Commit `7999b974d68c13d0211b9ea82167ee96530e86c1` na branch e worktree da F10-A.
- O guia explica como listar o `cloudflared` pelo nome exato do projeto e serviço, confirmar as etiquetas, validar outra vez o ID completo com os mesmos filtros e parar somente aquele contêiner via `docker stop`. A recuperação da configuração local usa o arquivo original com modo `0600` e `unpublish`.
- O guia usa `--project` em todos os exemplos, orienta a conferir o nome em contêineres e volumes e explica o vínculo entre checkout, nome, arquivo privado e volumes depois de `down`. A cópia offline usa o nome efetivo do projeto.

### Prova dirigida

1. Criei quatro contêineres descartáveis de `sleep` com `rtk proxy docker run --rm --detach --network none --label ... --entrypoint sleep postgres:17-alpine@sha256:a77aa70e641402a21411b92b721c58d10f23b50ae5fdd2333efd22d166e1e5f7 240`. Nenhum executou cloudflared. Dois foram alvos rotulados `cloudflared`, um foi controle `api` do projeto do primeiro alvo e um foi controle `cloudflared` de outro projeto.
2. Em diretório temporário, confirmei o arquivo ausente com `rtk proxy test ! -e .env.publish.local`. Consultei nome, ID e etiquetas com `rtk proxy docker ps --no-trunc --filter label=com.docker.compose.project=PROJETO --filter label=com.docker.compose.service=cloudflared --format ...`. A mesma consulta com `--filter id=ID_COMPLETO` retornou apenas o primeiro alvo. Com os IDs dos dois controles, retornou vazio. Apliquei `rtk proxy docker stop ID_COMPLETO` só ao alvo aceito. A execução inicial encadeada em um shell filho teve acesso negado ao socket Docker neste ambiente e foi refeita por chamadas diretas aos comandos documentados.
3. Criei um arquivo sintético vazio com `rtk proxy install -m 0644 /dev/null .env.publish.local` e confirmei o modo com `rtk proxy stat -c '%a' .env.publish.local`. Repeti as consultas com o projeto do segundo alvo e parei somente o ID aceito. `docker ps` mostrou os dois controles ainda ativos. Encerrei esses controles separadamente ao limpar o teste e confirmei a ausência de contêineres descartáveis restantes.
4. Executei `rtk proxy env PUBLISH_DB_PASSWORD=fixture … docker compose --env-file /dev/null --file compose.publish.yml --project-name PROJETO config --format json` com os nomes sintéticos `cloudwalk_publish_f10_round1_6n4_target` e `cloudwalk_publish_f10_round1_6n4_unsafe`. Os nomes dos três volumes foram disjuntos entre projetos. A consulta repetida com o primeiro projeto retornou os mesmos nomes. A composição foi só resolvida em texto com valores sintéticos.
5. Conferi a sintaxe dos dois trechos de emergência com `rtk proxy sh -n -c …` e o patch com `rtk git diff HEAD^ HEAD --check`. Worktree limpa. A revisão se limitou aos dois pontos operacionais.
