# C01-L / C02-L · Latência total da classificação

Decisão do responsável em 23/11/2026: usar o tempo total que o usuário espera para a classificação. O teto inclusivo permanece **3.000 ms no p95**. Esta implementação é offline, anterior ao teste final, sem novas chamadas pagas, sem novos modelos e sem escolha de vencedor.

## Especificação vinculante

- O cronômetro monotônico C02 começa antes de validar a entrada e termina depois de validar a decisão. Inclui despacho, fornecedor, perguntas dos dois campos, parse e validação. A população é de relatos reais concluídos com observação válida do candidato, inclusive abstenção, saída inválida, erro e timeout com duração observada. Cada relato conta uma vez. Warm, cold e unknown entram igualmente. Controles e fixtures ficam fora.
- Download, inicialização antes de READY, carregamento e aquecimento local permanecem dados separados. O atendimento posterior pelo broker tem outra medição. O estado térmico continua informativo.
- p50/p95 pelo posto mais próximo: ordenar e selecionar `ceil(p*n)`, sem interpolação. Para 36 relatos, p50 é o 18º, p95 o 35º. Recalcular de modo independente no verificador a partir dos tempos autenticados pelos inventários, sem confiar no percentil autodeclarado. Falta de observação/tempo não vira zero ou 5.000 ms: mantém ausência e estado parcial/inconclusivo. A resposta válida de timeout inclui sua duração real. No teste final incompleto, a população prevista continua 36.
- Preservar os demais critérios e os denominadores aprovados: 29 classificáveis, mínimo 21 automáticos, 7 revisões obrigatórias, 6 urgentes omitidos/mínimo 5 reconhecidos, 48 alvos, acerto aplicado >=0,90 por campo, zero rebaixamento urgente/zero aplicação parcial/100% preservação. Timeout5s, tolerância de transporte250ms, concorrência1 e uma tentativa não mudam. Os critérios de evidência completa e de elegibilidade mantêm os demais requisitos, retirando apenas a exigência de warm para o perfil novo.
- Nenhuma mudança em bytes de dataset, split24/36, catálogo, rubrica, streams/schemas IPC1.1, controles e relatórios históricos. O protocolo1.0/SHAeb9b e seu lock/golden continuam verificáveis no caminho original. Não trocar hashes nos relatórios antigos nem recalcular suas conclusões com a régua nova.
- Introduzir protocolo de qualidade1.1 e perfil do relatório1.2, com IPC1.1 explicitamente declarado. Novo gate `observed_total_latency_p95_ms_max`; recusar presença de chave antiga no perfil novo, mistura de protocolo/schema e perfil autodeclarado não confiável. Registro fechado de perfis com hashes e caminhos. Seleção explícita por argumento para novas execuções, anotada em plano/invocação/prefixos/manifesto/relatório; APIs e comandos legados continuam reproduzíveis.
- Adaptadores Qwen/GLiClass preservam o IPC1.1 e não fazem novas inferências. A configuração e a autorização de C05 final terão passagem própria; o seletor de relatório não habilita gastos ou holdout. Desenvolvimento/fixtures e execuções incompletas nunca selecionam candidato.

## Tarefas e propriedade

1. **C01-L · contrato e verificação.** Branch `feat/latencia-total-contratos`, worktree `.worktrees/c01-latencia-total`. Dono de protocolo novo, schema de relatório1.2, golden/contraprovas novos, registro/locks, checker `script/check_classification_contracts.py`, regressões de contrato e documentação de perfil. Preservar arquivos fonte históricos. Registrar hashes históricos para compará-los depois. O novo verificador deve conferir tempos/estados/população e percentis, inclusive desenvolvimento e parcial. Checagens legadas5schemas/64contraprovas/11regressões continuam passando. Não editar common/metrics/run/journal nem adaptadores.
2. **C02-L · avaliador.** Só depois da integração C01-L aceita, em branch/worktree próprias informadas pelo integrador. Dono de common/metrics/run/journal, testes C02 e exemplos novos. Consumir o registro/contrato aceito, distinguir versão de relatório da versão de IPC, contar todas as durações observadas e preservar interrupção/prefixo/cobrança. Não criar schema concorrente nem modificar arquivos históricos/adaptadores.
3. **Integração.** Revisão independente por tarefa, correções e revisão ampla final; reproduzir dois perfis offline, verificar exemplos novos e históricos, atualizar C05/guia/estado. Testes construídos para p95/falhas ficam identificados como sintéticos e não são evidência de qualidade real de um modelo.

Enquanto C01-L implementa, outra frente somente leitura pode preparar vetores e inventário de compatibilidade. Não editar os mesmos arquivos em paralelo. O integrador fixa o commit-base após este plano estar commitado.

## Casos de aceite

- Mistura warm/cold/unknown com sucesso, abstenção, inválido, erro e timeout; um caso de dois campos = uma duração; controle de candidato muito lento não altera p95 dos relatos.
- p95 exatamente3.000passa;3.001falha, em n36. Um timeout de5.000 pode coexistir com p95de3.000 se for a 36ª posição. Tratar zero amostras, fixture, ausência de tempo, final abreviado e todos os relatos indisponíveis.
- Percentil adulterado, exclusão de unknown/falha, denominador incorreto, inclusão de controle, versões/chaves/protocolos/hashcaminhos cruzados são rejeitados.
- Report antigo conserva p95 aquecido; novo aceita unknown. IPCconfig/entrada/observação/decisão continuam1.1 no relatório1.2.
- Prefixos/interrupções mantêm observação válida tardia, cobrança pendente e fronteira durável. Nenhuma reentrega silenciosa ou artefato parcial decisório.
- Revalidar os 17 relatórios presentes sob protocolo1.0/contrato1.1 (11GLi,3Qwen,2C02,1golden) sem mudar seus bytes. Exemplo antigo decontrato1.0 permanece reproduzível no commit de origem.

## Exercício

Ordenar 34 tempos de1.500ms, um de3.000ms e um timeoutde5.000ms. Localizar p95 na35ªposição. Trocar3.000por3.001e conferir o gate, sem mudar o restante do experimento.
