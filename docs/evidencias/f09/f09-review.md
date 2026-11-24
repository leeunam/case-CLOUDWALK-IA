# F09-A · Revisão independente

- Base `53c60a844006b47a97276e3f6b560d8920bb9c93`.
- Revisão `973fe469dccbf4e1991dae198bdee820dd3c3e4a`.
- Branch `feat/demo-reproduzivel`, worktree `.worktrees/f09-demo`.

## SPEC

**Ajuste solicitado no caminho Docker direto.** A configuração usa o arquivo
privado como fonte exclusiva de credenciais pelo wrapper. A alternativa
documentada pode priorizar valores exportados no terminal sobre esse arquivo.

- O diff está dentro do escopo da F09-A. O Compose complementar reutiliza
  a base de desenvolvimento, os contratos de evento, a assinatura das duas
  direções, o outbox e o verificador canônico de F02. O padrão do simulador
  abre a API real. O worker aceita fixture e desabilitado, com a chave HTTP
  vazia. O bypass de classificação completa permanece no serviço existente.
- A configuração tem onze serviços, PostgreSQL e Kafka com volumes nomeados,
  rede interna de integração e somente API e Vite publicados em loopback.
  O wrapper chama `down` sem remover volumes. A geração usa arquivo temporário
  privado e instalação por link exclusivo. `git check-ignore -v` confirmou
  que o arquivo de credenciais e seus temporários são ignorados.
- O [relatório de execução](f09-report.md) registra instalação com volumes
  vazios, dois turnos e reentrega, três canais e duas marcas, revisão auditada,
  handoff, espera, retomada, resolução e persistência após nova subida.
  Essas evidências vieram do executor. O roteiro de navegador foi cruzado com
  os rótulos da interface, as condições da fixture e a rota de auditoria.
  A execução F09 registrada usou HTTP pelo proxy do Vite.
- A imagem da integração inclui o digest e o Dockerfile roda `pip check`.
  Os dois pins diretos foram preservados e os 18 transitivos têm versão
  exata. O roteiro registra a fonte oficial e o comando de consulta do
  manifesto. A inspeção de registry, o build e os testes da integração
  constam no relatório de execução.
- README e roteiro cobrem instalação, login explícito, modos de
  classificação, testes e exercício com `correlation_id`. O resumo mantém a
  F08 histórica em cinco de seis, aponta as correções R01/R02 e apresenta
  C06, C07 e publicação como etapas pendentes.

## QUALITY

1. **P2 · Preservar a origem das credenciais no Docker direto.**
   `docs/f09.md:95–105` descreve os mesmos arquivos e projeto do wrapper.
   O Compose dá prioridade ao ambiente do terminal sobre `--env-file`.
   Com `DEMO_POSTGRES_PASSWORD` e `CLOUDWALK_SIMULATOR_BRANDS` exportados,
   a via direta usou os dois valores exportados. Na mesma prova, o wrapper
   usou a credencial do arquivo e as duas marcas do seed. Alternar entre as
   duas entradas pode trocar a credencial dos serviços diante de um
   PostgreSQL já inicializado, ou mudar o catálogo visível. A função
   documentada deve limpar as variáveis conflitantes ou explicar a precedência
   e instruir como deixar o terminal livre delas. Preserve as três opções
   suportadas para portas e modo de classificação.
2. **P3 · Documentar o isolamento entre checkouts mesmo com a demo parada.**
   `docs/f09.md:38–53` cria credenciais por checkout e recomenda outro
   projeto quando já existe uma demo em execução. O nome padrão em
   `script/demo.py:136` também seleciona os volumes de uma demo encerrada
   vinda de outro checkout no mesmo daemon. Em dois diretórios temporários
   independentes, o Compose calculou os mesmos nomes
   `cloudwalk_demo_kafka_data` e `cloudwalk_demo_postgres_data` para o
   projeto padrão. Vincule na orientação cada conjunto de dados ao mesmo
   checkout, arquivo de credenciais e nome de projeto. Ao alternar entre
   checkouts, use nomes distintos mesmo após `down`.

## Verificações desta revisão

- Conferi o commit e seu pai, os seis caminhos alterados e o pacote de diff.
  `git diff --check 53c60a8..973fe46` passou e a worktree estava limpa.
- Usei Compose 5.1.0 em configuração estática, sem daemon, com arquivos
  temporários e valores sintéticos. A validação silenciosa retornou código
  zero e saída vazia. Comparei a precedência da via direta e do wrapper
  sem imprimir valores. Confirmei os nomes renderizados dos volumes em
  dois diretórios diferentes.
- Conferi a existência dos 19 destinos de arquivos locais do README e dos
  sete do roteiro, os 20 pins Python e as rotas usadas no roteiro e no
  verificador. Os testes de execução do relatório original foram
  consultados sem repetir a subida, a matriz de carga ou as suítes.
