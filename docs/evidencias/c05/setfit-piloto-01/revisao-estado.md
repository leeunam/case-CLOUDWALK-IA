### Conformidade com a especificação — ajustes necessários

- ST1 · base `bf6322df792283e20cec5c12ef4dcc462bb5b846` · HEAD `3b45bd3a991c1bbe3e87bd8329727288fed27271` · branch `docs/entrega-sem-classificador` · worktree `.worktrees/standby-entrega`.
- Os quatro documentos pedidos receberam as alterações correspondentes. O resumo de entrega separa F09-A e F10 em fixture de C05/C06/C07 em espera e mantém os critérios futuros e o E01 opcional. `README.md:11`, `README.md:170`, `docs/estado-entrega.md:15`, `docs/estado-entrega.md:33`, `docs/estado-entrega.md:41`, `docs/planejamento/plano-de-execucao.md:137`, `docs/planejamento/conclusao-projeto.md:269`.
- A redação histórica em `docs/f10-resultado.md:59` deixa ambíguo se o teste móvel parcial cumpriu a etapa de verificação externa da F10. A cobertura descrita no novo estado está correta. A correção deve manter a prova histórica e explicitar o alcance da checagem junto ao próprio registro.

### Evidências verificadas

- F01–F07 e F09-A têm respaldo nos relatos de integração e instalação limpa. Conferi essas fontes para avaliar o risco de ampliar o alcance do aceite local. `docs/estado-entrega.md:13`, `docs/planejamento/plano-de-execucao.md:5`, `docs/planejamento/plano-de-execucao.md:24`, `docs/f09.md:134`.
- O resumo preserva a reprovação histórica F08, a ausência de nova matriz após as correções e o caráter exploratório dos cenários adicionais, incluindo dez mil conexões. Os relatos de R01 e R02 sustentam os aceites independentes. `docs/estado-entrega.md:14`, `docs/estado-entrega.md:26`, `docs/f08.md:84`, `docs/r01.md:107`, `docs/r02.md:39`.
- O recibo publicado da renovação coincide com o fornecido pelo integrador, conforme comparação de arquivos. A última URL está associada à sonda HTTPS de saúde, e a conversa de dois turnos pertence à URL da UX02. O reinício e a restauração pertencem ao histórico da primeira publicação. `README.md:57`, `docs/f10-resultado.md:5`, `docs/f10-resultado.md:15`, `docs/f10-resultado.md:38`, `docs/evidencias/f10/integrator-f10-renewal-2026-11-25.json:15`, `docs/planejamento/plano-de-execucao.md:260`.
- A disponibilidade atual da URL e o fluxo completo a partir de outra rede ficam pendentes de verificação operacional. O gate usou leitura do diff e das fontes pontuais, sem chamadas externas ou reexecução de suítes. `docs/estado-entrega.md:18`, `docs/evidencias/f10/integrator-f10-renewal-2026-11-25.json:27`.

### Achados

**Importante — `docs/f10-resultado.md:59`.** Conferi a passagem histórica fora do diff por risco de conflito com o status novo do aceite. Depois de descrever a exibição de marcas e canais por dados móveis, a frase “atendendo à verificação por outra rede” pode ser lida como aceite da etapa que exige conversa, handoff e isolamento. A nota nova em `docs/f10-resultado.md:8` e o plano em `docs/planejamento/plano-de-execucao.md:271` mantêm essa etapa pendente. Registre que o teste externo da primeira URL cobriu a abertura da página e a exibição de marcas e canais. Mantenha explícitas as verificações externas remanescentes.

**Menor — `docs/ux02.md:7`.** Conferi o destino do link de aceite acrescentado em `docs/estado-entrega.md:16` devido ao risco de conduzir o leitor ao endereço anterior como se fosse o atual. A descrição em tempo presente ainda aponta para a URL cujo túnel deixou de ser encontrado. Registre essa URL como a da publicação histórica da UX02 e remeta ao resultado F10 para o endereço mais recente.

### Qualidade da tarefa — ajustes necessários

O estado de entrega está sustentado pelas fontes e a renovação está bem delimitada. O registro F10 precisa explicitar a cobertura do teste móvel para que o status de aceite externo seja inequívoco.

### Revisão do ajuste — conformidade aprovada

- ST1 · base `3b45bd3a991c1bbe3e87bd8329727288fed27271` · HEAD `7bb244694a464c573dec85dbeef701e5cd236488` · branch `docs/entrega-sem-classificador` · worktree `.worktrees/standby-entrega`.
- **Importante — ADDRESSED.** O registro mantém o fato observado na primeira URL por dados móveis e especifica que conversa, handoff e isolamento por marca seguem pendentes em outra rede. `docs/f10-resultado.md:58`.
- **Menor — ADDRESSED.** O registro associa a URL histórica à publicação da UX02 e encaminha o leitor ao endereço mais recente registrado na F10. O cabeçalho de destino consta nas verificações relatadas. `docs/ux02.md:7`, `docs/f10-resultado.md:3`.
- O diff do ajuste se limita aos dois trechos acima. A revisão não identificou regressões. As verificações do implementador foram consultadas e não foram reexecutadas.

### Qualidade da tarefa após o ajuste — aprovada

O texto mantém a distinção entre o alcance da verificação móvel, o requisito de aceite externo e o histórico dos endereços da publicação.

### ST1-E — conformidade aprovada

- Base `7bb244694a464c573dec85dbeef701e5cd236488` · HEAD `06b77abd04221c37425edabdb6c94e1e1280c882` · branch `docs/entrega-sem-classificador` · worktree `.worktrees/standby-entrega`.
- Comparei as falas e o alcance registrado no diff com `f10-mobile-page.json`. A confirmação inicial “foi” e o esclarecimento “Apenas abri a página” constam no recibo. O texto atribui ao responsável apenas a abertura da página na URL nova e registra conversa, histórico após recarregar, handoff, acesso do analista e isolamento em outra rede como pendentes. O resultado da sonda HTTPS e o teste móvel histórico permanecem vinculados aos respectivos registros. `docs/evidencias/f10/integrator-f10-mobile-2026-11-25.json:7`, `docs/f10-resultado.md:5`, `docs/f10-resultado.md:12`, `docs/estado-entrega.md:23`.
- O resumo do piloto coincide com o resultado e a revisão SF1 registrados. Foram 15/16 decisões, 12/12 casos classificáveis e 3/4 revisões, com `jev-013` previsto como `terminal`. O p95 de inferência local por texto foi 21,078 ms com n=16. A amostra é sintética e de desenvolvimento. Prioridade, calibração, qualificação final e C05/C06/C07 permanecem pendentes. A demonstração segue em fixture. `docs/estado-entrega.md:34`, `docs/estado-entrega.md:42`, `docs/estado-entrega.md:46`, `sf1-review.md:16`.

### ST1-E — qualidade aprovada

- **Menor — `docs/estado-entrega.md:40`.** O link leva ao plano do piloto. Depois de juntar as frentes, um link para `docs/c05-setfit-piloto.md` permitirá chegar da síntese ao relatório que contém as métricas e os artefatos. O plano é um destino válido e a ausência desse segundo link não bloqueia a entrega.
- A revisão usou o diff, o registro original da abertura da página e a revisão SF1. As checagens de cópia, links e métricas relatadas pelo implementador foram consultadas, sem reexecutar cálculos, chamadas externas ou inferência.
