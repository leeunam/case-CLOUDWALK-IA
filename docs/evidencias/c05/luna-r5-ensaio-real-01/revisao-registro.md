# Revisão dirigida da atualização do resultado R5

Base examinada: main `8314ca56645e016167adf94833cb991be44421f6`. Revisão somente leitura, sem API, sem SQLite privado, sem teste novo e sem alteração dos documentos revisados.

## Achados

1. Os estados e valores nos quatro documentos conferem com os artefatos: desenvolvimento 8/8; final interrompido após 30/44 despachos; 29 respostas conciliadas e uma tentativa sem custo conhecido; 14 despachos restantes não enviados; prefixo inconclusivo; 1/26 aplicações; 0/4 urgentes após política; p95 parcial 3.269,135 ms; reserva USD 1,239 sem confirmação de cobrança. O custo reconciliado, saldos conservadores e suspensão de chamadas estão consistentes.

2. O trecho “nos campos classificáveis observados, foram 30/30 corretas” pode ser lido como se todas as tentativas de classificação nesses campos tivessem êxito. O denominador correto são **as propostas válidas efetivamente emitidas**: 30 propostas para campos classificáveis acertaram 30/30. Isso exclui dois campos classificáveis sem proposta por erro de transporte. Separadamente, três propostas adicionais nos campos cujo rótulo esperado era `informacao_insuficiente` foram indevidas. Sugestão: “Entre as 30 propostas válidas emitidas para campos classificáveis, 30/30 coincidiram com o gabarito; dois outros campos classificáveis não tiveram proposta por erro de transporte. Nos três campos de ambiguidade esperada, o modelo propôs valores em vez de pedir revisão.” Preservar também o total original de 33 propostas válidas: 30 corretas e 3 indevidas.

3. A cópia dos artefatos preserva os bytes: os 39 caminhos existentes tanto no executor quanto no checkout principal têm SHA-256 idêntico. O checkout principal acrescenta apenas `auditoria.md`, `supervisor-development.json` e `supervisor-final.json` nesse diretório. Não encontrei divergências semânticas de cópia.

4. Os registros em `final/inputs.jsonl` e `final-plan/inputs.jsonl` não estão malformados. Cada arquivo tem 49 registros delimitados por LF e os 49 são JSON válidos. O controle `ctl-simples` inclui U+2028, U+2029 e U+0085 dentro do texto, como caracteres Unicode da entrada. Um leitor que use `str.splitlines()` separa essas posições e gera 52 fragmentos, causando falsos erros nas linhas 38–41. JSON Lines usa LF como delimitador; a verificação deve dividir por LF físico, preservar esses caracteres e não “consertar” ou remover o controle. Os arquivos `verified_inputs.jsonl` e relatórios estruturados permanecem íntegros.

## Encaminhamento

Não há achado material que contradiga o resultado negativo/inconclusivo. O único ajuste recomendado é explicitar o denominador das 30/30 propostas e as duas falhas de transporte excluídas desse denominador. Nenhuma alteração foi feita nos arquivos originais.

HEAD permaneceu `8314ca56645e016167adf94833cb991be44421f6`.
