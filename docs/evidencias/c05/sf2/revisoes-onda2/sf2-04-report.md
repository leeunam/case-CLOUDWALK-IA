# Entrega SF2-04

**DONE** · Branch `feat/sf2-avaliador` · Worktree `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-avaliador`. Base `1f55d316f29afe7a749317ce136ebde28c2991be`. Commit `ad3a8ffc312d076205c47c2323be35a6d804a11f`. Worktree limpa após o commit, sem merge ou push. O esclarecimento da interface em `05d8799` foi consultado pelo blob confirmado.

## Entrega

O avaliador usa o contrato independente de 00. Um novo worker recebe apenas entradas projetadas por JSONL. O coletor aguarda o READY sem aquecimento, preserva a resposta original e separa o tempo do worker da duração externa medida de antes da projeção até a auditoria da decisão. O supervisor POSIX impõe 5.000 ms por tentativa. Incorreção parcial, identidade divergente, frame inválido, score inválido, falha de processo ou timeout interrompem a execução e ficam registrados. Controles de canal completo/inválido e de máscaras isoladas/dupla são observações adicionais.

Na validação, um recibo prévio fixa política dos menores cortes em ambos os campos, argv, fontes, pacote e dados. O replay consome os scores auditados da coleta única. Matriz, precisão, recall, F1 e suporte descrevem escolhas brutas. Acertos aplicados, revisões, cobertura total/correta, veto de não urgente sobre urgente e gates usam os denominadores do protocolo. A tabela contém 225 políticas e linha de base argmax separada. A latência diagnóstica da validação é a da coleta.

O freeze reaudita originais, controles, scores, relatório e vencedora. Seu `files.command` vincula o comando definitivo, fontes do avaliador, política de coleta, previsões originais, journal, scores, recibo e tabela. O acesso reservado requer digest do recibo de freeze e um registro exclusivo de exposição na validação e na liberação. A execução usa um worker novo e sela previsões/tempos antes da auditoria das métricas. O auditor exige o digest do recibo de execução. Casos sem resposta válida e IDs nunca tentados ficam identificados separadamente.

## Verificações executadas

- Dois testes focados iniciais em módulos distintos: executadas a suíte matemática/transporte então com 5 testes (0,706 s) e a de fluxo com 1 teste (4,774 s), ambas aprovadas.
- Suíte pertinente com os quatro módulos abaixo: 23 testes em 11,318 s, todos aprovados. O teste matemático adicional de matriz assimétrica e não urgente aplicado sobre gold urgente passou isoladamente em 0,003 s. Total de 24 testes distintos verificados. A verificação final de whitespace do diff passou depois de retirar linhas vazias no fim de arquivos.
- O teste de fluxo usa apenas fixtures numéricas em diretório temporário. Confirmou a diferença entre política de coleta e vencedora, 17/17 urgentes brutos versus 16/17 aplicados na fixture final, ausência de relatório final antes do selo, recusa de abertura após alteração do journal ou digest, recusa de métrica ausente, alteração das previsões e repetição da execução. Outro teste fixa durações sintéticas para verificar posto 114 e a fronteira exata 3.000/3.001 ms. As falhas de transporte e o timeout foram exercitados com processos reais de fixture.

```sh
sf2=script.classification_comparison.setfit_sf2
rtk proxy python3 -B -m unittest -v "$sf2.contracts.test_contracts" "$sf2.contracts.test_artifacts" \
  "$sf2.evaluation.test_evaluation" "$sf2.evaluation.test_workflow"
rtk proxy python3 -B -m "$sf2.evaluation" --help
```

## Recibo numérico de reprodução

Foi criada uma segunda fixture numérica com o helper `numeric_package` do teste de fluxo e executados somente `validate` e `freeze`. A pasta temporária é `/tmp/sf2-04-numeric-ihpnwtd9`. A coleta usou (0,5; 0) nos dois campos. A vencedora usou (0,6; 0) na categoria e (0,5; 0) na prioridade. 180 das 225 políticas foram elegíveis para esta fixture. O journal tem 90 tempos externos de narrativas, mais os controles. P50 de 1,322 ms e p95 de 2,906 ms descrevem apenas o worker numérico local nessa coleta.

