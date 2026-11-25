# Revisão da UX02

Base `1adc94127f3c66dcdc145117eda733781650cd46`, HEAD `56a6672`, branch
`feat/estilo-cloudwalk`, worktree `.worktrees/ux02-cloudwalk`.

## SPEC

**Ajustes necessários.** O tema escuro cobre login, operação, configuração e
simulador por regras compartilhadas e locais. O diff contém CSS, fonte, licença e
documentação. Os arquivos de comportamento, contratos e dependências permanecem
iguais à base. Os componentes mantêm a estrutura e a identidade Help desk. O CSS
usa os tons indicados no brief, define o esquema de cor escuro para controles
nativos e mantém o visto nas listas e os botões de opção dos canais. Gabarito é carregada
localmente com `font-display: swap`. A licença OFL 1.1, a origem e a limitação
tipográfica constam na entrega. O SHA-256 local confere com `SOURCE.md` e o
arquivo é identificado como Gabarito variável, com cobertura para português.

- **P2 · Seleção de seção pouco distinguível.** Em `frontend/src/staff/staff.css:8`,
  selecionar uma área na navegação de desktop só troca cores. O fundo ativo
  `#303030` fica a 1,49:1 da navegação `#0b0b0b`. Em
  `frontend/src/configuration/configuration.css:10`, o fundo ativo `#292929`
  fica a 1,22:1 do painel `#181818`. A forma muda discretamente por herança de
  `.primary`, sem um indicador a 3:1. Adicionar um marcador ou contorno ao
  estado ativo mantém layout e atributos acessíveis.
- **P2 · Hover invisível nas listas.** Em `frontend/src/style.css:126`, passar
  o cursor sobre um item sem seleção troca o fundo para `--canvas`. A lista
  da operação e o histórico do simulador já usam esse mesmo fundo em
  `frontend/src/staff/staff.css:32` e `frontend/src/simulator/simulator.css:8`.
  Trocar o fundo de hover para `--surface-raised` restaura o feedback e mantém
  a precedência do estilo de seleção.

## QUALITY

**Ajustes necessários.** Os pares da tabela de contraste de `docs/ux02.md`
foram recalculados e conferem. O placeholder existente usa `--muted` sobre
`--surface-raised` com contraste de 8,14:1. Os 34 testes e a compilação no Node
fixado constam como aprovados no relatório de execução.

- **P3 · Contraste da barra de rolagem.** Em `frontend/src/style.css:25` e `:52`,
  o indicador `#555555` tem 2,53:1 sobre a trilha `#111111` quando a barra
  estilizada é exibida. Usar `--control` como cor do indicador eleva o contraste
  para 3,98:1.
- **P3 · Espaço no fim de linha na licença.** `rtk proxy git diff --check
  1adc941..56a6672` acusa `frontend/public/fonts/OFL-Gabarito.txt:21`.
  Remover o espaço preserva o conteúdo da licença e limpa a checagem do diff.
  O comando sem faixa do relatório de execução não verifica mudanças commitadas.

A revisão foi estática. Capturas, carregamento da fonte em execução, focos e
menus nativos, dimensões em 390 e 1440 px e aparência após os ajustes ficam com
o integrador. Os testes e a compilação relatados não foram repetidos nesta revisão.
