# C05-SF1 — piloto local de categoria com SetFit

Pedido de 25/11/2026: testar SetFit com um modelo multilíngue pequeno e
permitir avançar no restante do projeto enquanto a categorização fica em
espera. Base inicial `e0b93d91ff081cdd368db4c13ae93eee57a2237e`.

O piloto responde se vale continuar a investigação. Não seleciona o melhor
modelo, não integra no Rails e não encerra C05/C06/C07. A demonstração
continua fixture; campos válidos do canal e revisão humana continuam disponíveis.
Nenhuma chamada paga, acesso a chaves ou conciliação financeira é necessária.
A pendência financeira da R5 permanece preservada.

## Contratos e limites

- Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`,
  fixando o commit efetivamente baixado. Usar somente arquivos públicos e
  pesos seguros, sem executar código remoto do repositório do modelo.
- Executar em CPU, com duas threads e dependências num ambiente isolado.
  Registrar versões exatas, hardware, hash das fontes, seed e argumentos.
  Venv, cache, pesos e modelos treinados ficam ignorados pelo Git.
- Fonte: dataset R2 2.0.0 e split R2 2.0.0 existentes. Selecionar somente os
  IDs de `development` e, entre eles, somente os casos com `category` em
  `missing`. São 16 textos: quatro para cada uma de `pix`, `payouts`,
  `terminal` e `informacao_insuficiente`. Conferir essa contagem antes de treinar.
- Entrada do modelo: apenas `text`. Nunca fornecer ID, rótulo esperado,
  rationale, estrato, categoria do canal ou gabarito. Nenhum caso final entra
  em treinamento, calibração, validação ou ajuste. Não gerar textos novos
  nesta fatia. Não reclassificar o final consumido.
- Conferir e registrar os comprimentos tokenizados contra o limite do
  modelo antes de treinar; qualquer texto acima dele interrompe o piloto
  em vez de sofrer truncamento silencioso.
- `informacao_insuficiente` é uma decisão de revisão para o piloto, não uma
  quarta categoria do catálogo. Este piloto não mede prioridade.
- Uma execução predefinida: validação cruzada estratificada com quatro
  divisões, `shuffle=True`, seed 42. Cada texto é avaliado uma vez por um
  modelo que não o usou para treinar. Conferir que textos normalizados não
  se repetem entre treino e validação. São 12 textos de treino e quatro de
  validação por divisão; somente três exemplos por classe no treino.
- Treinar efetivamente o encoder pelo SetFit (pares contrastivos) e sua
  cabeça classificadora. Fixar antes de medir: uma época do encoder,
  cinco iterações de amostragem de pares, batch 8, learning rate do encoder
  2e-5, cabeça de regressão logística, seed 42. Adaptar somente a sintaxe à
  versão instalada, registrando o equivalente; não mudar hiperparâmetros
  em função dos acertos.
- Sem busca de limiar, novos seeds ou repetição para melhorar resultados.
  Salvar probabilidades da cabeça apenas como scores não calibrados.
  Não aplicar limiar de 80% nem apresentá-las como probabilidade confiável.
- Prazo operacional: até 30 minutos para instalação/download e até 15
  minutos para o treinamento total. Uma falha deve gerar registro parcial
  claro, sem inventar previsões. Ajustes de instalação/código para executar
  o mesmo experimento são permitidos, sem otimização pelos resultados.
- Medir separadamente download/carregamento, treino e inferência por texto.
  Uma inferência de aquecimento fixa por divisão não entra no percentil.
  Medir cada texto de validação uma vez, incluindo classificação e extração
  do resultado. Reportar p50/p95 por posto mais próximo e tamanho da amostra;
  o resultado não é o aceite do protocolo completo de atendimento.
- Artefatos: seleção/contagem de IDs, divisões de treino/validação, commit
  do modelo, ambiente, parâmetros, previsões individuais, scores, métricas
  por classe, matriz de confusão, reconhecimento de revisão, cobertura de
  categoria e duração. Reportar explicitamente que são dados sintéticos,
  rótulos exploratórios e amostra pequena. Sem alegação de qualidade em produção.

## Execução e aceite

| Tarefa | Produz | Consome / fronteira | Verificação |
| --- | --- | --- | --- |
| SF1-A | Runner isolado, ambiente e resultado real de categoria | Apenas desenvolvimento R2 e modelo público; sem contratos da aplicação | Treino contrastivo e cabeça executados; separação sem vazamento; artefatos e métricas reproduzíveis |
| SF1-R | Revisão por tarefa e ampla do piloto | Diff, fontes, manifesto e resultados SF1-A | Conferir escopo, cálculos, ausência de final, revisão como decisão separada e ausência de aprovação indevida |
| ST1 | Estado de entrega com classificador em espera | Relatórios existentes F09/F10/UX02/R01/R02 e esta decisão | Preservar a exigência futura do classificador; apontar somente lacunas reais independentes |

SF1-A não altera arquivos de ST1 e ST1 não altera fonte, dados, ambiente ou
resultados do piloto. A revisão não roda novamente treinamento para produzir
uma amostra mais favorável. A falta de critério completo ou uma execução
interrompida permanecem visíveis.

Após o piloto, escolha, calibração e integração do classificador ficam em
espera até retomada explícita. O usuário propôs adiar a frente, não retirar
silenciosamente a exigência futura de classificação real nem declarar todo
o projeto concluído. F10 pode avançar em paralelo com o classificador fixture.
O teste completo em outra rede continua necessário para seu aceite interno.
E01 continua evolução posterior e opcional; 10 mil conexões continuam
experimento exploratório sem medição, sem virar requisito novo de conclusão.

## Referências

- [SetFit: treinamento e inferência](https://huggingface.co/docs/setfit/en/quickstart)
- [Modelo multilíngue](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
- [Último resultado real da classificação](../../c05-luna-r5-resultado.md)
