# C05-R4 · Instrução de revisão da Luna

A R4 está preparada para execução offline. O teste da CLI percorreu seis
chamadas sintéticas de desenvolvimento e 44 finais, com 50 reservas liquidadas
em uma conta temporária. O desenvolvimento retornou `fixture_ready`. O relatório
final registrou elegibilidade `inconclusive` e p95 `unmeasured`. A qualidade da
Luna R4 continua sem medição. O gasto real desta preparação foi zero.

O perfil `observed-total-luna-r4` usa instrução 1.2.0, protocolo 1.4.0,
relatório 1.5.0 e IPC 1.1.0. Mantém o modelo `openai/gpt-5.6-luna`, a política
1.1.0, o adaptador e o transporte da R3, com uma tentativa por caso. Os critérios
e os 36 relatos finais são os originais da R2, com zero aprovações humanas
individuais no conjunto final. O manifesto e o selo de desenvolvimento vinculam
a conta, a candidata e a etapa. A aprovação da R4 cobre preparação offline.
[Protocolo](planejamento/classificacao-comparativa/r4/protocol.json) ·
[Congelamento](evidencias/c05/r4-instrucao/candidate-freeze.json) ·
[Aprovação](evidencias/c05/r4-instrucao/offline-approval.json)

Os 16 relatos novos servem para diagnóstico de desenvolvimento. Duas
rotulações por IA concordaram em 16/16 casos e 18/18 campos, com zero aprovações
humanas e zero chamadas à Luna. O autor da instrução trabalhou sem ver esses
pares e o final. O integrador rotulou os pares às cegas após o commit da
instrução e antes do registro formal de congelamento, sem fornecer retorno ao
autor. Os 16 relatos ficam fora das duas etapas oficiais. Executá-los no modelo
exigiria autorização específica para um experimento separado.
[Comparação cega](planejamento/classificacao-comparativa/r4/diagnostico/blind-comparison.json)

## Reproduzir com uma conta temporária

Na raiz do checkout, os comandos abaixo verificam o exemplo de relatório e
percorrem as duas etapas pela CLI. O teste cria a conta temporária, planeja cada
etapa, habilita somente os manifestos sintéticos gerados, confere a prova e o
extrato e remove os arquivos ao terminar.

```sh
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-r4
rtk proxy env -u FEITA_API_KEY PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna_r4.test_round.R4Test.test_cli_two_stages_and_replay
```

O último registro público da conta histórica mostra US$ 0,02869232 acumulados
sob teto global de US$ 10, com 56 reservas liquidadas e zero pendências. Essa
conta ficou fechada durante a preparação R4. O exemplo de configuração real
aguarda verificação de tarifas, limites e unidade de custo. Um futuro ensaio
pago dependerá de pré-voo privado, nova autorização e uso da conta existente.
A etapa final depende de aprovação e selo da etapa de desenvolvimento da
própria candidata, no mesmo modo e conta.
[Registro financeiro da R3](c05-luna-resultado.md)

**Exercício.** No teste acima, encontre os 36 casos finais e os 13 controles.
Quantos controles precisam do adaptador para que o total seja 44 chamadas?
