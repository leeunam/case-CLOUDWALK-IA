# Interface do help desk

A caixa atende quem acompanha várias filas e precisa ler o histórico, verificar o responsável e responder ao cliente. Na supervisão, o mesmo caso dá acesso à origem da classificação, ao encaminhamento humano e à auditoria. O simulador usa os nomes de marca, canais e categorias entregues pelo repositório selecionado.

## Superfícies

| Superfície | Organização |
| --- | --- |
| Operação | Navegação verde à esquerda. O cabeçalho reúne a área selecionada e os controles disponíveis na sessão. A lista mantém filtros e paginação junto aos atendimentos. |
| Conversa | O histórico ocupa a área central. O compositor do analista responsável fica abaixo das mensagens, com rolagem própria quando o espaço vertical diminui. |
| Contexto | O resumo do encaminhamento precede as propriedades. As referências levam à mensagem no histórico. O registro do caso reúne identificador e datas. Correção, transferência e auditoria se abrem sob demanda. |
| Configuração | O supervisor escolhe a marca e uma área de edição. Alterações administrativas podem ser consultadas na auditoria da marca. |
| Simulador | Histórico e conversa dividem a mesma superfície. No primeiro envio, marca e canal precedem a classificação e a mensagem. O modo fixture aparece como “Dados locais”. |
| Login | Formulário de coluna única, com rótulos persistentes, preenchimento automático do navegador e mensagem de erro junto ao envio. |

## Cor e tipografia

| Token | Valor | Uso |
| --- | --- | --- |
| `--ink` | `#192f2a` | Texto principal e navegação |
| `--accent` | `#155c49` | Ação primária e links |
| `--tint` | `#e7f2eb` | Seleção, encaminhamento e mensagem de saída |
| `--paper` e `--canvas` | `#ffffff` e `#f5f7f4` | Área de trabalho e superfície de apoio |
| `--muted` | `#52665e` | Contexto, datas e texto secundário |
| `--line` e `--control` | `#d8e2db` e `#99ada2` | Divisórias e contornos de controles |
| `--warn` e `--warn-bg` | `#6f4b12` e `#fcf1d8` | Espera, bloqueio e perda de conexão |
| `--error` e `--error-bg` | `#8c322c` e `#fff0ed` | Falhas que exigem atenção |

A fonte é a sans-serif do sistema. O texto base mede 15 px na configuração padrão do navegador, os controles 14 px, os títulos de painel 18 px e o título do simulador 28 px. Todos usam unidades relativas ao tamanho de fonte do usuário. A navegação e os estados têm rótulos de texto. Os ícones usam traço uniforme e os controles que exibem apenas um ícone têm nome acessível.

## Largura e interação

- Acima de 77 rem, navegação, lista, conversa e contexto dividem a largura. Em 1024 px, “Ver contexto” alterna o conteúdo apresentado ao lado da lista.
- Até 58 rem, a navegação da operação vira um seletor no cabeçalho. Em 768 px, a lista e a conversa ainda podem ser lidas juntas.
- Até 44 rem, a operação alterna “Lista” e “Conversa”. O simulador alterna o formulário ou conversa e o histórico. Ocultar um painel mantém o rascunho do caso selecionado.
- O foco do teclado é visível e os controles usam elementos nativos. Uma referência do encaminhamento revela e foca a mensagem mesmo quando a conversa está oculta. O CSS respeita a preferência por movimento reduzido.
- As mensagens de carregamento, erro e confirmação acompanham a operação que as gerou. Uma falha de rede mantém disponíveis os mecanismos existentes de confirmação idempotente. Os dados da sessão alimentam a disponibilidade, os casos ativos e a carteira.

## Referências de organização

A separação entre lista, conversa e contexto segue a estrutura de uma caixa compartilhada. [Chatwoot](https://www.chatwoot.com/)

Os atributos do atendimento e os comandos de supervisão ficam próximos ao ticket. [Zammad](https://zammad.com/en)

A supervisão distingue falha e revisão com rótulos compactos e atalhos para os respectivos filtros. A referência visual foi a captura do painel Web apresentada no projeto. [Sidekiq](https://github.com/sidekiq/sidekiq)
