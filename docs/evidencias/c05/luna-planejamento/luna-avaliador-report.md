# C05-R3 Task3-B · Avaliação offline da Luna

Base `7f04b9b3b2e75c3db4993bcaf0ce82140a86f96f`, entrega `85803430f17d5f582b26890e621746412a85db66`, branch `feat/avaliador-luna`. Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/r3-luna-avaliador`. O commit seleciona 22 arquivos do perfil/execução. O relatório externo à worktree fica com o integrador. Não houve merge, push ou chamada externa. A conta SQLite real e as credenciais não foram consultadas.

## Resultado reproduzido

| Execução fixture | Relatos | Controles | Chamadas | Custo simulado em USD | Resultado |
| --- | ---: | ---: | ---: | ---: | --- |
| Development | 6 | 0 | 6 | 0,003282 | `fixture_ready`, 8/8 alvos, 4/4 fornecidos, 3 completos corretos, 3 revisões integrais, 1 urgente, 0 erros |
| Final | 36 | 13 | 44 | 0,024068 | 36 relatos e oito controles com chamada, quatro controles com bypass e um injetado |
| Conta temporária | 42 | 13 | 50 | 0,027350 | 50 reservas liquidadas, dois lotes concluídos |

Saldo anterior **simulado** de US$ 0,02687405. Saldo simulado conservador depois de reabrir a conta de fixture, US$ 0,05422405. O p95 ficou sem medição com denominadores planejados 6 e 36, respectivamente. Elegibilidade inconclusiva nas duas etapas. O fixture de desenvolvimento simula respostas conhecidas para testar o gate, e o transporte sintético do final usa a projeção existente. A qualidade e a latência da Luna na Feita continuam pendentes.

## Vínculos e interfaces

| Artefato | SHA-256 |
| --- | --- |
| Congelamento da candidata anterior à abertura do final | `d54be325ca254797be9056039bfa5004824a2d587ac78f1d2f9614fe68820c2d` |
| Manifesto da candidata | `1daac4749be2e8ac07989780ce5b4aae58f3f7f2bbbf460fdfb904a98295caf5` |
| Operação Luna | `0666cdd1c99f58c52512681563b72ddcaf4f97593071a1797104526d062678da` |
| Vínculo R3 de dataset, decisões e congelamentos | `339fd9aef7df5cb217e81ca07f69c16551827038400b6d4d1067a73ebb6cf908` |
| Protocolo de qualidade 1.3.0 | `a9fe9fc8fd55420986ca9a1e63ed09d9be8b88d55cd3373235f471d5e50b288b` |
| Lock do relatório 1.4.0 | `7a826e8217be8f5a0ca00b3d51d596dd724b620efcf7ac932744fc02bc18ae1b` |
| 36 finais históricos R2 | `17f5bae372983f90aa1956d0d583db25483a77a3ff35e4f1041ad4d51b897af9` |
| Ledger original C05 schema 4 | `d9a81084546db988ef8afc6f33732120749c749a9415bebae07f3402dbbef44e` |

O checker seleciona `observed-total-luna-1.0` por relatório 1.4.0 e SHA de protocolo. Valida o pacote R2 com seu protocolo histórico antes de conferir equivalência, aprovação D, controle, freeze da candidata, arquivos de runtime/semântica e origem exploratória dos 36 casos finais, com zero aprovações humanas. Plan, validação de entradas, métricas, gate, diário e selo são compartilhados. A CLI C02 genérica bloqueia as duas rodadas dedicadas. `luna/execute.py` usa o descritor fixo em `luna/round_spec.py`. O subcomando privado chama o mesmo wrapper da etapa que gerou o manifesto.

`LunaAdapter(identity, run_id, instructions, capture, budget, timeout_ms)` e `LunaTransport(api_key)` conservam a interface congelada. O corpo usa esforço none, stream false, 128 tokens de conclusão e schema estrito exclusivamente dos ausentes. A identidade real é feita/openai/gpt-5.6-luna e o fornecedor de fixture é simulador-c05-luna. O verificador reconstitui numeradores e denominadores dos fluxos e verifica origem dos controles, limite de uma chamada, ausência de score e prefixos inconclusivos.

A conta global é localizada em relação ao diretório Git comum e vinculada ao ID publicado no manifesto histórico público da C05-R2. Execução real exigiria a conta existente, modo real, tarifa/limites com evidência, teto 10, confirmação e manifesto habilitado. Cada prova de development incluída no manifesto final exige o selo original ao lado da conta correspondente. Mudanças de config/git/saída não criam outro ID de etapa. Exemplos real/manifesto ficam desabilitados, com tarifa real e reserva pendentes. Reservas usam o maior preço sustentado em contexto padrão/longo, incluindo leitura e gravação de cache e pisos conservadores de 1.050.000/128.000 para limites de entrada/saída. O exemplo de saída usa 140.000.

O processo pai publica o deadline absoluto do relógio C02 em arquivo efêmero na pasta privada do IPC antes da entrega de cada caso Luna. O transporte usa o menor prazo entre esse relógio e o interno. A entrada IPC 1.1.0 e os bytes da candidata permanecem preservados. O gateway fecha em finally. Custo conhecido de erro técnico liquida antes da interrupção, custo desconhecido ou timeout mantém reserva, e nenhum desses casos despacha o próximo relato. Abstenção semântica permite concluir o gate.

## Verificações executadas

Na raiz da worktree, estes comandos retornaram zero.

```sh
rtk proxy python3 -B -m unittest discover -s script/classification_comparison
rtk proxy python3 -B -m unittest discover -s script/classification_comparison/c05
rtk proxy python3 -B -m unittest discover -s script/classification_comparison/r2
rtk proxy python3 -B -m unittest discover -s script/classification_comparison/adapters/qwen
rtk proxy env PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen python3 -B -m unittest adapters.luna.test_adapter adapters.luna.test_transport
rtk proxy env PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna.test_round
rtk proxy python3 -B script/check_classification_contracts.py --profile warm-1.0
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-1.1
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-r2
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-1.0
rtk proxy python3 -B /tmp/luna-eval-historical.py
rtk git diff --cached --check
```

C02 39, C05 37, R2 14, Qwen 30, adaptador/transporte Luna 23, executor Luna 5. Total 148 testes. Os quatro checkers encontraram 5 schemas, 13 entradas, 9 observações, 13 decisões e, em ordem, 64/7/9/10 contraprovas. Os testes Luna incluem CLI com 50 liquidações, gate reprovado, prova modificada, conta/modo/manifesto de outra candidata, tentativa repetida com configuração nova, custo conhecido em HTTP 500 e JSON de saída inválido, custo desconhecido, timeout, recusa do gateway após prazo externo, integridade de fontes financeiras/congeladas e desvio de métrica. As contraprovas ampliadas de regeneração de prova, lacuna de selo e alteração durante publicação também passaram nos 14 testes do motor compartilhado R2.

O inventário temporário usou `git ls-tree` na base, comparou cada relatório a `git show BASE:caminho` e chamou `verify_report` sem imprimir textos, rótulos ou saídas de casos. Foram verificados 18 históricos warm, três observed-1.1, o golden R2 e o prefixo real R2. Para o protótipo anterior de relatório 1.0.0, o checker atual não possui perfil. Os bytes desse exemplo também foram comparados à base. Os 12 arquivos congelados e o ledger foram conferidos. As primeiras invocações por descoberta simples dos testes do adaptador Luna não resolveram o import histórico `transport`. A invocação por módulos acima passou nos 23 testes. O primeiro inventário de relatórios também tentou interpretar o protótipo 1.0.0, corrigido na divisão explicitada acima.

## Reproduzir o percurso completo de CLI

`test_cli_two_stages_and_replay` inicializa uma conta temporária com teto 10 e o saldo anterior simulado da tabela. Para cada etapa, chama `luna/execute.py run --mode fixture --stage ETAPA --config script/classification_comparison/luna/config-fixture.json --account ARQUIVO_TEMPORARIO --account-id ID --cap-usd 10 --dry-run --output DIRETORIO_NOVO`. Para a segunda etapa acrescenta `--development-gate CAMINHO_DA_PROVA`. Só na cópia sintética do manifesto habilita `enabled`, repete o comando com `--manifest CAMINHO --confirm-execution`, consulta `status`, verifica cada relatório e tenta repetir a etapa em outra configuração. As pastas temporárias são recolhidas ao terminar. O percurso reproduzível em um comando é

```sh
rtk proxy env PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna.test_round.LunaTest.test_cli_two_stages_and_replay
```

## Pré-voo real pendente

Cabe ao integrador revisar os bytes e reproduzir os testes. Antes de pedir execução paga, confirmar na fonte oficial e na rota Feita o modelo retornado, suporte efetivo ao esforço none e ao schema estrito, teto faturável em tokens e maiores preços para cada tipo de cache e para contexto longo. Arquivar respostas/documentos públicos e hashes. A confirmação de unidade deve justificar o cálculo bruto, inclusive eventual conversão de créditos por US$ 0,01. Conferir de forma autorizada o caminho, ID, saldo cumulativo e pendências da conta histórica. Só depois propor autorização financeira explícita da execução, com limite de seis chamadas de development e 44 condicionadas ao gate real. Um evento técnico interrompe a etapa.

Exercício para reprodução local: rode o teste do fluxo CLI e confira por que quatro controles têm bypass e um é injetado. A diferença entre os 49 registros de entrada da etapa final e suas 44 chamadas aparece no inventário do plano.
