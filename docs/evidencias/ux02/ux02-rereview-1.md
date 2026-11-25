# UX02 — revisão do primeiro ajuste

Faixa `56a6672..540f975`, branch `feat/estilo-cloudwalk`, worktree
`.worktrees/ux02-cloudwalk`. Revisão estática limitada ao patch.

## SPEC

**Aprovado com ressalva menor.** Os quatro ajustes cumprem o aceite no tema
padrão. A ressalva sobre cores forçadas está registrada em QUALITY.

- **ADDRESSED · Seleção no tema padrão.** A faixa de 3 px marca a área ativa
  a 11,49:1 em `frontend/src/staff/staff.css:8` e a aba ativa a 12,66:1 em
  `frontend/src/configuration/configuration.css:10`.
- **ADDRESSED · Hover das listas.** `frontend/src/style.css:125` aplica
  `#202020` sobre o canvas `#111111` aos itens sem seleção. O seletor exclui o
  item atual e preserva seu fundo, contorno e visto. O efeito em tela fica para
  as recapturas do integrador.
- **ADDRESSED · Barra de rolagem.** Em `frontend/src/style.css:51`, o indicador
  `#737373` sobre a trilha `#111111` atinge 3,98:1.
- **ADDRESSED · Licença.** O diff da OFL contém apenas a remoção do espaço final.
  `git diff --check 1adc941..540f975` passou e o SHA-256 da fonte segue igual.

## QUALITY

**Aprovado com ressalvas menores.** Os três achados P3 abaixo ficam para
triagem na revisão ampla.

O relatório de execução foi movido com 100% de similaridade e tem link válido
em `docs/ux02.md`. O frontmatter YAML e o sidecar JSON são legíveis, os 24
tokens de cor correspondem ao CSS e as referências dos sete componentes se
resolvem. O escopo segue restrito a CSS, documentação e espaço na licença.

- **P3 · Seleção em cores forçadas.** Em `frontend/src/staff/staff.css:8` e
  `frontend/src/configuration/configuration.css:10`, o navegador suprime a faixa
  de `box-shadow` quando o sistema ativa cores forçadas. O usuário perde o novo
  indicador de posição. Uma borda com `ButtonText` em um pseudoelemento ou um
  fallback sob `@media (forced-colors: active)` cobre esse modo.
- **P3 · Tokens de componente divergentes.** `DESIGN.md:69` prescreve raio
  de `0.45rem` para o botão secundário e `DESIGN.md:81` usa `--ink` no texto da
  navegação ativa. O produto usa `0.65rem` e `#fff`, respectivamente. A amostra
  da navegação em `.impeccable/design.json:44` também usa peso 600, enquanto
  `staff.css:6` usa 550. A amostra de etiqueta na linha 60 usa peso 600 em vez
  do 650 de `style.css:118`. Alinhar o documento e as amostras aos estilos reais.
- **P3 · Amostra da seleção ausente.** Em `.impeccable/design.json:51`, a
  amostra `list-item-selected` nasce sem `aria-current`. O painel renderiza o
  estado normal e o CSS da amostra também omite o visto presente na aplicação.
  Incluir um item atual com o visto torna a seleção demonstrável.

O relatório do commit registra 34 testes aprovados e build aprovado. Esta
revisão conferiu o diff, os contrastes calculados, a fonte e a documentação.
As evidências de navegador ficam com o integrador.
