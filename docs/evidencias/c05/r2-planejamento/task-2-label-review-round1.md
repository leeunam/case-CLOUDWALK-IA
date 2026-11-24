# C05-R2 · nova conferência da Task 2

**Especificação — aprovada. Qualidade dos rótulos — aprovada como referência exploratória de IA.** Os dez casos substituídos sustentam os 13 alvos atribuídos. Para os outros 26 casos, o registro incorpora as decisões anteriores sobre 35 alvos. O conjunto final tem 48 de 48 alvos concordantes e zero disputas abertas.

## Versões e escopo

A revisão usou a branch `docs/r2-protocolo-dados` na worktree `.worktrees/r2-dados`. O commit revisado é `96b9dfa920756236b5e81a08e04df2a3e71a4acf`, filho de `29973d74209796c54076fcaf9348c14a37ab1743`. Os hashes recalculados coincidem com o relatório de autoria e o documento de origem aponta para os bytes finais do conjunto.

| Artefato | SHA-256 |
| --- | --- |
| Conjunto final | `4f1d712b87bbee326e3602b3fb74398558f929b08c1709b11407676869a21145` |
| Autoria final | `2236559d41cf1f1a50b09e961fd6797bb83e0f71578e9fc217b8c6dd195b2b7a` |
| Conjunto da primeira revisão | `de29a2de28e9b643dfe82eff97ef54263afa3eca7ad0b8642f5c3fc4ee22d4b8` |
| Registro anterior das 36 decisões | `193189ebbc798991b620f03b6b715c6f069bd1f995287ca35e4b26a550c8cf0e` |

O diff dos blobs do conjunto (`92e6894 → e380d64`) contém somente substituições de `text` e `rationale` nos dez IDs registrados na autoria. Todos os demais bytes dos 26 objetos ficam fora das linhas alteradas. O cabeçalho, os campos recebidos, as máscaras, os estratos e os rótulos permanecem idênticos em todos os 36 registros. A inspeção do diff sustenta a reutilização por ID das 26 decisões vinculadas ao hash anterior. A autoria em `d6760d1` atualizou o hash e registrou o histórico desse recorte.

## Revisão semântica

| Relevância e IDs | Decisão fundamentada na rubrica 1.0.0 |
| --- | --- |
| Alta · r2-014, r2-019, r2-022 | A urgência vem, respectivamente, de desvio de pagamentos que continua ocorrendo, de risco presente a pessoas e de consequência material prestes a ocorrer. A regra de ação imediata abrange o perigo físico mesmo sem afirmar que as vendas pararam. Rubrica, linhas 25–26. |
| Média · r2-020, r2-023, r2-030, r2-033 | As dificuldades afetam um reembolso, um caixa, um contrato ou um lote específico. O texto fornece evidência de continuidade, processamento dos demais itens ou alternativa manual. Rubrica, linha 22. |
| Média · r2-031 | O impacto em dezenas de equipamentos e a manutenção programada sustentam o retrabalho significativo. A venda e a via digital continuam. Rubrica, linhas 23–24. |
| Média · alvos de categoria em r2-001, r2-007, r2-030, r2-031, r2-033 | O objeto do pedido identifica uso ou conservação da maquininha, programação de Pix ou conciliação do repasse, conforme o ID. Rubrica, linhas 11–15. |

A composição continua com 12 casos por máscara. Categoria tem 10 classificáveis e dois para revisão. Prioridade tem 10 e dois. A máscara dupla tem nove e três. Dos 24 alvos de cada campo, cinco categorias e três prioridades são insuficientes, com uma sobreposição. Seis prioridades ausentes são urgentes, três na máscara simples e três na dupla, uma destas em revisão.

O revisor `/root/r2_revisar_dados` fez a leitura dos dez casos e conferiu o escopo do diff, os pins e o vínculo à revisão anterior. As verificações estruturais e de codificação constam como executadas no apêndice do autor e não foram reexecutadas pelo revisor. O arquivo `task-2-label-review-final.json` discrimina as 36 decisões, a evidência, o modo de conferência e a origem exploratória. Não houve inferência de candidato ou aprovação humana. O parecer de similaridade pertence ao terceiro conferente. Nenhum achado de especificação ou rotulação exige correção.
