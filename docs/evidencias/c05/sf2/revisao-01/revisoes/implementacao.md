# SF2-R1 · Task 1

**Estado:** correção P2 implementada e testada com fixtures. Nova revisão independente pendente.

| Referência | Valor |
| --- | --- |
| Base da emenda | `290dee316c6fde2414f414dcfcb81a72b39daf18` |
| Commit da implementação inicial | `7ae98ff129ce9058f7ff1ec2c471bbdaafea8396` |
| Commit da correção P2 | `99cf2f33e1803838e33813d5c4ff46971181ce4e` |
| Branch | `feat/sf2-revisao-grade` |
| Worktree | `/home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-revisao-grade` |
| SHA-256 da emenda | `c3a6db8134f71491c1e743ddf6d57a400bba6449017b336e0a311c02f4eb07b3` |
| SHA-256 de `revision_r1/sources.json` na correção P2 | `f9199e3535f5504df2a1c9f11b317b526920d643a2653328fd5012f61eb8739e` |
| SHA-256 do inventário da implementação inicial | `f459a21a4fea1a78ab2b65c6df71a697dbb4666adb5d50ce8ff0cb4f7999475d` |

## Entrega

A função de replay extraída preserva os parâmetros, tipo de política e resultados da API original `select`. A CLI realiza a auditoria antes do replay, reconstitui as 225 políticas e a baseline e exige paridade de objetos e bytes. O contrato de categoria 0,95 restringe a extensão a 45 políticas. O ranking e os gates são os congelados da avaliação SF2. O arquivo de saída inclui as matrizes, suporte, intervalos, vetos, candidata ou seleção nula, estado do final, hashes e consumo. O ajuste foi proposto após observar a validação original.

O inventário contém 30 fontes e recursos. A CLI toma os dois digests esperados pela linha de comando, exige caminhos autorizados e verifica o conjunto completo das fontes executadas. A fonte histórica de seleção e os 17 membros do adaptador são conferidos na árvore histórica. Os módulos SF2 executam os bytes atestados em namespace exclusivo. A configuração arquivada tem o próprio hash verificado. A resolução de arquivos parte de papéis públicos e caminhos fixos. O treinamento original e a captura sustentam a proveniência dos pesos físicos. O replay usa os índices públicos e registra que não fez nova verificação dos pesos.

## Verificações reproduzíveis

A partir da worktree acima:

```sh
rtk proxy /home/inteli/Documents/projetos/case-CLOUDWALK-IA/.worktrees/sf2-treinamento/script/classification_comparison/setfit_sf2/.cache/verification/.venv/bin/python -B -m unittest -v \
  script.classification_comparison.setfit_sf2.revision_r1.test_replay \
  script.classification_comparison.setfit_sf2.evaluation.test_evaluation.MathTest
rtk git diff --cached --check
```

Resultado do comando de testes na configuração documentada: **11/11 passaram** em 7,051 s. O segundo comando passou sobre os sete arquivos selecionados antes do commit. A edição inicial do teste sobrescrevia a cópia de requirements do cenário sintético. O teste acusou o hash divergente, o construtor da fixture foi corrigido e a suíte final passou.

As seis verificações R1 abrangem:

