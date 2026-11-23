# Ajuste técnico de proveniência encontrado na C02

Em 23 de novembro de 2026, a revisão da C02 em `3bb2742` identificou que
o contrato 1.0.0 exige controles de aplicação parcial, mas atribui toda
observação à identidade do candidato e exige uma requisição para respostas
preditas. Um candidato que sempre retorna códigos válidos não produz o
controle misto necessário. Reetiquetar uma fixture como resposta real
fabricaria origem e requisições.

## Decisão do integrador

Revisar a representação para **1.1.0**, antes de liberar C03/C04. Esta é uma
correção do instrumento de avaliação, dentro da execução autônoma autorizada.
Não altera os rótulos, os 24/36 IDs, a rubrica, os critérios numéricos,
o orçamento pendente ou a decisão humana sobre o vencedor.

Foram consideradas duas abordagens:

- Associar um relatório de controles separado ao relatório do candidato.
  Isola as identidades, mas acrescenta validação entre relatórios, inventários
  e denominadores de gates que o contrato atual exige no mesmo lote.
- Identificar explicitamente observações de controle injetado no próprio lote.
  Conserva o caminho de validação e decisão e permite excluir controles da
  medição do candidato. Requer representação e validação próprias da origem.

Adotar a segunda abordagem. O contrato deve identificar cada controle
injetado e sua política versionada por hash, separadamente da identidade do
candidato. Um controle injetado só pode ocupar um ID sintético de controle,
nunca um dos relatos do dataset. Não pode declarar chamadas, tokens, custo,
modelo retornado, scores ou tempo de inferência reais do candidato. Os totais
de inferência/uso do candidato excluem essas injeções e os relatórios exibem
a quantidade e a origem dos controles separadamente. Preservar os controles
completos/inválidos que comprovam zero chamadas e a detecção de aplicação
parcial independentemente das respostas naturais do candidato.

Também é necessário registrar uma tentativa despachada quando o processo
encerra sem resposta. A C02 deve manter um diário durável do plano, despacho,
conclusão e interrupção, com uso desconhecido explicitamente desconhecido.
Pode emitir um manifesto de interrupção separado e um relatório do prefixo
validado. Uma tentativa sem resposta não vira observação fabricada com zero
requests; casos não iniciados continuam distintos dos interrompidos.

As outras correções dirigidas são enquadramento JSONL por LF/CRLF, com rejeição
de linhas vazias e conteúdo extra, e leitura de recursos ao final do processo
para registrar um pico de memória posterior ao aquecimento. Separadores
Unicode dentro de strings continuam válidos.

## Passagem e verificação

O integrador prepara e revisa o contrato 1.1.0 em branch/worktree próprias.
A frente C02 corrige diário, enquadramento e recursos na sua worktree, sem
consumir alterações não commitadas de outra frente. Após o aceite e a
integração do contrato, recebe sua base imutável para implementar os controles
e atualizar os locks, exemplos e relatórios. A revisão dirigida deve comprovar
os quatro achados antes da liberação dos adaptadores.

A consequência deste ajuste é revisar formatos e exemplos técnicos antes de
existirem consumidores reais. As evidências 1.0.0 permanecem no histórico Git.
Nenhuma chamada a fornecedor ou gasto foi autorizado por esta decisão.
