# C05 · Autorização do primeiro lote final

Em 24/11/2026, após o integrador informar que o próximo passo era liberar a
avaliação final do Qwen após consolidar os gastos anteriores, o responsável
respondeu: «boa, libero, vai la».

Esta autorização permite **um lote final**, com 36 relatos e 13 controles do
conjunto congelado, até 44 chamadas sequenciais ao `qwen/qwen3.8-27b` na Feita,
uma tentativa por caso. Preserva o teto **cumulativo de US$ 10**, incluindo os
pilotos anteriores e reservas sem custo conhecido. A autorização não é uma
nova verba por execução nem uma aprovação antecipada de adoção operacional.

Base da preparação: `7eb1bf193e8183248293d2a1272a4c7240f4a7ec`.
Branch `feat/executor-qwen-final`, worktree `.worktrees/c05-comparacao`.
Executor previamente revisado: `e4ce14c95a4a59737b000bcc8dfa21009a1d566d`.

O [pré-voo](preflight.json) confirma as tarifas exibidas, a conversão documentada
de créditos para USD e os dois registros anteriores. A conta única persistente
será inicializada com US$ 0,001038 anteriores. A reserva de US$ 1,5032 por
despacho usa limites e preço de cache arredondados para cima; não prevê o custo
real. [Configuração específica](config.json). Os exemplos genéricos reais
continuam desabilitados.

O manifesto específico vinculará a conta, esta configuração, o HEAD de
preparação, as fontes, os hashes, as versões e a ordem dos IDs. Conta e
manifesto ficam no diretório privado ignorado `.superpowers/financial/c05-qwen/`.
A chave local será carregada somente no processo real, sem constar de comandos,
artefatos ou mensagens. Não haverá chamada adicional de sondagem.

Sem custo verificável, após timeout ou queda, o executor conserva a reserva e
interrompe o lote. Um prefixo interrompido fica inconclusivo e não será retomado
ou repetido sob esta autorização. Resultados finais não poderão ser usados
para ajustar prompt, política, dados, rótulos ou limites de aprovação.

A análise posterior deve declarar os denominadores, erros de urgência,
abstenção, cobertura, latência total e custo separadamente. C06 exige
elegibilidade comprovada e decisão humana de adoção.
