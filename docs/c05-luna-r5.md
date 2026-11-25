# Avaliação offline da Luna com evidência

O perfil dedicado `observed-total-luna-r5` usa protocolo 1.5.0 e relatório 1.6.0. Cada caso elegível tem uma tentativa e uma única chamada. O adaptador retorna o envelope privado 1.0.0 com a observação IPC 1.1.0 e a auditoria dos campos pedidos. O avaliador verifica a citação e a decisão da política congelada contra o insumo original. O hash e o replay atestam essa correspondência. A qualidade da classificação exige comparação com os rótulos do protocolo.

A política ativa é 2.1.0, sobre o adaptador 2.0.0. O freeze original 2.0.0 precedeu o acesso de B ao pacote final. A revisão 2.1.0 aconteceu após esse acesso e se baseou exclusivamente nas quatro escolhas positivas de desenvolvimento e em casos sintéticos comunicados aos novos autores. O conjunto final permaneceu congelado. [Registro da revisão e dos hashes](evidencias/c05/r5-candidata-v2/candidate-freeze.json)

## Reprodução com transporte simulado

A partir da raiz do checkout, execute os comandos abaixo. O teste do CLI cria diretórios temporários e uma conta SQLite exclusiva de fixture, prepara os manifestos das duas etapas, executa o desenvolvimento, verifica o gate e o selo e confere o recibo final. Qualquer falha do gate bloqueia a autorização da etapa seguinte.

```sh
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-r5
rtk proxy env -u FEITA_API_KEY PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna_r5.test_round
```

No desenvolvimento, o simulador propõe os códigos com os relatos de desenvolvimento como citação e usa abstenção nos casos previstos. A candidata aplica o mesmo veto de produção. No final, o simulador devolve abstenção explícita em todo campo solicitado, independentemente do gabarito. Um lote de desenvolvimento tem seis chamadas. Um final autorizado tem 36 relatos e 13 controles, com 44 chamadas, uma observação de controle injetada e quatro entradas sem tentativa. As métricas reais de latência ficam sem medição em fixture, com elegibilidade `inconclusive`.

## Conferência de um lote salvo

`inputs.jsonl` contém a projeção autorizada. `observations.jsonl` e `decisions.jsonl` registram as escolhas e sua aplicação. `luna-evidence.jsonl` guarda uma linha por observação da candidata, na ordem do plano, inclusive quando uma falha observada precede o POST. O controle injetado não tem envelope da candidata. Em execução real, o processo principal guarda o tempo medido no evento de conclusão. Esse tempo inclui o recebimento, a validação e o replay.

O relatório vincula caminho, hash, contagem e versão do stream de evidências. O recibo de desenvolvimento ou final compromete tanto o relatório como a evidência. O selo privado junto à conta permite detectar a substituição conjunta dos arquivos e dos hashes. Um prefixo tem inventário e replay próprios e requer o registro de interrupção. Verifique um relatório público com o primeiro comando abaixo. Para reproduzir a prova final contra a conta sintética original, use o segundo na mesma revisão do executor, substituindo os caminhos e o identificador da conta.

```sh
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-r5 --report CAMINHO/report.json
rtk proxy python3 -B script/classification_comparison/luna_r5/execute.py verify-final \
  --mode fixture --stage final --config script/classification_comparison/luna_r5/config-fixture.json \
  --account CONTA_FIXTURE --account-id ID_DA_CONTA --cap-usd 10 \
  --development-gate DESENVOLVIMENTO/development-gate.json --output FINAL
```

Para acompanhar um caso, compare o primeiro `id` candidato do desenvolvimento nos três streams. Verifique quais campos o canal forneceu, onde a citação começa, qual foi o veredicto e quais campos foram aplicados na decisão. Faça os exercícios de adulteração em uma cópia temporária.

## Execução e histórico

O pedido limita a saída a 384 tokens. A reserva financeira usa os limites faturáveis confirmados e as maiores tarifas aplicáveis, incluindo cache. O valor original da resposta é conciliado em decimal. Custo desconhecido ou falha técnica interrompem a etapa. O caminho real mantém a conta global anterior, o teto cumulativo de USD 10 e a exigência de manifesto, configuração e autorização próprios. O exemplo real distribuído mantém a confirmação de tarifa e limites desativada.

O checker lê contratos e streams no checkout. O compromisso do plano inclui o hash do executor, a revisão e a conta. Para auditar um plano R2/R3/R4 anterior, confira seus arquivos inalterados e compare os hashes das fontes executáveis com os blobs Git da revisão registrada. Um manifesto de outra rodada ou revisão não autoriza o novo perfil.
