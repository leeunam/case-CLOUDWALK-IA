---
name: Interface do help desk
description: Caixa de atendimento com tema escuro neutro e estados operacionais legíveis.
colors:
  canvas: "#111111"
  paper: "#181818"
  surface-raised: "#202020"
  navigation: "#0b0b0b"
  navigation-selected: "#303030"
  ink: "#ecebe9"
  muted: "#b9b7b4"
  accent: "#f0efed"
  accent-hover: "#ffffff"
  button-ink: "#111111"
  tint: "#292929"
  selection-border: "#797979"
  selection-bg: "#4a4a4a"
  line: "#363636"
  control: "#737373"
  focus: "#f0efed"
  neutral-bg: "#252525"
  neutral-text: "#d0cfcd"
  warn-bg: "#332b1b"
  warn: "#f1c976"
  error-bg: "#351f1d"
  error: "#ffaaa0"
  success-bg: "#1b2c23"
  success: "#a8dbb7"
typography:
  body:
    fontFamily: "Gabarito, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.48
    letterSpacing: "normal"
  heading:
    fontFamily: "Gabarito, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.16
    letterSpacing: "-0.035em"
  control:
    fontFamily: "Gabarito, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "normal"
rounded:
  sm: "0.45rem"
  xs: "0.3rem"
  panel: "0.75rem"
  pill: "999px"
spacing:
  sm: "0.5rem"
  md: "1rem"
  lg: "1.25rem"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.button-ink}"
    typography: "{typography.control}"
    rounded: "{rounded.pill}"
    padding: "0.45rem 0.8rem"
    height: "2.3rem"
  button-secondary:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.sm}"
    padding: "0.45rem 0.8rem"
    height: "2.3rem"
  field:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "0.55rem 0.7rem"
    height: "2.5rem"
  navigation-active:
    backgroundColor: "{colors.navigation-selected}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.sm}"
  list-item-selected:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
  status-neutral:
    backgroundColor: "{colors.neutral-bg}"
    textColor: "{colors.neutral-text}"
    rounded: "{rounded.xs}"
    padding: "0.16rem 0.44rem"
  panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
---

# Interface do help desk

## Overview

A caixa reúne navegação por perfil, lista de atendimentos, conversa e contexto.
A supervisão mantém configuração e auditoria; o simulador apresenta histórico,
classificação e conversa. UX02 altera o tema visual e preserva os fluxos e
estados existentes.

O tema escuro é inspirado nas superfícies neutras do site da CloudWalk. O produto
mantém o nome Help desk e o ícone abstrato de três barras, sem logotipo nem
indicação de afiliação.

## Colors

O canvas e a navegação são quase pretos; os painéis e campos usam níveis
próximos de grafite. Texto principal e secundário permanecem claros. A ação
primária é clara com texto escuro. A seleção, o hover e os contornos usam
marcadores de cinza distintos. Espera, falha e sucesso usam cores semânticas
discretas e continuam acompanhados por rótulos.

## Typography

Gabarito variável é usada localmente, em peso 400 para o corpo e 500/600 para
títulos e controles. É uma aproximação geométrica gratuita, não Cera Pro e não
uma correspondência tipográfica exata da referência. A família servida pelo
site de referência requer licença web que não está disponível neste projeto.
Origem, licença OFL e SHA-256 constam em `frontend/public/fonts/SOURCE.md`.

## Layout

- Acima de 77 rem, navegação, lista, conversa e contexto dividem a largura.
  Abaixo desse limite, “Ver contexto” alterna conversa e contexto.
- Até 58 rem, a navegação da operação vira um seletor no cabeçalho.
- Até 44 rem, a operação alterna “Lista” e “Conversa”; no simulador, navegação
  alterna formulário/conversa e histórico.
- Campos e controles nativos seguem o esquema escuro do navegador. O foco do
  teclado é claro; uma referência do encaminhamento revela e foca a mensagem.

## Elevation & Depth

As superfícies se distinguem por cor e divisórias discretas. Painéis não usam
sombras decorativas. A barra de rolagem usa o contorno de controle como thumb
para preservar sua leitura em relação à trilha escura.

## Shapes

Campos e botões secundários têm cantos discretamente arredondados. Painéis usam
raio um pouco mais amplo. A ação primária usa forma de pílula; estados compactos
mantêm cantos menores.

## Components

- **Ação primária.** Fundo claro, texto escuro e forma de pílula; hover aumenta
  levemente o brilho.
- **Ação secundária.** Campo grafite com contorno de controle e texto claro.
- **Campo.** Fundo grafite levantado, texto claro e contorno visível; radio e
  checkbox usam a cor de ação.
- **Navegação ativa.** Fundo grafite selecionado e faixa clara interna na borda
  esquerda, sem alterar a largura do item.
- **Item de lista.** Hover usa a superfície elevada; seleção preserva fundo,
  contorno e visto próprio.
- **Estado.** Espera, falha, sucesso e estado neutro mantêm rótulos textuais.
- **Painel.** Fundo de superfície, divisória discreta e cantos arredondados.

## Do's and Don'ts

- Mantenha as superfícies escuras e a hierarquia por tons neutros.
- Preserve indicadores visíveis de foco e seleção; use marcadores claros junto
  do fundo para que os estados não dependam apenas da cor.
- Use rótulos com cores semânticas de espera, falha e sucesso.
- Não adicione o logotipo CloudWalk, o nome da marca ao produto ou alegação de
  afiliação.
- Não substitua Gabarito por fonte proprietária sem licença válida.
- Não introduza gradientes, hero de marketing, imagens ou animações decorativas.

As dimensões, a navegação responsiva e os comportamentos da UX01 permanecem;
consulte [UX01](docs/ux01.md) e [UX02](docs/ux02.md).
