# SF2-FINAL-R1/3 — QA de integração e liberação pública

A liberação pública tem SHA-256 `5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b`. O `freeze` emitiu o recibo e o `check` público reconstruiu a mesma liberação. Cinco testes passaram. O conjunto final permanece fechado. O aceite independente e a decisão do responsável sobre eventual exposição seguem pendentes.

## Identificação

| Item | Valor |
| --- | --- |
| Tarefa | SF2-FINAL-R1/3 |
| Base | `9b8f5127ae5e44c5287b824f2e46fb789f11f45b` |
| Commit de QA e commit aceito pela CLI | `31a055bcdae0c89c2bdb626ce4084e405a07be4e` |
| Branch | `feat/sf2-final-integracao` |
| Diretório de trabalho e cwd do comando | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao` |
| Única mudança versionada | `script/classification_comparison/setfit_sf2/qualification_r1/test_integracao_publica.py` |
| Ambiente | Python 3.11.13, `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python` |
| Proveniência histórica | Captura `4eb86a3282f94f32119042a0f6aa075e9f72960a`, fontes do replay offline `99cf2f33e1803838e33813d5c4ff46971181ce4e` |

O commit do teste precedeu a configuração e o congelamento. O Git informou árvore limpa após o commit e após a checagem. A worktree congelada deve permanecer nesse HEAD para reprodução.

## Integração exercitada

O subprocesso JSON recebeu a projeção de cada item e respondeu com o frame público correspondente ao ID. O teste usou a CLI de fixture existente, os bytes públicos das políticas e do manifesto e as implementações aceitas de `load_context`, `derive`, `verify`, supervisão e auditoria. A auditoria selada reconstruiu 90 decisões e cinco controles e retornou `inconclusive` para o ensaio final, que exige 120 relatos. A validação pública reproduziu integralmente a linha selecionada.

| Ensaio | Resultado observado |
| --- | --- |
| 90 relatos e cinco controles | SHA do frame e ID em todas as decisões, ordem dos tempos, mudanças de motivo e igualdade integral das métricas e dos gates |
| Atraso do derivador e do verificador | Em cada ensaio o callable real terminou e entrou na espera de 1 s. O prazo externo de 150 ms interrompeu o primeiro item no intervalo exigido de 140 a 900 ms. Auditor reconheceu zero decisões |
| SIGINT antes da publicação da segunda unidade | Primeiro tempo válido, segundo inválido, um relato auditável |
| SIGINT após a publicação da segunda unidade | Dois tempos válidos, dois relatos auditáveis, estado inconclusivo |
| Corrida sobre custódia temporária | Dois processos, dois recibos/destinos e o mesmo selo fictício. Uma única leitura registrada |
| Paridade por ID | O teste público adicional conferiu resultados individuais com o replay sobre scores arquivados, campos e motivos do bruto e todas as matrizes, razões, Wilson e gates |

Comandos a partir da worktree de QA.

```sh
rtk proxy /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python -B -m unittest -v \
  script.classification_comparison.setfit_sf2.qualification_r1.test_integracao_publica \
  script.classification_comparison.setfit_sf2.qualification_r1.test_exposure.Exposure.test_two_processes_different_releases_and_destinations_same_seal \
  script.classification_comparison.setfit_sf2.runtime_r1.test_public.PublicParityTests
