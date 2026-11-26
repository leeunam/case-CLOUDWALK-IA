# SF2-FINAL-R1 · revisão independente das correções

**SPEC aprovada. QUALITY aprovada.** Os três achados P1 da revisão ampla foram atendidos. O diff da correção trouxe oito módulos e quatro arquivos de testes em `qualification_r1/`. Nenhum novo achado importante foi identificado nesse intervalo. O digest revisado da preparação pública é `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a`.

| Identificação | Valor |
| --- | --- |
| Tarefa | SF2-FINAL-R1, reavaliação da rodada consolidada |
| Base | `e1df85ee737d77a5698e9f4735f1a9aaf908cfed` |
| HEAD | `486d55c76d6a2436826364f01057dc0436247216` |
| Branch | `feat/sf2-final-ajustes` |
| Worktree | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-ajustes` |

## Veredito por achado

| Achado | Veredito | Evidência de implementação e regressão |
| --- | --- | --- |
| P1 · SIGINT antes da publicação do selo | **ADDRESSED** | Em `runner.py`, `_supervise` mantém o registro de SIGINT durante o fechamento completo. O trecho preemptivo termina com a coleta. As unidades, o journal, o selo e seu diretório pai são sincronizados antes de encaminhar uma interrupção tardia ao recibo externo. A fixture em `test_corrections.py` injeta o sinal em seis pontos da limpeza, materialização, publicação e sincronização. Ela confere os sete tempos válidos, o digest do selo, os dois relatos e cinco controles auditáveis, o resultado inconclusivo e um único lançamento. Outra fixture preserva a causa de uma falha anterior no segundo relato e a interrupção posterior do fechamento. |
| P1 · raiz temporária herdada do ambiente | **ADDRESSED** | O ponto de entrada `cli.main` fixa `tempfile.tempdir` em `/tmp` e substitui os candidatos de ambiente presentes antes de interpretar os argumentos. Os snapshots de fontes, dependências, histórico, pacote e leitura futura da custódia também especificam a raiz. A fixture `test_first_temporary_lookup_and_snapshots_ignore_all_environment_candidates` começa com o cache de diretório temporário vazio e observa o primeiro uso implícito e o explícito, com zero operações no destino fictício. |
| P1 · links nas fontes históricas e no pacote | **ADDRESSED** | O bootstrap abre a raiz do checkout por descritor. As fontes, os papéis históricos e os membros do pacote usam aberturas de arquivo regular com recusa de links em cada componente. A enumeração classifica entradas com seguimento de links desativado. O verificador histórico recebe cópias locais dos papéis previstos, e o consumidor do pacote recebe os bytes copiados e conferidos pelo hash. As fixtures de `test_public_io.py` cobrem redirecionamento do arquivo e do pai, entrada extra de arquivo ou diretório, troca do pai após enumeração e consumo dos bytes anteriores a uma alteração na origem. O check independente percorreu os papéis e o pacote públicos reais. |

As regressões são evidências do autor, que registrou **32 testes aprovados em 7,736 s**. Nesta revisão li as mudanças e as asserções correspondentes. A verificação de execução independente ficou restrita ao único check público solicitado.

## Check independente e cópias públicas

A partir da worktree congelada, executei uma vez:

```sh
rtk proxy /usr/bin/time -f 'elapsed_s=%e maxrss_KiB=%M' /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python -I -B -S /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-ajustes/script/classification_comparison/setfit_sf2/qualification_r1/cli.py check --release /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-final-ajustes/script/classification_comparison/setfit_sf2/.cache/qualificacao-r1-01/release --expect 1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a
```

```text
1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a
elapsed_s=7.53 maxrss_KiB=515120
```

Código de saída **0**. A checagem pública recompôs o congelamento com o interpretador pinado e a validação por bytes. O tempo de 7,53 s mede esse comando.

Com a biblioteca padrão, comparei as quatro cópias em `final-fix-publico/` com os respectivos originais e conferi os três vínculos do recibo, o comando, o commit aceito e o digest integral das métricas de paridade `86825eebee11a7815c337f99b96b841de32da4f2c45bdfe85a879adb09d157e4`. Essa verificação saiu com código 0.

| Documento | SHA-256 verificado |
| --- | --- |
| release.json | `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a` |
| config.json | `fb6613573c5fa02322cf14ce1b8b576c0daa30138cd6bcf46215b443b7929dac` |
| command.json | `5b81d96adcca66e2920fadcb5361fcf65dbf743c60d6d6463289dbf2388e4a8c` |
| freeze.json | `41c25a53b46f9928fd92252caf6249a545336c9b4d1e5da49787b35a906fff5a` |

## Limites do aceite

A revisão aceita a preparação pública nesse commit e digest. Os 120 finais continuam fechados. A confirmação do nome de inventário e dos quatro papéis pela custódia, a autorização expressa do digest e a execução independente permanecem pendentes. A inferência, seus gates, a eventual adoção e C06/C07 pertencem às etapas posteriores. Nesta revisão não houve consulta à custódia ou aos marcadores reais, carga de modelo, nova execução da suíte ou modificação da worktree congelada.
