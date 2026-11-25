# Fechamento da C01 — contratos e passagem para C02

Base de retomada: `13adb18173074fcb624dacc5c2f8151e4f79340c`.
Os critérios e a divisão 24/36 foram aprovados pelo responsável em 2026-11-23.
A revisão dos rótulos possui oito casos aprovados diretamente e 52 por IA
delegada. Orçamento de API e escolha do vencedor permanecem pendentes.

## Restrições globais

- Preservar dataset/catálogo e seus hashes, relatórios históricos F08, contratos
  HTTP/Kafka públicos e código Rails/React. Não executar nem selecionar modelos.
- Usar `protocolo-comparacao.json`, `divisao-dados.json`, `rubrica-comum.md` e
  CLASS-SPEC-001 como fontes normativas. Critérios numéricos não mudam nesta etapa.
- Contratos neutros de fornecedor; sem exigir parser Choice do Jev, probabilidades
  fabricadas ou equivalência entre scores de modelos diferentes.
- C01 encerra contratos e exemplos; o agregador/runner de avaliação é C02.
- Ausência de credencial/orçamento não bloqueia schemas e fixtures. Nenhuma
  autorização de chamada paga está implícita na autonomia de execução.

## Task 1: Entregar contratos neutros e fixtures verificáveis

Leia AGENTS.md e os arquivos normativos acima. Trabalhe no ambiente preparado
pelo integrador. Pode editar somente
`docs/planejamento/classificacao-comparativa/contratos/` e
`script/check_classification_contracts.py`. Integração e documentação geral
ficam com o chat central. Entregue contrato v1.0.0 em JSON Schema 2020-12,
exemplos e verificação local sem fornecedores.

O conjunto cobre entrada do experimento, observação bruta do adaptador,
resultado por caso/aplicação e relatório agregado/manifesto de execução.
Escolha uma representação compacta e estável e documente claramente os nomes.
O input inclui marca sintética, texto, catálogo e campos recebidos/ausentes;
schemas não aceitam gabarito, rationale, estrato ou origem da revisão no input
enviado ao modelo. Validar catálogo e campos antes da inferência, inclusive
vazios/nulos/omitidos e entrada completa ou inválida com zero chamadas.

Separar status por campo fornecido, predito, abstenção, inválido e erro.
Preservar campos válidos do canal, escolhas brutas e a aplicação efetiva.
Complemento completo ou revisão: um resultado ausente/inválido/abstido/erro
impede aplicar todas as novas predições, mantendo valores válidos recebidos.
Um campo bruto correto pode permanecer não aplicado. JSON Schema valida
estrutura; invariantes entre input/observação/resultado são verificadas
separadamente quando não expressáveis no schema.

Registrar fornecedor, modelo solicitado/retornado, revisão dos pesos quando
disponível, versão do adaptador/política, modo fixture/real e tipo do score
opcional. Não assumir score calibrado; preservar sua natureza. Registrar tempo
por relato completo (incluindo falhas), cold start/carregamento separado,
tentativas, tokens quando disponíveis, custo observado versus estimado, origem
da tarifa e indisponibilidade explícita. Ausência de medição não vira zero.

Relatório inclui versão/hash dos dados, catálogo, rubrica, protocolo, divisão,
prompt/política, revisão Git e ambiente; inventário dos artefatos; métricas
com numerador/denominador e estado medido/não medido/parcial/indisponível;
resultados por campo, máscara e estrato. Elegibilidade é pass/fail/inconclusive,
e fixture ou evidência incompleta nunca vira aprovação de um modelo real.
Não implemente agregação de métricas nem um adaptador de modelo na C01.

Documente interface portável por JSON/JSONL entre Ruby e Python: uma entrada
por relato, observação normalizada por tentativa, erros operacionais explícitos,
ordem/IDs estáveis e regras para batch sem recarregar pesos por relato.
O comando de avaliação e invocação concreta pertencem à C02, preservando o
formato de dados congelado. Metadados de avaliação ficam fora do input do modelo.

Fixtures devem cobrir: entrada completa; omissão simples e dupla; ausente nulo
e vazio; valor presente fora do catálogo; abstenção; código de saída inválido;
timeout/erro; campo bruto correto recusado por outro campo; score ausente ou
de ranking; preservação de campos; sucesso/erro de versão; falta de medição
e relatório fixture/incompleto. Exemplos negativos exercitam tanto schema
quanto invariantes semânticas, com resultado esperado explícito.

O verificador deve validar schemas/fixtures offline, refs locais sem buscar
rede, unicidade e compatibilidade de IDs/versões; diferenciar erro de estrutura
de violação semântica. Use Python e `jsonschema` já disponível; documente a
dependência. Não instale runtimes/modelos nem execute Rails/Docker neste trabalho.

Faça commits Conventional Commits em português. Sem merge ou push. Retorne
status, commits, comando e resultado das verificações, relatório no caminho
fornecido pelo integrador e eventuais limites. A revisão é feita pelo integrador.

## Task 2: Revisar, integrar e congelar o protocolo

Revisar aderência e qualidade do diff da Task 1. Conferir exemplos negativos,
as regras de tudo-ou-revisão e metadados de evidência ausente. Corrigir achados
relevantes e registrar resultado real. Integrar na branch da C01, atualizar
rubrica/spec/canonical hashes e o aceite, preservando orçamento pendente.

## Task 3: Liberar C02 e sincronizar o quadro

Integrar C01 na main local após verificações. Registrar aceite e SHA imutável
no card/issue e atualizar o épico, plano e passagem. Preparar ambiente próprio
da C02 e despachar somente o avaliador fixture; C03/C04 dependem de C02.
As correções R01/R02 seguem independentes, com arquivos próprios. O atendente
real E01 só será retomado depois de concluir e publicar o projeto.