rtk git diff --cached --check
```

```text
test_prazo_inclui_derivacao_e_verificacao ... ok
test_replay_integrado_de_90_relatos_e_cinco_controles ... ok
test_sigint_preserva_unidade_atomica_e_auditoria ... ok
test_two_processes_different_releases_and_destinations_same_seal ... ok
test_frames_por_id_e_metricas_completas_da_linha_selecionada ... ok
Ran 5 tests in 4.133s
OK
```

A checagem do diff terminou com código zero e sem diagnóstico.

## Paridade da validação

A seleção histórica teve 0/225 elegíveis na grade original e 9/45 na extensão. A política escolhida fixa categoria em τ=0,95, prioridade em τ=0,70 e ambas as margens mínimas em zero. O SHA-256 das métricas reconstruídas é `86825eebee11a7815c337f99b96b841de32da4f2c45bdfe85a879adb09d157e4`. A cópia legível por máquina em `task-3-publico/paridade.json` contém a linha completa com métricas, matrizes, valores por classe, F1 e todos os intervalos, além das observações do replay.

| Medida | Contagem | Intervalo de Wilson 95% |
| --- | --- | --- |
| Cobertura automática | 51/72 | 0.5949425733065095 a 0.8006194381116332 |
| Cobertura correta | 51/72 | 0.5949425733065095 a 0.8006194381116332 |
| Revisões | 39/90 | 0.3357657253124879 a 0.5363590247627558 |
| Revisão de categoria | 24/60 | 0.2856949053488255 a 0.5263394650795924 |
| Revisão de prioridade | 20/60 | 0.22729261523522679 a 0.459431335478803 |
| Conclusão indevida em revisão esperada | 0/18 | 0 a 0.17587922364665756 |
| Acerto de categoria aplicada | 32/32 | 0.8928208017449296 a 1 |
| Acerto de prioridade aplicada | 33/33 | 0.895730002457548 a 0.9999999999999999 |
| Urgente bruto | 12/13 | 0.6668604907890041 a 0.9862895787574433 |
| Urgente aplicado | 10/13 | 0.49743624053272506 a 0.9182047128150144 |
| Campos fornecidos preservados | 60/60 | 0.93982814785791 a 0.9999999999999998 |

Houve zero rebaixamentos de urgente, zero aplicações parciais e zero chamadas nos controles completo e inválido. Os nove gates de qualidade passaram. Nos 90 relatos, os motivos de categoria foram `{"accepted":36,"below_tau":15,"provided":30,"raw_review":9}` e os de prioridade `{"accepted":40,"below_tau":9,"provided":30,"raw_review":11}`. As decisões de campo que mudaram frente à captura passaram de aceite para `below_tau`. O restante preservou o motivo do frame.

| Controle | Resultado | Chamadas categoria / prioridade | Aplicação |
| --- | --- | --- | --- |
| sf2-control-complete | complete | 0 / 0 | vazia |
| sf2-control-invalid | review | 0 / 0 | vazia |
| sf2-control-blank-category | review | 1 / 0 | vazia |
| sf2-control-null-priority | review | 0 / 1 | vazia |
| sf2-control-omitted-both | review | 1 / 1 | vazia |

Numa medição adicional com o mesmo teste integrado e entradas públicas, o replay apresentou startup de 98.20 ms, p50 de 12.31 ms, p95 de 17.13 ms e máximo de 27.66 ms. Esses tempos incluem transporte da fixture e cálculo da decisão. A latência da inferência e o gate de p95 de 3.000 ms dependem de ensaio real.

## Recursos públicos e pacote

O disco da worktree tinha 11 GiB livres. O temporário local tinha 7,2 GiB livres, com 9,8 GiB de RAM disponíveis antes das cópias. Nas origens, `du -s -B1` mediu 29.519.872 bytes alocados no site-packages do venv, 1.715.654.656 no overlay SF1 e 975.687.680 no pacote. Esses tamanhos estimam o espaço necessário, incluindo entradas que o copiador pode omitir. O bootstrap usou diretórios temporários sob `/tmp`. O tempo e o pico de RSS da CLI estão na tabela a seguir.

O pré-voo conferiu um inventário fechado de 36 membros mais o manifesto. Abriu bytes dos encoders, cabeças e tokenizadores, verificou os SHA-256 e entregou a cópia verificada à conferência do manifesto. A etapa histórica de replay offline registrara `weights_verified_in_replay=false`. A conferência física dos pesos nesta etapa consta do recibo atual.

| Papel | SHA-256 |
| --- | --- |
| Manifesto do pacote | `224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872` |
| Manifesto do modelo category | `b989492b3623dc6015e97c5d8af975950a48ce72f489d467062e07fe6996a6c5` |
| Manifesto do modelo priority | `8a0224ad38fa45a902a58bc25c8dbcc4c9e9aff96ec50024dfe4a01c304bcab1` |
| category.encoder/model.safetensors | `21474caf9fdb4d7f4145ff1aa2aecc131e73baa235545bcc910bebefcfd77c5a` |
| category.head/logistic.joblib | `dfe395d06ea5d50baf3c349596bfdf3716b42bcd5c3ccea326578fa4ccb6769d` |
| category.tokenizer/tokenizer.json | `cad551d5600a84242d0973327029452a1e3672ba6313c2a3c3d69c4310e12719` |
| priority.encoder/model.safetensors | `5ab6115e779f6cea70e1166d0f724ef44dc9deb5f01a337a3b94eecc2ac09768` |
| priority.head/logistic.joblib | `1f82eec45d489939a4d748ae24328e993179e1b00499588fb1d39024ade22a93` |
| priority.tokenizer/tokenizer.json | `cad551d5600a84242d0973327029452a1e3672ba6313c2a3c3d69c4310e12719` |
| Binário Python carregado | `b000b16939f3c0e64b365ce6371046b77ca5df2845180c8005b24ccf7373dcd0` |
| pyvenv.cfg | `5f1382fe290f655c72d57ecb92dff21ebe55489ca92fd50cce9a52118c8ed5eb` |

Origem física do pacote público: `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-qualificacao/script/classification_comparison/setfit_sf2/.cache/qualificacao-01/training-02/package`. O freeze identifica 84 arquivos atuais, 28 papéis históricos, 19 vínculos da captura, 17 membros do adaptador, 74 campos de versões e 75 instalações de distribuições nas duas origens, com 27.357 membros de RECORD verificados e três .pth. Principais versões: Python 3.11.13, SetFit 1.2.0, Torch 2.12.0+cpu, Transformers 5.8.1, Sentence Transformers 6.3.0, scikit-learn 1.8.0, tokenizers 0.22.2, safetensors 0.8.0 e joblib 1.6.0. A configuração lista os diretórios originais e o freeze arquivado contém o inventário completo. O custo histórico de treinamento foi 913.684,54 ms. O pré-voo atual operou offline, com zero chamadas de classificação e sem iniciar o trabalhador do pacote.

## Freeze e check do executor de QA

```sh
rtk mkdir -p /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01
rtk proxy /usr/bin/time -f 'elapsed_s=%e maxrss_KiB=%M' /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python -I -B -S /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/qualification_r1/cli.py template --release /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release --run /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/final-run > /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/config.json
rtk proxy /usr/bin/time -f 'elapsed_s=%e maxrss_KiB=%M' /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python -I -B -S /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/qualification_r1/cli.py freeze --config /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/config.json --out /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release
rtk proxy /usr/bin/time -f 'elapsed_s=%e maxrss_KiB=%M' /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python -I -B -S /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/qualification_r1/cli.py check --release /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release --expect 5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b
```

A configuração e a liberação já existem. O revisor independente reproduz somente o último comando, recebendo o SHA externo e conferindo os bytes do recibo original.

| Etapa | Saída | Tempo de parede | RSS máximo da CLI |
| --- | --- | --- | --- |
| template | configuração JSON, saída zero | 8,45 s | 56.752 KiB |
| freeze | `5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b`, saída zero | 7,82 s | 517.404 KiB |
| check | `5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b`, saída zero | 7,47 s | 513.508 KiB |

Caminho do recibo original: `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release/release.json`. A cópia pública dos quatro documentos foi arquivada em `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.superpowers/sdd/sf2-final-r1-plano/task-3-publico`, junto à paridade. `sha256sum` produziu os mesmos quatro digests nas duas localizações.

| Documento | SHA-256 dos bytes |
| --- | --- |
| config.json | `449a2207d5e75ff56418ced863c83ff9d340b4978d073d8ba6bc4f9834a92837` |
| command.json (comando interno do worker) | `6d880923414fa6d6a8c7ee793872fb6740adf8ff5d3f5f4d270ba042f425bafd` |
| freeze.json | `7c311d9b9cb2ec48db3733a02e4885c78ca0b53f695c368157d0d53d6f77465c` |
| release.json | `5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b` |
| paridade.json (evidência adicional) | `8ec7806557bd0e8b4f841bed818671f4a22639804706ce502b16e9455f95001f` |
| Selo público do conjunto final usado como compromisso | `71bea26395321246ef00c4374465c6cd8bd3320252a7729429cfad5e3c2263a4` |


## Comando futuro condicionado

O array abaixo está escrito por extenso para revisão. O argumento `--custody` usa o basename **projetado** `private-inventory.json`. O resumo público confirma a pasta, e o selo confirma os nomes do arquivo de relatos e do arquivo de anotações. A referência conhecida a esse basename vem de uma fixture. O responsável pela custódia ou o handoff público ainda precisa confirmar o nome exato do inventário. A liberação identifica a configuração e o comando interno do worker. A futura autorização deve vincular, separadamente, inventário, quatro papéis, SHA da liberação, selo e ação de execução única. Caso o basename confirmado difira, o integrador deve atualizar este argv antes de solicitar autorização.

```json
[
  "/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python",
  "-I",
  "-B",
  "-S",
  "/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/qualification_r1/cli.py",
  "execute",
  "--release",
  "/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release",
  "--expect",
  "5c5aac6e1dcf00facadb2eafdd86adf97875ad8e9cdcc0e5169a51ce2eeade2b",
  "--custody",
  "/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.superpowers/sdd/conclusao-projeto/sf2-final/accepted/private-inventory.json",
  "--out",
  "/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-integracao/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/final-run"
]
```

O arquivo `task-3-publico/comando-futuro-projetado.json` conserva o mesmo array para o revisor. Nenhum argumento de custódia foi consultado no sistema de arquivos. A exposição única, a abertura do final, o carregamento de modelos e a inferência real permanecem pendentes de decisão específica após a revisão independente. O checksum não constitui autorização. Os resultados se limitam à validação pública que participou da seleção.

**Exercício.** Localize a decisão de `sf2-validation-001` no teste de paridade e confira como o score de prioridade 0,6313874585281872 passa do limiar original 0,50 para revisão pelo limiar 0,70. Compare essa decisão com os campos preservados e a aplicação vazia.

## Objeto completo de referência reproduzido

A igualdade conferida percorreu todo o objeto de métricas e todos os gates. Cada matriz é indexada por classe de referência e classe observada. Os campos `precision` e `recall` guardam numerador, denominador e intervalo de Wilson de 95%.

```json
{
  "eligible": true,
  "failed_gates": [],
  "gates": {
    "automatic_coverage": true,
    "category_accuracy": true,
    "control_calls": true,
    "nonurgent_on_urgent": true,
    "partial_applications": true,
    "preservation": true,
    "priority_accuracy": true,
    "raw_urgent": true,
    "wrong_expected_review": true
  },
  "metrics": {
    "applied_accuracy": {
      "category": {
        "denominator": 32,
        "numerator": 32,
        "wilson95": [
          0.8928208017449296,
          1
        ]
      },
      "priority": {
        "denominator": 33,
        "numerator": 33,
        "wilson95": [
          0.895730002457548,
          0.9999999999999999
        ]
      }
    },
    "applied_urgent": {
      "denominator": 13,
      "numerator": 10,
      "wilson95": [
        0.49743624053272506,
        0.9182047128150144
      ]
    },
    "automatic_coverage": {
      "denominator": 72,
      "numerator": 51,
      "wilson95": [
        0.5949425733065095,
        0.8006194381116332
      ]
    },
    "by_class": {
      "category": {
        "informacao_insuficiente": {
          "f1": 0.8421052631578947,
          "precision": {
            "denominator": 9,
            "numerator": 8,
            "wilson95": [
              0.5650002944233441,
              0.9801091123614551
            ]
          },
          "recall": {
            "denominator": 10,
            "numerator": 8,
            "wilson95": [
              0.49016247153664183,
              0.9433178485456247
            ]
          },
          "support": 10
        },
        "payouts": {
          "f1": 0.967741935483871,
          "precision": {
            "denominator": 15,
            "numerator": 15,
            "wilson95": [
              0.7961166989641514,
              0.9999999999999999
            ]
          },
          "recall": {
            "denominator": 16,
            "numerator": 15,
            "wilson95": [
              0.7167126242970108,
              0.9888806552353575
            ]
          },
          "support": 16
        },
        "pix": {
          "f1": 0.9444444444444444,
          "precision": {
            "denominator": 19,
            "numerator": 17,
            "wilson95": [
              0.6860591728889099,
              0.9706414397011297
            ]
          },
          "recall": {
            "denominator": 17,
            "numerator": 17,
            "wilson95": [
              0.8156818649911481,
              0.9999999999999998
            ]
          },
          "support": 17
        },
        "terminal": {
          "f1": 1,
          "precision": {
            "denominator": 17,
            "numerator": 17,
            "wilson95": [
              0.8156818649911481,
              0.9999999999999998
            ]
          },
          "recall": {
            "denominator": 17,
            "numerator": 17,
            "wilson95": [
              0.8156818649911481,
              0.9999999999999998
            ]
          },
          "support": 17
        }
      },
      "priority": {
        "advanced": {
          "f1": 0.8181818181818182,
          "precision": {
            "denominator": 10,
            "numerator": 9,
            "wilson95": [
              0.5958499732047616,
              0.982123786904927
            ]
          },
          "recall": {
            "denominator": 12,
            "numerator": 9,
            "wilson95": [
              0.4676946650664344,
              0.9110583316059453
            ]
          },
          "support": 12
        },
        "basic": {
          "f1": 0.8333333333333334,
          "precision": {
            "denominator": 12,
            "numerator": 10,
            "wilson95": [
              0.5519691377470267,
              0.9530348578161462
            ]
          },
          "recall": {
            "denominator": 12,
            "numerator": 10,
            "wilson95": [
              0.5519691377470267,
              0.9530348578161462
            ]
          },
          "support": 12
        },
        "informacao_insuficiente": {
          "f1": 0.8571428571428571,
          "precision": {
            "denominator": 11,
            "numerator": 9,
            "wilson95": [
              0.5230194380391561,
              0.948632310253915
            ]
          },
          "recall": {
            "denominator": 10,
            "numerator": 9,
            "wilson95": [
              0.5958499732047616,
              0.982123786904927
            ]
          },
          "support": 10
        },
        "intermediate": {
          "f1": 0.9166666666666666,
          "precision": {
            "denominator": 11,
            "numerator": 11,
            "wilson95": [
              0.7411670330319684,
              1
            ]
          },
          "recall": {
            "denominator": 13,
            "numerator": 11,
            "wilson95": [
              0.5776536898051747,
              0.9567418216419188
            ]
          },
          "support": 13
        },
        "urgent": {
          "f1": 0.8275862068965517,
          "precision": {
            "denominator": 16,
            "numerator": 12,
            "wilson95": [
              0.5050168346449122,
              0.8981793250878696
            ]
          },
          "recall": {
            "denominator": 13,
            "numerator": 12,
            "wilson95": [
              0.6668604907890041,
              0.9862895787574433
            ]
          },
          "support": 13
        }
      }
    },
    "confusion": {
      "category": {
        "informacao_insuficiente": {
          "error": 0,
          "informacao_insuficiente": 8,
          "payouts": 0,
          "pix": 2,
          "terminal": 0
        },
        "payouts": {
          "error": 0,
          "informacao_insuficiente": 1,
          "payouts": 15,
          "pix": 0,
          "terminal": 0
        },
        "pix": {
          "error": 0,
          "informacao_insuficiente": 0,
          "payouts": 0,
          "pix": 17,
          "terminal": 0
        },
        "terminal": {
          "error": 0,
          "informacao_insuficiente": 0,
          "payouts": 0,
          "pix": 0,
          "terminal": 17
        }
      },
      "priority": {
        "advanced": {
          "advanced": 9,
          "basic": 0,
          "error": 0,
          "informacao_insuficiente": 0,
          "intermediate": 0,
          "urgent": 3
        },
        "basic": {
          "advanced": 0,
          "basic": 10,
          "error": 0,
          "informacao_insuficiente": 2,
          "intermediate": 0,
          "urgent": 0
        },
        "informacao_insuficiente": {
          "advanced": 0,
          "basic": 1,
          "error": 0,
          "informacao_insuficiente": 9,
          "intermediate": 0,
          "urgent": 0
        },
        "intermediate": {
          "advanced": 0,
          "basic": 1,
          "error": 0,
          "informacao_insuficiente": 0,
          "intermediate": 11,
          "urgent": 1
        },
        "urgent": {
          "advanced": 1,
          "basic": 0,
          "error": 0,
          "informacao_insuficiente": 0,
          "intermediate": 0,
          "urgent": 12
        }
      }
    },
    "control_calls": 0,
    "correct_coverage": {
      "denominator": 72,
      "numerator": 51,
      "wilson95": [
        0.5949425733065095,
        0.8006194381116332
      ]
    },
    "nonurgent_on_urgent": 0,
    "partial_applications": 0,
    "preservation": {
      "denominator": 60,
      "numerator": 60,
      "wilson95": [
        0.93982814785791,
        0.9999999999999998
      ]
    },
    "raw_urgent": {
      "denominator": 13,
      "numerator": 12,
      "wilson95": [
        0.6668604907890041,
        0.9862895787574433
      ]
    },
    "review_by_case": {
      "denominator": 90,
      "numerator": 39,
      "wilson95": [
        0.3357657253124879,
        0.5363590247627558
      ]
    },
    "review_by_field": {
      "category": {
        "denominator": 60,
        "numerator": 24,
        "wilson95": [
          0.2856949053488255,
          0.5263394650795924
        ]
      },
      "priority": {
        "denominator": 60,
        "numerator": 20,
        "wilson95": [
          0.22729261523522679,
          0.459431335478803
        ]
      }
    },
    "wrong_expected_review": {
      "denominator": 18,
      "numerator": 0,
      "wilson95": [
        0,
        0.17587922364665756
      ]
    }
  },
  "policy": {
    "category": {
      "delta": 0,
      "tau": 0.95
    },
    "contract_version": "sf2-r1-offline/1.0",
    "priority": {
      "delta": 0,
      "tau": 0.7
    }
  }
}
```