| Artefato da fixture | SHA-256 conferido |
| --- | --- |
| Política de coleta | `66a2915852b684e29278b2e2d5f131186d50133a594ffb68817136fa6530d89e` |
| Previsões originais | `85c3230ae964f8d90368435dbee0c22b24e2e1645b64b5a19b35c77bd2ad975f` |
| Journal de tempos | `66297cef4762107c5edc545f2abdacb648edc724018288f4786ba801be4c48a1` |
| Scores derivados | `76ee8ee170f9f56df4a9e305fc69997000eda5bf051f455227444be23cec1b7a` |
| Tabela e argmax | `c0953d240e7ab88add2a7151b86d0205de7f22d03351fc1ea7a27f84c753e5d1` |
| Política vencedora | `b6cf2de46fc299c8e7c27989837a43cabaa39fdf983a59e007f2db8720bc4d99` |
| Descritor de comando | `88ab2ee0f3c134ef08356d6cf80417bd9c04061e0b9636ff67c611339d86b90a` |
| Freeze | `f30ee3279eaa37fca148f8a33da011b85bad91d514d2c5c5331dde0fe89d7ed7` |
| Recibo de liberação | `f137945a585cba42392944d3d2ce84376b5c7ae2d5f7c89b0db11063d869bbda` |

O README do módulo descreve o formato de configuração, os quatro comandos e o contrato dos recibos. A execução real é responsabilidade de 05. A integração do worker e do extrator de 03 com 04 fica para o integrador. Esta entrega não envolve treino, calibração dos relatos de pesquisa, acesso ao final reservado, chamada a classificador externo, consulta a segredos/finanças ou mudança na aplicação.

## Limites e exercício

CPU é o maior uso observado do processo do worker em amostras de 50 ms no Linux, e memória é seu VmHWM. Tempo de treino e download e a atestação de chamadas externas vêm do recibo do operador. A custódia dos caminhos, artefatos e digests confiáveis continua sendo uma responsabilidade externa. Aprovação da fixture demonstra a implementação dos cálculos e do fluxo.

Leia o teste `test_applied_and_raw_urgent_have_distinct_numerators`. Encontre o caso com categoria insuficiente e prioridade urgente na máscara dupla. Confira o rótulo bruto de prioridade, os complementos vazios e a diferença de um caso entre os dois numeradores de urgência.

## Correção 1 após revisão

SF2-04, base da correção `ad3a8ffc312d076205c47c2323be35a6d804a11f`, commit local `3b5b12918799ebe734e153799b1a9470896296cb`. Mesma branch e worktree, limpas após o commit. Aguardando re-revisão do diff e integração pelo responsável. O recibo numérico da seção anterior pertence à entrega inicial.

| Achado | Mudança e verificação |
| --- | --- |
| Resposta anterior ao envio | O supervisor verifica a sobra da leitura anterior e observa simultaneamente stdout e stdin antes de cada escrita. Uma linha completa antecipada e seus primeiros 19 bytes, tanto após READY quanto após a primeira decisão, interromperam o ensaio. Ficaram zero e uma observação, respectivamente. Em um teste adicional, um único byte chegou ao pipe depois que READY já tinha sido lido. O supervisor recusou a saída e nenhum byte da próxima requisição chegou ao destinatário. |
| Catálogo efetivo | A projeção, a auditoria e a grade recebem o catálogo decodificado dos bytes do inventário aprovado. O pré-voo e a reauditoria conferem SHA da cópia selada, bytes da fonte do contrato e conteúdo do catálogo carregado em memória. A fixture verificou recusa antes de iniciar o worker quando a descrição em memória mudou, recusa do freeze com um espaço extra apenas na fonte local e recusa de abrir o inventário reservado quando a descrição mudou após um freeze válido. |
| Interrupção durante a persistência | A decisão validada e a duração observada ficam preparadas antes de escrever. Na recuperação, o executor confere o prefixo e acrescenta os bytes faltantes. O teste injetou KeyboardInterrupt após a gravação do frame e imediatamente após a gravação válida do journal. Nas duas execuções, o auditor encontrou exatamente um frame original, um registro válido com a medida capturada antes da interrupção, 119 IDs sem tentativa e parecer inconclusivo. Não houve repetição de inferência. |
| Aplicação parcial real | O worker de teste recebeu máscara dupla com categoria em revisão e prioridade bruta urgente aceita. A fixture aplicou erroneamente só a prioridade. O executor preservou o frame recusado no registro de interrupção, obteve zero decisões aceitas, não iniciou o replay e produziu parecer inconclusivo. |

Comandos executados a partir da worktree:

