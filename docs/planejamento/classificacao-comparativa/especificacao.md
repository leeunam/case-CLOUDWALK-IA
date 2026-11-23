# CLASS-SPEC-001 — comparação e seleção do classificador

Versão: 0.1, de 2026-11-23. SDD significa **Specification Driven Development**:
o comportamento e suas provas são definidos antes da implementação.

## Estado e objetivo

A comparação **Qwen pela Feita × GLiClass local** foi escolhida pelo responsável.
O vencedor, os limites de aceitação, os dados finais revisados e o orçamento de
execução ainda não foram aprovados. C01 resolve esses pontos antes de liberar
as tarefas dependentes. Esta especificação não declara um vencedor antecipado.

O objetivo é escolher um classificador para completar categoria e prioridade
ausentes, com acerto, tratamento de urgência, abstenção, latência e custo
mensurados. O experimento usa modelos já treinados e relatos sintéticos em
português. Não inclui treinamento do zero, fine-tuning, engenharia reversa do
Jev, novos canais reais ou uma plataforma genérica de roteamento entre modelos.

## Regras de produto preservadas

1. Validar a entrada e o catálogo ativo da marca antes da inferência.
2. Com os dois campos válidos, preservar os valores e fazer zero chamadas ao
   classificador. O atendimento segue ao atendente simulado pelo Kafka.
3. Campo ausente, nulo ou vazio pode ser completado. Um campo válido fornecido
   pelo canal permanece idêntico e não conta como acerto do modelo.
4. Campo presente inválido ou catálogo incompatível encaminha para revisão,
   sem chamada ao modelo. O classificador não cria códigos de catálogo.
5. Os dois campos precisam ficar válidos para aplicar o complemento. Quando
   qualquer campo solicitado se abstiver, falhar ou vier inválido, registrar
   as escolhas brutas, preservar os campos do canal e encaminhar o conjunto
   para revisão. Não aplicar apenas uma parte das predições do modelo.
6. Registrar separadamente categoria e prioridade, escolhas brutas e valores
   aplicados. Abstenção significa `informacao_insuficiente` ou uma política
   de recusa explícita definida e congelada em C01.
7. O modelo não decide autorização, capacidade, carteira ou responsável humano.
   Regras de marca, fila, distribuição e handoff continuam no domínio existente.
8. A integração conserva idempotência, versões, descarte auditado de resultados
   tardios e prevalência de uma correção humana posterior.

## Contrato do experimento a congelar em C01

A versão final deve ter JSON Schema, exemplos válidos e inválidos e uma
semântica única para os dois adaptadores. Não é o contrato HTTP público Rails.

| Área | Informação obrigatória |
| --- | --- |
| Entrada | ID sintético, texto, marca, catálogo/códigos/descrições versionados, campos recebidos e máscara de omissão. |
| Decisão por campo | Valor recebido, campo solicitado ou não, escolha bruta e estado: fornecido, predito, abstenção, inválido ou erro operacional. |
| Aplicação | Resultado completo ou revisão; classificação efetivamente aplicada; motivos e preservação dos campos do canal. |
| Origem | Provedor, modelo solicitado/retornado, revisão dos pesos quando disponível, modo fixture/real e versão do adaptador/política. |
| Pontuações | Valores brutos opcionais e sua natureza: probabilidade do fornecedor, score de ranking, autoavaliação textual ou ausente. Calibração não comprovada deve aparecer como não avaliada. |
| Tempo | Duração total da chamada; cold start, carregamento e inferência separadamente quando mensuráveis; unidade e tamanho da amostra. |
| Uso e custo | Tokens cobrados quando disponíveis, custo observado, estimativa separada com fonte/data/tarifa e campos indisponíveis explícitos. |
| Ambiente | Revisão Git, hashes dos dados/catálogos/prompt/política, hardware/runtime, concorrência, semente e inventário dos artefatos. |

É proibido fabricar uma distribuição de probabilidades para encaixar uma
resposta Qwen ou GLiClass no parser Choice do Jev. Usar o mesmo significado
de conclusão/revisão e registrar evidências próprias de cada fornecedor.
O avaliador comum valida e agrega decisões; cada adaptador faz sua inferência
e a conversão de saída segundo o schema congelado.

## Dados e prevenção de vazamento

- A base existente tem 60 relatos, 20 com categoria omitida, 20 com prioridade
  omitida e 20 com ambas omitidas. Versão 1.1.0, SHA-256
  `0e7e4c342c2a39cefd89855d8c0513f447d7878303eb4091488ca8af78928880`.
- Esse conjunto é provisório. Os campos ausentes de `jev-001`, `jev-002`,
  `jev-005`, `jev-041` e `jev-044` possuem aprovação humana registrada na
  [revisão parcial](revisao-de-rotulos.md). Os outros 55 relatos aguardam revisão.
- C01 registra a revisão humana de todos os rótulos e justificativas. Alterar
  texto, rótulo, catálogo ou máscara exige nova versão/hash e registro do motivo.
- Separar exemplos de desenvolvimento/calibração do conjunto final de teste.
  Prompts, limiares e política de abstenção não podem ser ajustados usando os
  resultados do teste final. C01 escolhe e registra a separação e os tamanhos.
