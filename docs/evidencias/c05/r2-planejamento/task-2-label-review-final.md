# C05-R2 · segunda revisão das substituições da Task 2

**Especificação — aprovada. Qualidade da rotulação — aprovada como referência exploratória de IA.** O único alvo reavaliado, a prioridade de `r2-014`, tem evidência para `urgent`. Com os 47 alvos de 35 registros idênticos já aprovados, o parecer consolidado abrange 36 casos e 48 alvos. Há zero disputas abertas.

**Fundamentação de alta importância.** O relato de `r2-014` conecta o saque debitado sem entrega de cédulas à necessidade de pagar uma passagem em espécie e ao fechamento do último embarque em seis minutos. O compromisso de trabalho explica a consequência relevante da perda do embarque. Essa combinação sustenta a intervenção imediata prevista na rubrica comum 1.0.0, linhas 25–26. O risco é prospectivo, e o rótulo não exige que a travessia já tenha sido perdida. A categoria foi fornecida.

**Escopo e integridade.** Na branch `docs/r2-protocolo-dados`, worktree `.worktrees/r2-dados`, o commit `9648208b47112fa87a8e584bb30e2779f2449ed8` tem por pai `96b9dfa920756236b5e81a08e04df2a3e71a4acf`. O diff de `final-cases.json` mostra duas linhas substituídas no objeto `r2-014`, nos campos `text` e `rationale`. Os demais objetos são byte a byte idênticos. O diff de autoria atualiza o pin e vincula o ID e a rodada àquela base. Os SHA-256 recalculados conferem com o apêndice do autor.

| Artefato | SHA-256 |
| --- | --- |
| Conjunto revisado | `17f5bae372983f90aa1956d0d583db25483a77a3ff35e4f1041ad4d51b897af9` |
| Autoria revisada | `e4ee3ff880c230dff7b53136c64e6db30b4c96e774d3f695663786793f3495bc` |
| Conjunto anterior | `4f1d712b87bbee326e3602b3fb74398558f929b08c1709b11407676869a21145` |
| Consolidado anterior | `90aeba5068d0135be5e122f5f1ca6597cdb1a0067b24b81e938504835fc5ca1f` |

Todos os campos que determinam as cotas coincidem entre as versões. Há 12 casos por máscara, com 10, 10 e 9 classificáveis nas máscaras categoria, prioridade e dupla. Dos sete para revisão, cinco têm categoria insuficiente e três, prioridade insuficiente, com uma sobreposição. Das seis prioridades urgentes omitidas, três pertencem à máscara de prioridade e três à dupla, uma delas em caso para revisão.

O revisor `/root/r2_revisar_dados` conferiu o delta e a evidência textual do alvo alterado. O registro `task-2-label-review-final.json` identifica a origem da decisão dos 36 IDs. O apêndice do autor registra suas verificações locais, que o revisor não reexecutou. O parecer cobre a rotulação exploratória por IA e deixa a similaridade ao terceiro conferente. Não houve aprovação humana nem inferência de candidato.
