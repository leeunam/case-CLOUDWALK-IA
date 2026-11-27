# Validação e limites

Resumo dos aceites registrados no snapshot [`e422db3`](https://github.com/leeunam/case-CLOUDWALK-IA/tree/e422db3ea6efddc8835036ce2095c48143d81516). As medições descrevem a capacidade observada no ambiente de teste.

Os comandos para rodar a demo e as suítes estão no [README](README.md).

## Carga, recuperação e chat — F08

A matriz usou seis rodadas isoladas: **5 minutos a 5 novos atendimentos por segundo** em cada rodada (1.500 entradas), com dois minutos de observação posterior. Três rodadas tiveram uma parada programada de 30 segundos no Kafka. As 9.000 entradas iniciais foram aceitas com HTTP `202`; p95 de aceite variou entre 154 e 241 ms.

Nas rodadas interrompidas, os consumidores voltaram e o backlog chegou a zero, mas **208 turnos aceitos expiraram sem resposta**: 200 primeiros turnos e 8 segundos turnos. Outros 37 segundos turnos planejados não foram enviados porque faltava a primeira resposta. A reconciliação registrou expiração dos prazos sem perda irreversível ou efeito duplicado confirmados. A matriz, após as correções R01/R02, passou nas três rodadas sem parada e reprovou nas três com parada. A conclusão é que drenagem do backlog, sozinha, não garante resposta ao cliente dentro do prazo.

O ensaio separado de Action Cable confirmou **100/100** conexões simultâneas e 300 mensagens aceitas. No alvo de 1.000, confirmou pico de **486** e aceitou 1.455/3.000 escritas previstas; houve timeouts ao abrir sessões e o worker atingiu o limite local de memória. O alvo de 10.000 foi interrompido no início da rampa, com 17 confirmações.

Evidência, denominadores, metodologia e critérios para repetir: [relatório F08](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/f08.md), [referência inicial](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/evidencias/f08/referencia-inicial/README.md) e [referência complementar](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/evidencias/f08/referencia-complemento/README.md). A reprodução da carga está em `script/load_testing/`; o ensaio de recuperação controlado, em `script/kafka_recovery/`.

## Classificação SetFit R1 — SF2

Foram preparados **360 relatos sintéticos**: 150 para treino, 90 para escolher a regra de revisão e 120 reservados ao teste final. Categoria e prioridade usam especialistas separados. A política R1 congela os limiares de score em 0,95 para categoria e 0,70 para prioridade, com margem zero. Score baixo, conflito ou resultado inválido leva o atendimento à revisão.

O teste independente aplicou a política uma vez aos 120 casos e cinco controles. **Passou nos 10 critérios.** Entre os 96 casos classificáveis, 69 foram concluídos automaticamente: 68 corretamente e um com prioridade incorreta. A categoria aplicada acertou **40/40** e a prioridade, **47/48**. Os 24 casos que exigiam revisão foram todos revisados; não houve conclusão indevida nesses casos. Houve 51 revisões ao todo (24 esperadas e 27 entre os classificáveis). Os 17 casos urgentes foram reconhecidos pelo rótulo bruto; 13 receberam prioridade urgente e quatro foram encaminhados à revisão. O p95 do adaptador foi **71,96 ms**; esse número exclui espera na fila, HTTP Rails, Kafka e tempo visível ao cliente.

O segundo auditor reconstruiu a avaliação e produziu auditoria idêntica em bytes. O pacote R1 aprovado foi integrado no fluxo local e reproduzido em clone limpo. O ensaio usou relatos sintéticos. Fontes: [protocolo e decisão](https://github.com/leeunam/case-CLOUDWALK-IA/tree/e422db3ea6efddc8835036ce2095c48143d81516/docs/planejamento/classificacao-comparativa/sf2), [resultado final independente](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/evidencias/c05/sf2/final-r1-01/README.md), [aceite integrado C06](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/evidencias/c06/aceite-integrado/README.md) e [reprodução C07](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/c07.md).

## Isolamento por marca — F10

A matriz pública executou **36/36 verificações** na listagem, detalhe, histórico, painel e assinatura Action Cable. Bia acessou Aurora; o caso Horizonte ficou fora da lista dela, retornou 404 genérico no detalhe/histórico e teve a assinatura WebSocket rejeitada. Cris e Alex acessaram as duas marcas. O responsável também confirmou no celular, em dados móveis, o acesso permitido de Bia à Aurora, o bloqueio de Bia à Horizonte e o acesso de Cris ao mesmo caso Horizonte. O aceite funcional também percorreu conversa, handoff humano, resposta, resolução e recarga do histórico.

Esse aceite usou fixture de classificação e atendente mock. A prova de marca e as limitações estão no [aceite integrado F10](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/f10-aceite-integrado.md), com [observações JSONL da matriz](https://github.com/leeunam/case-CLOUDWALK-IA/tree/e422db3ea6efddc8835036ce2095c48143d81516/docs/evidencias/f10/aceite-integrado).

## Atendente experimental — E01

E01 foi um **piloto isolado**, com GPT-5.6 Luna pela Feita e conhecimento fictício separado por marca. A matriz revisada passou em nove verificações técnicas em seis conversas, nove turnos, duas marcas e três canais simulados. A primeira candidata passou em 4/5 e foi reprovada por proposta inválida; essa falha foi mantida no histórico. A revisão da geração produziu um novo ensaio, que passou em 9/9. As 14 chamadas acumuladas reportaram US$ 0,00508345; o ledger registrou US$ 0,1500054 em provisões conservadoras e zero reservas pendentes, dentro do teto aprovado de US$ 1.

A Luna foi desligada ao final do ensaio. A demonstração pública usa o mock com canais e conhecimento sintéticos. Consulte [resultado e limites do E01](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/evidencias/e01/README.md), [conversas aprovadas](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/evidencias/e01/piloto-20261126/conversas.md) e [aceite final](https://github.com/leeunam/case-CLOUDWALK-IA/blob/e422db3ea6efddc8835036ce2095c48143d81516/docs/evidencias/e01/piloto-20261126/aceite-final.json).

## Localização das reproduções

Os relatórios completos e as reproduções ficam organizados por finalidade:

- Robustez e cenários de falha: `script/resilience/`.
- Recuperação Kafka: `script/kafka_recovery/`.
- Carga e conexões: `script/load_testing/`.
- Isolamento de acesso: `script/access_isolation/`.
- Aceite da classificação integrada: `script/classification_acceptance/`.
- Validação da demonstração reproduzível: `script/demo_validation/`.
- Piloto do atendente experimental: `script/agent_pilot/`.
- Fluxo de resposta do agente e atribuição humana: `script/check_agent_flow.py` e `script/check_human_assignment.py`.

As verificações nesses diretórios têm custo e pré-requisitos diferentes. Leia o roteiro correspondente antes de executar; testes de carga não devem concorrer com a demonstração local.
