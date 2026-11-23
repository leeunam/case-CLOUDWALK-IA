# Autorização de um piloto pago

**Registro histórico anterior ao primeiro piloto.** A autorização posterior de até US$ 10 e o recorte de uma requisição estão em [autorização do piloto econômico](autorizacao-piloto-economico.md). O primeiro piloto real foi concluído; [recibo](../../evidencias/c03/piloto-unitario-real.json). O responsável aprovou depois substituir o critério aquecido pelo tempo total da classificação, conforme o [plano prospectivo](plano-latencia-total.md). As condições abaixo explicam a decisão original de configuração.

Decisão técnica do integrador durante a revisão C03, em 23 de novembro de
2026. A autorização atual continua **pendente**, sem teto ou chamada paga.

O protocolo de qualidade e seus hashes permanecem congelados. A revisão
encontrou que alterar seus campos financeiros para iniciar o piloto quebraria
o preflight do avaliador. Por isso, a futura autorização financeira de uma
execução será registrada em um **manifesto separado**, dentro da frente Qwen,
atrelado ao protocolo, ao modelo e à configuração do piloto por seus hashes.
Esse manifesto não muda os critérios de escolha, os rótulos ou a partição.

O exemplo versionado deve permanecer desabilitado e sem teto. Somente depois
de uma resposta explícita do responsável sobre o limite de gasto o integrador
poderá preparar a autorização da execução. Ter uma chave ou créditos não
substitui essa autorização. A chave fica no ambiente local e nunca no
manifesto, nos logs ou no GitHub.

O preflight deve conferir a autorização, sua vinculação à configuração e ao
protocolo imutáveis, o teto, modelo, IDs elegíveis e limites do piloto antes
de construir o transporte ou consultar a credencial. O lote mantém uma
tentativa por caso, concorrência um e reserva conservadora antes do envio.
Uso desconhecido conserva a reserva; cobrança ou tokens acima do limite
interrompem os envios seguintes. O guia precisa declarar o alcance do teto
por lote e impedir retentativas ocultas.

Os testes de autorização positiva usam somente transporte sintético. Uma
configuração de teste não deve ativar o fornecedor real. A execução ao vivo
continua bloqueada até a liberação humana e a confirmação técnica das
informações de faturamento necessárias ao limite.

## Aquecimento e tempo observado

Um orçamento configurado não comprova aquecimento. Enquanto a C03 não puder
comprovar o estado do recurso de inferência avaliado, registra `unknown` e
conserva o tempo integral observado, sem fabricar tempo interno do fornecedor.
Os percentis aquecidos da C02 permanecem sem essa evidência. Uma eventual
adequação do método de comparação remoto/local será discutida antes do teste
final C05; não se aprova o gate aquecido por presunção. As metas numéricas
aprovadas permanecem inalteradas.
