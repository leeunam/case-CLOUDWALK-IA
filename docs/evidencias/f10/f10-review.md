# F10-A · Revisão independente

- Base `ad1d1bd0160b26ca49e52c1076f49fdbcac4c257`.
- Revisão `7b30c4eb868a01d1b4d4d85a0b3e1126c51e6015`.
- Branch `feat/publicacao-demo`, worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/f10-publicacao`.

## SPEC

**Ajuste solicitado na parada da publicação.** A configuração e a prova local registradas cobrem o recorte técnico da F10-A. A parada documentada depende do arquivo de segredos mesmo quando o operador precisa somente interromper o túnel.

- O Compose independente usa Rails em `production`, inicializa banco e tópicos e roda worker, outbox, ponte e mock. As duas portas publicadas são do Caddy e estão vinculadas ao loopback. API, PostgreSQL, Kafka e ponte ficam na rede interna. O túnel compartilha a rede de borda com o Caddy. Os três volumes são nomeados por projeto e `down` preserva os dados.
- O frontend é compilado com `npm ci` e servido pelo Caddy oficial fixado por versão e digest. O fallback da SPA, as rotas de API, webhook e WebSocket e a política de cache estão separados. O contêiner web recebe o build e a configuração do Caddy. O mock usa os callbacks assinados existentes e o classificador roda em fixture com chaves dos fornecedores vazias.
- O Rails mantém `force_ssl`, cookie `Secure`, `HttpOnly` e `SameSite=Lax` e a verificação de CSRF. `assume_ssl` é habilitado no Compose privado para os proxies e retornos HTTP internos. O Caddy valida o host público e o Rails permite a origem HTTPS local e a origem pública extraída e validada. As consultas e os eventos WebSocket continuam sujeitos à revalidação e à visibilidade por sessão.
- Produção exige `CLOUDWALK_PUBLISH_DEMO_LOGIN=1` e senha privada não vazia. A comparação segura e o caminho de sessão e papéis permanecem compartilhados com desenvolvimento e teste. O wrapper exige configuração ignorada pelo Git e `0600`, preserva o arquivo existente e reserva a leitura das senhas para a ação explícita `credentials` em um terminal.
- `prepare` valida a composição do perfil opcional e prepara a imagem oficial fixada de cloudflared. O `publish` aplica host e origem obtidos dos logs e aguarda com TLS verificado. O perfil fica inativo no fluxo local normal e o serviço de túnel não tem política de reinício automático. A disponibilidade externa, login e WebSocket nas condições reais, handoff e persistência após reinício da instância pública são aceites do integrador.

## QUALITY

1. **P2 · Permitir a parada mesmo sem acesso ao arquivo privado.** Em `script/publish.py:223–244`, tanto `unpublish` quanto `down` abrem, bloqueiam e validam `.env.publish.local` antes de fazer qualquer chamada ao Docker. Com esse arquivo ausente ou com modo `0644`, ambos resultaram em status 1 e zero chamadas ao Docker. Se a configuração ficar indisponível durante uma publicação, o caminho de parada de `docs/f10.md:82–93` deixa o túnel ativo. Permita interromper o contêiner de cloudflared do projeto sem depender dos segredos, ou documente a parada direta de emergência com identificação pelo projeto e serviço. A restauração do ambiente local pode continuar usando o arquivo privado.
2. **P3 · Explicitar o vínculo entre checkout, arquivo privado e projeto.** Em `script/publish.py:200` e `docs/f10.md:16–33`, o padrão `cloudwalk_publish` é igual em todos os checkouts, enquanto o `init` gera segredos por checkout. Em duas pastas temporárias independentes, o `docker compose config` resolveu o mesmo projeto e os mesmos volumes `cloudwalk_publish_postgres_data`, `cloudwalk_publish_kafka_data` e `cloudwalk_publish_caddy_data`. Uma nova cópia com outro arquivo privado pode selecionar esses dados mesmo após `down` e encontrar a senha anterior do PostgreSQL. Oriente a usar um nome exclusivo ao preparar outra instância e a reutilizar o mesmo conjunto de projeto, volumes e arquivo privado ao retomar a original.

## Verificações desta revisão

- Confirmei branch, worktree limpa, commit e pai. Comparei a seção de patch do pacote com `git diff -U10 ad1d1bd..7b30c4e` e executei `git diff --check`. `git check-ignore -v` confirmou a regra dos arquivos privados.
- Usei arquivos exclusivamente sintéticos e Docker simulado para conferir os dois comandos de parada com arquivo ausente e com permissão inválida. Usei `docker compose config` em dois diretórios temporários para confirmar os nomes de projeto e volume. Nenhum contêiner foi iniciado por essas provas.
- O [relatório do executor](f10-report.md) registra a inspeção dos digests, cinco testes do wrapper, 89 testes Rails com zero falhas e um teste Jev real ignorado, HTTPS local com CA explícita, cookies e CSRF, WebSocket local, candidato de hostname em loopback, fluxo assinado até Kafka e handoff e confirmação de persistência depois de `down` e `up`. A revisão conferiu a configuração e os testes correspondentes e usou a evidência de execução registrada.
- A revisão não abriu túnel, usou rede pública, leu credenciais de trabalho, importou CA ou alterou código. A pinagem da imagem de integração entra pela F09. A restauração de backup foi documentada pelo executor e segue sem ensaio registrado.