```sh
ev=script.classification_comparison.setfit_sf2.evaluation
rtk proxy python3 -B -m unittest -v "$ev.test_evaluation.TransportTest"
rtk proxy python3 -B -m unittest -v "$ev.test_workflow"
rtk proxy python3 -B -m unittest -v "$ev.test_evaluation.MathTest"
rtk proxy python3 -B -m unittest -v "$ev.test_evaluation.TransportTest.test_original_decisions_timeout_and_protocol_failures"
rtk proxy git diff --cached --check
```

Foram aprovados 4 testes de transporte em 1,652 s, 2 de fluxo em 7,073 s e 5 matemáticos em 0,234 s. Após explicitar a asserção de que a aplicação parcial bloqueava o replay, esse teste específico passou em 0,604 s. Total de 11 testes distintos do avaliador. O diff passou na verificação de whitespace. Os 16 testes do contrato, inalterado, foram verificados na entrega anterior. Estas verificações usaram somente processos e dados de fixture. A supervisão atesta a ordem dos bytes que pôde observar no transporte. Uma perda definitiva do disco ou encerramento forçado de todo o executor excede a recuperação de interrupções capturáveis verificada aqui.

## Correção 2 após o QA combinado

SF2-04, branch `feat/sf2-avaliador` na worktree `.worktrees/sf2-avaliador`. A branch avançou por fast-forward para a base integrada `237df80b4d27229fe79456f943cc11dc2b31f066`. A concretização de interface foi consultada no commit `c910ba83fa8b03f979329da3931fe727e488ce98`. Correção em `2a24f0d0ed6b29d2263450ddeb416af19a49111c`, com três arquivos de 04 e worktree limpa. A re-revisão desse diff e a repetição focal do QA são os próximos marcos do integrador.

O pré-voo e a reauditoria verificam o contrato `componentIndex`, a segurança dos caminhos relativos à raiz e os SHA-256 atuais de cada membro. Conferem a cobertura dos nomes contra o inventário de treino congelado de 03 acrescido de `adapter/__main__.py`, e contra o inventário produzido pelo helper de 03 no checkout efetivo. A verificação direta dos membros precede o import desse helper. O digest dos bytes do índice permanece em `capture.json` e `freeze.files.adapter`. O README descreve a geração do índice e a custódia da invocação. Os metadados das fixtures passaram a conter os índices completos.

O teste focal recria as fontes num espelho temporário. Cada comando usa um processo Python novo, com imports a partir do espelho e o mesmo índice, argv e configuração. A árvore íntegra admitiu a coleta e o freeze de fixture. Acrescentar um comentário em `adapter/decide.py`, `adapter/__main__.py` ou `contracts/__init__.py`, um por vez, produziu nove recusas verificadas, correspondentes a três arquivos por três fases. A coleta não iniciou o worker, o freeze recusou emitir liberação e a execução recusou criar saída ou recibos de exposição. Um caminho sentinela inexistente ocupou o argumento de inventário reservado. Também foram recusados ponto de entrada omitido, módulo removido simultaneamente do índice e da árvore, caminho com travessia e link simbólico para fora da raiz.

```sh
ev=script.classification_comparison.setfit_sf2.evaluation
rtk proxy python3 -B -m unittest -v "$ev.test_workflow.WorkflowTest.test_adapter_members_in_effective_checkout_before_capture_freeze_and_exposure"
rtk proxy python3 -B -m unittest -v "$ev.test_workflow"
rtk proxy git diff --check 237df80 HEAD
```

O teste focal inicial passou em 5,390 s. Na versão final, os três testes do módulo de fluxo passaram em 14,103 s, incluindo cobertura de fontes, catálogo e execução/auditoria numérica. O diff-check passou. Em uma checagem separada por Python 3.11, `adapter_digest` aceitou os 17 membros sem carregar Torch, SetFit ou Transformers. Esse índice temporário usou a serialização compacta da fixture e seu digest foi `f95802a920774335ee239ff7c2853a8b6470adb0893ec211f6c3a1847efcbae8`. Os hashes de índices dependem dos bytes da serialização. As suítes inalteradas de 00 e 03 ficaram fora desta rodada. Não houve mudanças nesses módulos nem execução sobre narrativas da pesquisa.

**Exercício.** No teste focal, observe que os bytes e o digest do índice não mudam durante as três mutações de código. Compare cada membro do índice com o arquivo no espelho e identifique a primeira fase que recusa iniciar o worker. A invocação e o ambiente que resolvem imports na árvore conferida continuam sob custódia do operador.
