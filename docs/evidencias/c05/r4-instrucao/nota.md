# C05-R4 · Instrução de categoria da Luna

Na etapa de desenvolvimento R3, a Luna acertou sete dos oito campos pedidos.
Em um caso escolheu uma categoria quando faltava informação para distinguir a
operação. A instrução 1.2.0 orienta o modelo a identificar o que o cliente
quer fazer, entender ou corrigir e a verificar quais fatos ligam essa demanda
a uma operação do catálogo.

Uma consulta pode indicar a operação em linguagem comum, mesmo antes de sua
realização. Uma tentativa que falhou também pode identificar o assunto. A
instrução diferencia essas situações de uma causa cogitada ou de uma operação
apenas mencionada. Descartar uma possibilidade deixa em aberto as demais.
Quando a escolha depender de presumir um fato, a saída para categoria é
`informacao_insuficiente`. A política 1.1.0 encaminha o conjunto para revisão
se qualquer campo solicitado tiver abstenção.

O manifesto em `script/classification_comparison/adapters/luna/r4/candidate.json`
identifica a nova instrução. A comparação com a R3 confirmou a mesma redação
desde a instrução de prioridade até o contrato de saída, além dos mesmos
arquivos de política, rubrica e configuração operacional. O teste local montou
os corpos JSON das duas versões para categoria ausente, prioridade ausente e
ambas ausentes. Em cada par, mudou apenas o conteúdo da mensagem de sistema
que contém a instrução. Nenhuma requisição foi transmitida.

A revisão técnica verificou o conteúdo da requisição. A capacidade da Luna
de aplicar essa distinção a pedidos novos continua sem medição.