- O teste pareado usa os mesmos relatos, catálogos e máscaras nos dois modelos.
  Ambos recebem as mesmas definições de categoria, prioridade/urgência,
  informação insuficiente e eventuais exemplos. O formato pode variar, mas
  qualquer diferença de informação ou capacidade de representar o protocolo
  deve ser registrada antes do teste, sem favorecer um dos candidatos.
  Controles de entrada completa/inválida, abstenção, resposta inválida, timeout
  e transporte ficam identificados separadamente.
- Os rótulos nunca são inferidos da resposta de um dos modelos nem aprovados
  automaticamente por outro LLM. Não usar dados pessoais reais.

## Métricas e decisão

Apresentar contagens, denominadores e limitações, por campo, máscara e estrato:

- Acerto da escolha bruta e acerto da classificação aplicada.
- Cobertura automática, abstenções corretas/indevidas, revisão e erros de saída.
- Nos casos cuja prioridade urgente foi omitida: quantos viraram urgente,
  quantos receberam automaticamente prioridade inferior, quantos se abstiveram
  e quantos falharam operacionalmente. Não juntar esses grupos numa taxa única.
- Preservação dos campos válidos do canal, com meta de 100%.
- Latência p50/p95 com tamanho da amostra. Falhas/timeouts ficam contados;
  a latência só dos sucessos não representa a população inteira.
- Requisições, tentativas e perguntas efetivas, tokens e custo de API. GLiClass
  tem custo por chamada de API zero quando executado localmente, mas demanda
  download, memória, CPU/GPU, carregamento e tempo de execução mensuráveis.
  Custo monetário de infraestrutura não observado permanece indisponível.
- Calibração, se avaliada, exige critério e amostra próprios. Scores ou números
  de confiança dos dois modelos não são diretamente equivalentes.

C01 deve fixar, antes da execução final, os limites numéricos de erro de
urgência, cobertura/abstenção, acerto, latência e orçamento, com justificativa
do responsável. Esses valores são decisões do experimento, não exigências
quantitativas do TAPI. Um modelo que se abstém em tudo não ganha por evitar
erros. C05 pode concluir que nenhum candidato satisfaz os critérios ou que
a evidência é insuficiente. A escolha operacional exige decisão humana.
Registrar quantos urgentes com prioridade omitida permanecem no teste final
e o alcance da conclusão permitido pelo tamanho da amostra. Um piloto pequeno
sem erros observados não comprova uma baixa taxa de erro em produção.

## Execução e limites financeiros

- Qwen inicial: `qwen/qwen3.8-27b`, no gateway Feita. Confirmar disponibilidade,
  endpoint, versão, capacidades e tarifa no preflight da tarefa; não presumir
  que uma entrada no catálogo garante uma chamada bem-sucedida.
- GLiClass inicial: `knowledgator/gliclass-multilang-mini`; fixar revisão dos
  pesos, licença e dependências antes da medição. Registrar o dispositivo.
- Sem autorização explícita de consumo e chave configurada localmente, rodar
  apenas validação e fixtures. Crédito disponível não libera gasto automático.
- O ensaio real deve exigir teto de custo, limite de casos, concorrência e
  número de tentativas. Estimar o lote antes de iniciá-lo e registrar como o
  limite será aplicado. Tarifa/usage ausentes bloqueiam qualquer garantia de
  orçamento, em vez de virarem custo zero.
- Começar com piloto limitado, usando somente exemplos de desenvolvimento.
  A comparação final começa depois de corrigidos os problemas do piloto e
  congelados seus artefatos. Sem retentativas escondidas ou seleção de resultados.
- Nunca gravar chaves, cookies, cabeçalhos de autenticação ou saldo da conta
  nos relatórios, no Git ou nas issues. Não criar chaves como parte destes cards.
- Fixtures comprovam funcionamento do avaliador, não qualidade do fornecedor.
  Falha total do fornecedor deve aparecer como medição indisponível/bloqueada.

## Integração posterior

O experimento é independente da aplicação. Depois da decisão C05, C06 conecta
um único classificador ativo por configuração ao fluxo existente. Preservar
o histórico Jev e os testes já disponíveis. Atualizar em conjunto origem da
classificação, schemas/fixtures e tipos consumidores para não registrar Qwen
ou GLiClass como se fossem Jev. O formato público escolhido será uma decisão
explícita de contrato antes de sua implementação; não alterar webhooks e
eventos Kafka incidentalmente.

Se GLiClass for selecionado, empacotar sua execução Python/pesos e verificar
prontidão, carregamento, limites de recurso e falhas na instalação de demo.
Se Qwen for selecionado, documentar credencial, rede, timeout e custo. Não
introduzir UI de troca de modelos, fallback automático entre fornecedores ou
duas inferências por atendimento no escopo atual.

## Dependências do fechamento

C07 verifica a demonstração local depois da integração e das correções R01 e
R02. Os resultados históricos da F08 são imutáveis. A falha de recuperação
dos consumidores, os dois casos limite do analisador e os cenários de escala
continuam explícitos até seus respectivos aceites. Publicação por URL é F10,
com infraestrutura e autorização próprias; não está implícita neste conjunto.

## Fonte das decisões

Referências no checkout: AGENTS.md, CONTEXT.md, especificação MVP, decisões
D015/D017, plano F04/F08/F09/F10, contratos v1 e relatórios F08. Model cards:
[Qwen](https://huggingface.co/Qwen/Qwen3.8-27B),
[GLiClass](https://huggingface.co/knowledgator/gliclass-multilang-mini).
