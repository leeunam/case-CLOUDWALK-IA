# UX01 · Entrega para revisão

| Item | Evidência |
| --- | --- |
| Base | `3e59f4ad80536b5586e91c89a2ea157bebbcb442` |
| Branch | `feat/interface-operacional` |
| Diretório | `.worktrees/ux01-interface` |
| Commit | `e0e2a0d01f6e5c7ff826a9f74fa2ed77c58ec842` |
| Prévia fixture | [Simulador privado](http://127.0.0.1:45189/?fixture=demo), HTTP 200 na entrega |
| Reprodução | `docs/ux01.md` |
| Sistema visual | `DESIGN.md` |

A caixa possui navegação por perfil, seis filtros, lista paginada, compositor e contexto do caso com origem da classificação, encaminhamento e referências. Em telas menores, lista e contexto mudam de painel sem desmontar a conversa. As ações do supervisor apresentam o resultado no mesmo contexto em que o comando foi iniciado. A correção e a transferência montam o formulário no primeiro acesso. O simulador mantém a identificação do modo local e as três opções de canal provenientes do catálogo. Login e configuração seguem o mesmo conjunto visual.

A revisão de código conferiu foco das referências ao alternar o contexto, ações com efeito incerto junto ao supervisor e correspondência entre as áreas permitidas e o seletor móvel do analista. Os componentes novos concentram navegação, controles da operação, filtros, lista, contexto, login e aviso de conectividade. O diff contém frontend, dois testes de navegação e documentação.

## Verificações executadas

- `npm ci --offline --no-audit --no-fund` no host encontrou cache incompleto. `npm ci --no-audit --no-fund` com acesso autorizado instalou as 23 dependências de `frontend/package-lock.json`. O lockfile permaneceu íntegro.
- O primeiro `npm test` local encontrou o Node da distribuição compilado sem suporte a TypeScript, com erro `ERR_NO_TYPESCRIPT`. O build local passou.
- `docker build -t cloudwalk-ux01-web:accept frontend` construiu a imagem a partir do Dockerfile do projeto. A camada que executa `npm ci` estava em cache. Foram usados o digest Node 22 Alpine e o lockfile do repositório.
- `docker run --rm --network none cloudwalk-ux01-web:accept npm test` passou com 29 testes, zero falhas e zero ignorados. Os dois testes novos percorrem mudança de área, escopo por perfil e manutenção de marca, fila e classificação.
- `docker run --rm --network none cloudwalk-ux01-web:accept npm run build` passou com TypeScript e Vite 8.3.8, processando 57 módulos.
- `git diff --cached --check` passou antes do commit. A worktree voltou ao estado limpo depois do commit.

## Aceite pelo integrador

A prévia em 45189 atende a fixture e não aponta para a API pública. O integrador confirmou no navegador o simulador em desktop e 390 × 844 px. No móvel, verificou ausência de rolagem horizontal e preservação do rascunho de WhatsApp ao alternar histórico e conversa. A inspeção da caixa autenticada nos tamanhos do brief e os fluxos de handoff, configuração e supervisão na pilha isolada seguem com o integrador. Sugestão de exercício com rascunho e referência em `docs/ux01.md`.
