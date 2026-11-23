# Autorização do piloto econômico Qwen · 23/11/2026

O responsável confirmou a credencial local e autorizou **até US$ 10**, acrescentando explicitamente que as requisições devem ser minimizadas. Trata-se de teto total desta autorização, não de meta de consumo nem de teto por tentativa. Pela tabela pública Feita, um crédito equivale a US$ 0,01; US$ 10 correspondem a 1.000 créditos. [Fonte](https://feita.ai/models/qwen/qwen3.8-27b).

## Primeira execução

- Uma única requisição real em `jev-003`, pertencente à divisão de desenvolvimento congelada, com categoria e prioridade ausentes.
- Zero controles naturais pagos, concorrência um, uma tentativa e nenhuma repetição automática. O diretório e o diário da tentativa são exclusivos e não podem ser reutilizados.
- Pedido de resposta limitada a 128 tokens e solicitação de raciocínio desativado. O suporte ao parâmetro é anunciado pelo catálogo; seu funcionamento é uma das verificações do primeiro piloto. Não se presume que essa opção confirme o total de tokens cobrados.
- Rubrica, catálogo, relato, critérios e divisão 24/36 permanecem os aprovados. O relatório de um caso é inconclusivo e não escolhe vencedor nem comprova taxa de erro.
- A configuração e a autorização da execução ficam ligadas por hashes. A chave permanece somente no ambiente do processo, sem aparecer em arquivos versionados ou no relatório.

## Reserva conservadora antes da chamada

O catálogo oficial do próprio gateway, `GET https://api.feita.ai/gateway/v1/models`, informou para `qwen/qwen3.8-27b` contexto máximo de 1.024.000 e saída máxima de 131.072 tokens. Preços por milhão: entrada US$ 0,425; leitura de cache US$ 0,085; escrita de cache US$ 0,53125; saída US$ 2,55. O transporte nativo `http.client` conseguiu ler esses metadados públicos sem credencial ou inferência; o cliente urllib recebeu HTTP 403.

Para esta primeira chamada, a reserva usa os máximos anunciados do modelo, somando conservadoramente ambas as tarifas de cache à entrada. Ela não usa 128 como garantia do total faturável de saída:

`1.024.000 × (0,425 + 0,085 + 0,53125) / 1.000.000 + 131.072 × 2,55 / 1.000.000 = US$ 1,4004736`.

A reserva não representa gasto esperado. O payload real será curto, pedirá 128 tokens e só será enviado uma vez. O teto operacional do lote inicial será US$ 1,50, abaixo dos US$ 10 autorizados. Os limites e preços são os anunciados pelo gateway; eventuais divergências devem permanecer registradas, sem disparar outra tentativa. A unidade de `usage.cost` ainda não foi confirmada e pode permanecer nula. Os tokens retornados permitem estimativa separada, sem apresentá-la como débito observado da conta.

Se houver timeout ou cobrança indisponível, a reserva continua comprometida no registro do piloto. Não iniciar outro lote automaticamente nem tratar uso desconhecido como zero. A próxima decisão técnica é analisar o recibo desta tentativa antes de considerar chamadas adicionais dentro do teto total.

O protocolo de qualidade e o exemplo de autorização financeira anteriores permanecem congelados e desabilitados. Esta autorização nova não libera os 36 casos reservados da C05, escolha de vencedor, integração C06 ou implantação.
