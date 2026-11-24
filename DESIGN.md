# Interface do help desk

A caixa reúne navegação por perfil, lista de atendimentos, conversa e contexto.
A supervisão mantém configuração e auditoria. O simulador apresenta histórico,
classificação e conversa em um fluxo compacto. A adaptação UX02 troca apenas
estilo visual; os fluxos e estados da UX01 permanecem.

## Direção visual

O tema escuro é inspirado nas superfícies neutras do site da CloudWalk, sem
logotipo nem indicação de afiliação. O ícone original de três barras e o nome
Help desk permanecem. As cores semânticas de espera, falha e sucesso ficam
restritas aos estados operacionais, sempre acompanhadas de rótulos.

| Token | Valor | Uso |
| --- | --- | --- |
| `--canvas` / `--paper` | `#111111` / `#181818` | Fundo da aplicação e superfícies de trabalho |
| `--surface-raised` / `--navigation` | `#202020` / `#0b0b0b` | Campos, apoio e navegação |
| `--ink` / `--muted` | `#ecebe9` / `#b9b7b4` | Texto principal e secundário |
| `--accent` / `--button-ink` | `#f0efed` / `#111111` | Links, ícones e ação primária clara |
| `--tint` / `--selection-border` | `#292929` / `#797979` | Seleção, destaque e contorno selecionado |
| `--line` / `--control` | `#363636` / `#737373` | Divisórias e contornos de campos |
| `--warn` / `--warn-bg` | `#f1c976` / `#332b1b` | Espera e revisão |
| `--error` / `--error-bg` | `#ffaaa0` / `#351f1d` | Falhas que exigem atenção |
| `--success` / `--success-bg` | `#a8dbb7` / `#1b2c23` | Atendimento ativo |

A tipografia usa Gabarito variável, peso 400 no corpo e pesos 500/600 em títulos
e controles. Gabarito é uma aproximação geométrica gratuita; não é Cera Pro e
não reproduz com exatidão a fonte computada no site de referência. O arquivo e
a licença OFL estão em `frontend/public/fonts/`; `docs/ux02.md` registra origem
e hash. A fonte é servida localmente com `font-display: swap`.

## Superfícies e interação

| Superfície | Organização |
| --- | --- |
| Operação | Navegação grafite, lista, conversa e contexto em superfícies escuras. |
| Conversa | Mensagens recebidas em grafite e enviadas em cinza neutro mais claro. |
| Configuração | Campos nativos escuros; abas e seleção usam cinzas da paleta. |
| Simulador | Histórico e conversa preservam o layout da UX01 com a paleta compartilhada. |
| Login | Formulário compacto em painel escuro e ação clara arredondada. |

O foco é claro e visível, campos têm contorno contrastante, checkbox e radio
seguem o tema escuro nativo do navegador e a seleção textual usa cinza claro.
As dimensões, a navegação responsiva e os comportamentos documentados em
[UX01](docs/ux01.md) permanecem.

## Organização responsiva preservada

- Acima de 77 rem, navegação, lista, conversa e contexto dividem a largura.
  Abaixo desse limite, “Ver contexto” alterna a conversa e o contexto.
- Até 58 rem, a navegação da operação vira um seletor no cabeçalho.
- Até 44 rem, a operação alterna “Lista” e “Conversa”; no simulador, a navegação
  alterna formulário/conversa e histórico.
- O foco do teclado é visível. Referências ao encaminhamento revelam e focam a
  mensagem no histórico, inclusive quando a conversa está oculta.
- As superfícies e estados existentes conservam os rótulos. Os tokens de espera,
  falha e sucesso mudam apenas sua apresentação cromática.