- Captura e CLI ponta a ponta em fixtures de 90 relatos, cinco controles e 95 tempos. O harness inicia a CLI em interpretador isolado e bloqueia acesso ao final, pesos, rede, subprocessos e importação de modelos dentro do processo monitorado.
- Casos elegível e negativo com os códigos 0 e 1. O código 2 protege um destino existente e falhas de integridade. O diretório é reservado antes do primeiro corte novo e o resultado é publicado após escrita completa.
- Prova independente da fixture com seletor histórico em `sf2-qualificacao`. SHA-256 da grade `8e2187ca9227250d3ca0beb24ed25e366eecd31103b83771085c78aa3c94f4e7`; baseline `7e9449ea428276dd37c82d29a8f6722b5b2d0537616e42ec830ebc8a51dc402c`. Esses digests referem-se unicamente a relatos e vetores sintéticos.
- Paridade de 225 políticas e baseline, cortes únicos entre as 270, desempate entre elegíveis, ausência total de elegíveis, precisão no limite tau, margem igual ao delta, erro de vetor, veto da classe de revisão, atomicidade e preservação do canal.
- Recusa de adulteração de selo, frames, journal, scores, configuração, política, grade, fonte histórica/atual, inventário e emenda. As fixtures exercitam também um frame semanticamente inválido com selo recalculado, divergência dos scores, quota alterada, prioridade 0,95, manifesto incompleto e substituição de caminho.

Os cinco testes matemáticos do avaliador original também passaram. Foi executado apenas o subconjunto pertinente de regressão.

## Passagem ao executor

O README da CLI contém o comando e os argumentos da Task 2. O integrador deve obter os digests no commit aceito e o executor deve aplicar esse commit na worktree exclusiva. A saída única será `script/classification_comparison/setfit_sf2/.cache/revisao-01/result.json`. O diretório não deve existir no início da rodada.

A Task 1 não executou quaisquer políticas reais novas, processos de modelo, treino, inferência ou chamadas de API. O conjunto reservado permaneceu fechado. A paridade e o resultado da **captura real** estão pendentes de revisão do código e da execução separada da Task 2. Não houve merge ou push. Uma falha após a reserva da rodada deixa o diretório reservado para investigação. O Python e a instalação de jsonschema constituem a base externa de execução.

**Exercício:** na fixture, siga o vetor de categoria com Pix 0,92 e repasse 0,08. Em delta zero, observe a aplicação no corte 0,90, a revisão no corte 0,95 e o efeito sobre uma prioridade aceita quando ambos os campos são alvos.

## Correção 1 · Integridade dos bytes auditados

O parecer de revisão identificou um intervalo entre a conferência de hashes e a releitura da captura pelo motor. A hipótese foi reproduzida apenas em fixture. A correção parte de `7ae98ff129ce9058f7ff1ec2c471bbdaafea8396` e está no commit `99cf2f33e1803838e33813d5c4ff46971181ce4e` da mesma branch.

O inicializador entrega os bytes retidos ao replay. A cópia temporária privada contém os insumos consumidos pela auditoria, inclusive stderr do selo e protocolo, schema e catálogo carregados por contracts.core. Os módulos Python continuam carregando os bytes previamente autenticados. Quando um caminho aparece em mais de um inventário, o inicializador também confere a concordância dos bytes retidos. A reserva e a saída são criadas na worktree da rodada. As APIs SF2 originais, o protocolo e o destino permanecem preservados.

A fixture troca o score 03 por uma representação JSON equivalente e altera outros sete recursos depois da atestação. Bloqueia toda releitura da origem, observa o SHA do score efetivamente aberto na cópia privada e o compara à proveniência publicada. A grade sintética mantém o hash histórico, e o resultado é publicado no destino da fixture.

Com o mesmo Python pinado, foram executados:

```sh
rtk proxy "$PYTHON_SF2" -B -m unittest -v script.classification_comparison.setfit_sf2.revision_r1.test_replay
rtk proxy "$PYTHON_SF2" -B -m unittest -v script.classification_comparison.setfit_sf2.revision_r1.test_replay.ReplayTests.test_snapshot_survives_source_replacement_after_attestation
rtk git diff --check 7ae98ff HEAD
```

Os sete testes R1 passaram em 7,500 s. Após acrescentar a observação explícita do digest do score 03 realmente lido, o teste focal passou em 1,651 s. O diff passou na conferência e a worktree ficou limpa. A suíte matemática geral não foi repetida nesta correção. Nenhuma política nova foi aplicada à captura real; a revisão do fix e a execução da Task 2 continuam pendentes.
