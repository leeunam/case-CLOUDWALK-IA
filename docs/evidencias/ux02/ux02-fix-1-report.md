# Relatório do fix 1 — UX02

- Tarefa: UX02 — primeira rodada consolidada de correções visuais e documentação.
- Commit-base: `56a6672054ae93e36246a75b88c87dfcf0979597`.
- Branch: `feat/estilo-cloudwalk`.
- Worktree: `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/ux02-cloudwalk`.
- Commit: `540f975` (`fix: destacar estados do tema escuro`).

## Correções

- Navegação ativa e aba ativa de configuração receberam uma faixa clara interna
  de 3 px. Os contrastes são 11,49:1 sobre o fundo ativo da navegação e 12,66:1
  sobre o fundo ativo das abas.
- O hover de um item não selecionado agora usa `--surface-raised`, diferente do
  canvas da lista; o item selecionado mantém fundo, borda e visto.
- A barra de rolagem usa `--control` sobre `--canvas`, com contraste calculado
  de 3,98:1.
- Removi apenas o espaço final acidental no texto da OFL, sem alterar termos ou
  o arquivo binário da fonte.
- `DESIGN.md` agora tem frontmatter YAML de tokens e as seções canônicas. O
  sidecar `.impeccable/design.json` registra somente tokens e componentes já
  usados. O relatório inicial foi movido sem alteração para
  `docs/evidencias/ux02/ux02-report.md`.

## Verificações

Executadas na raiz da worktree:

```sh
rtk proxy docker build -t cloudwalk-ux02-web:accept frontend
rtk proxy docker run --rm --network none cloudwalk-ux02-web:accept npm test
rtk proxy docker run --rm --network none cloudwalk-ux02-web:accept npm run build
rtk git diff --check 1adc941..HEAD
```

- A imagem usa `node:22-alpine` pelo digest fixado no Dockerfile.
- Suíte frontend: 34 testes passaram, sem falhas ou omissões.
- Build: `tsc --noEmit` e Vite passaram.
- `git diff --check` desde a base UX02 passou, incluindo a remoção do espaço
  final na licença.
- Frontmatter YAML passou na leitura por Ruby/Psych e o sidecar passou em
  `python3 -m json.tool`.
- O diff do fix contém CSS e documentação; não contém TS/TSX, JavaScript de
  comportamento, dependências, backend ou contratos.
- A fonte binária permaneceu inalterada. Sua origem e hash continuam registrados
  em `frontend/public/fonts/SOURCE.md`.

## Limites

O navegador e a prévia compartilhada não foram abertos. A captura inicial já foi
aprovada pelo integrador; recapturas após este commit, incluindo desktop e
mobile, ficam com ele. A pasta `.impeccable/review/` continha uma imagem de
revisão preexistente e permaneceu fora do commit.
