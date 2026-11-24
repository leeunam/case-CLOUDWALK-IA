# Revisão integrada da aplicação F09/F10

24/11/2026 · `main` · checkout principal `/home/inteli/Documents/projetos/case-CLOUDWALK-IA` · base `53c60a844006b47a97276e3f6b560d8920bb9c93` · revisão `b056b120a4d4878ad398248c6207e44b653b683e`.

## SPEC

A preparação da aplicação atende ao corte de preview com classificação fixture. F09 e F10 usam a mesma implementação de ponte, o mesmo contrato de eventos e o mesmo callback assinado. As imagens de F10 para pedidos, eventos e mock são construídas com o Dockerfile integrado da F09, que fixa Python por digest, instala os 20 pacotes com versões exatas e executa `pip check`. Os tópicos, o destino dos pedidos, a URL de retorno e os pares de segredos usados nas duas pontas correspondem.

F10 mantém banco, Kafka, Rails e ponte na rede interna. Apenas Caddy publica portas de loopback. O túnel depende do perfil explícito, recebe só a rede de borda e encaminha para o Caddy. A aplicação React usa caminhos de mesma origem e seleciona WSS para HTTPS. A validação do domínio, o host configurado no proxy, o opt-in de login e a lista explícita de origens no Rails são compatíveis. O login reaproveita as sessões, a autorização e o CSRF existentes. O encerramento normal preserva volumes, e a parada de emergência seleciona o contêiner por projeto, serviço e ID completo.

A verificação por URL de outra rede continua com o integrador. O aceite final C06/C07 depende do classificador real e da decisão de adoção previstos no planejamento.

## QUALITY

Solicito uma correção operacional no roteiro de recuperação. O P2 afeta a confiança no backup antes de atualizar a instalação. O caminho de aplicação revisado pode seguir para os testes públicos após a revisão dirigida da correção.

- **P2 · Uma restauração incompleta pode terminar como bem-sucedida.** Em `docs/f10.md:157–163` e `174–183`, o shell prossegue quando a cópia privada ou uma operação de arquivamento ou extração falha. Uma falha no PostgreSQL pode deixar um volume vazio, após o que `up` prepara um banco novo. O `check` em `script/publish.py:139–146` valida serviços e consulta de saúde. Um banco recém-inicializado também satisfaz esse teste. Em shell isolado, injetei retorno 17 exclusivamente na extração PostgreSQL do trecho literal de restauração. Os passos seguintes chegaram a `up` e `check` e o trecho retornou zero. Ações solicitadas: fazer a cópia e a restauração interromperem ao primeiro erro, verificar que os três volumes de origem já existem no projeto e validar no destino um ID de atendimento anotado antes do backup. O verificador com `--case-id` já existe. Prova dirigida esperada: falha simulada impede iniciar o destino e devolve erro; na restauração válida a mesma conversa pode ser relida no projeto novo.
- **P3 · Os comandos de F10 dependem de um programa omitido dos pré-requisitos.** Em `docs/f10.md:16–17` o operador encontra Docker, BuildKit e Python, mas até o primeiro comando em `docs/f10.md:30` invoca `rtk`. Em um host só com os requisitos listados a sequência interrompe já na inspeção inicial. Documentar o equivalente direto de `rtk proxy COMANDO` e `rtk docker` para o operador que não usa RTK resolve também os exemplos de restauração e parada de emergência.

## Evidências e limites

- Comparei o patch do pacote com `git diff -U10 53c60a8 b056b12`. O conteúdo coincide byte a byte. `git diff --check 53c60a8 b056b12` passou. A exclusão anterior do PDF segue no checkout.
- Conferi os manifestos, wrappers, configuração Rails/Caddy, login, rotas do navegador, sessões, verificador de produção e guias no commit integrado. A única execução funcional nesta revisão foi o teste de falha do shell, com substitutos locais para os comandos, sem contêineres ou volumes.
- As evidências existentes da F09 incluem a pilha limpa e o fluxo HTTP dos três canais, duas marcas, replay, entrega humana e persistência. O integrador registrou quatro mensagens e o mesmo caso após recarregar o navegador. Os relatórios da F10 registram produção HTTPS local com CA explícita, CSRF, cookies seguros, upgrade WebSocket, rejeição de origem indevida, entrada assinada com handoff e releitura após reinício. A rodada autoral de F10 precede a integração do pin Python de F09.
- Não executei suítes, carga, restauração real nem publicação nesta revisão. O teste externo com login, WebSocket, handoff e persistência e o exercício de recuperação em novos volumes continuam pendentes. Não houve acesso a arquivo de credenciais, conta financeira ou fornecedor de IA. A avaliação R3/Luna permanece em sua própria frente.
