# Task3-D3 · Executor offline da instrução Luna R4

Entrega para revisão do integrador. Base `f9445ed4a05036c81d624123c0fe696e12822511`,
commit `5aa4955d62f2fdf1f51fe9d22b02f778e29f33e6`,
branch `feat/luna-executor-r4`, worktree `.worktrees/r4-luna-executor`.
A árvore ficou limpa após o commit. A conta real ficou fechada, com zero
chamadas externas e zero gasto real durante a tarefa. O último registro público
R3 informa US$ 0,02869232 acumulados, 56 reservas liquidadas e zero pendências.

## Interfaces e fontes

A CLI `script/classification_comparison/luna_r4/execute.py` fixa o perfil
`observed-total-luna-r4`, escopo `c05-feita-luna-r4`, prefixo `luna-r4-`,
modelo `openai/gpt-5.6-luna` e versões de protocolo/relatório/IPC
1.4.0/1.5.0/1.1.0. A CLI C02 genérica rejeita o perfil na análise dos
argumentos, antes de abrir configuração, processo ou chave. A CLI dedicada
oferece apenas development e final. O exemplo real aguarda evidência financeira
e o exemplo de manifesto mantém `enabled=false`. Não foi criada autorização
financeira ou configuração real verificada.

O descritor R4 usa as classes de adaptador, transporte e configurações da Luna
e as mesmas rotinas de plano, validação, IPC, diário, gate, selo e finanças.
O atributo de família do perfil ativa o prazo externo por caso e a identidade
fixture de ambas as rodadas. O fechamento do gateway subjacente está no
`finally` do processo C05. O modelo recebe somente a projeção histórica e a
instrução/rubrica. Os 16 diagnósticos de desenvolvimento ficam em artefatos
separados, com 16 acordos entre duas rotulações por IA, 18 campos coincidentes,
zero aprovações humanas e zero chamadas à Luna. Os denominadores oficiais de
desenvolvimento e final permanecem idênticos aos da R3. O autor não viu os
pares novos ou o final. A leitura cega do integrador ocorreu depois do commit
da candidata, antes do congelamento formal e sem feedback ao autor.

| Fonte | SHA-256 |
| --- | --- |
| Aprovação offline R4 | `bc1ff0dc085764e2f3ff41698f6097bd7e95f0bad48c4f7f89c4a3773e2df1ef` |
| Congelamento R4 | `a1e53d4379d0e45ab3a5d86452e872179facad5fcecf1ebded29c161f604925e` |
| Candidata R4 | `ba0701bd3b003cb146f8212bef1753d45c9a2ef8d548472ffe3d04d83cced888` |
| Instrução R4 1.2.0 | `026c70c89da05102f9c6b84c87ba8e2c522d8d77cd2405403849d6823b7e2741` |
| Configuração operacional R3 | `0666cdd1c99f58c52512681563b72ddcaf4f97593071a1797104526d062678da` |
| 36 casos finais da R2 | `17f5bae372983f90aa1956d0d583db25483a77a3ff35e4f1041ad4d51b897af9` |
| Binding R4 | `fdccf2127947da876720cd501c972000d52af365111787f096111748300855b5` |
| Protocolo R4 | `85590d95926acc76c05e50bae420180f869ff1084856f4c1fcf11542175df8fd` |
| Lock de fontes 1.5 | `ea1531d622ea21c0db68f71b576acea59cef829d765ed16a76a36312b25584be` |
| Exemplo de relatório 1.5 | `1f0506fea34ad7926daad2b3c7e714227fde03417e52750a1d3f9f42bf1bdfd0` |
| Motor financeiro histórico | `d9a81084546db988ef8afc6f33732120749c749a9415bebae07f3402dbbef44e` |

## Verificações

Passaram **160 testes distintos** somando as suítes e as repetições dirigidas
dos itens abaixo. C02 39, C05 37, R2 14, Qwen 30, adaptador Luna 14,
transporte Luna 9, executor R3 7 e executor R4 10. Todos os HTTP simulados
usaram fixtures. A CLI R4 liquidou 6+44 reservas numa conta temporária.
O saldo dessa conta de teste passou de 0,02869232 a 0,05604232. O fluxo final
resultou em 36 candidatos, 13 controles, 44 requisições sintéticas, p95
`unmeasured` e decisão `inconclusive`. O gate anterior foi `fixture_ready`.
O ID da etapa permaneceu usado depois de trocar configuração e saída.

A suíte também verificou interrupção na primeira falha técnica, inclusive HTTP
500 com liquidação do valor conhecido, retenção na incerteza, prazo total e
custo original ausente com recibo manual concorrente. A reprovação R3 produzida
em fixture bloqueou o final R4 na própria conta e em outra conta temporária,
inclusive quando o arquivo de prova foi reescrito sem o selo R4. As guardas
rejeitaram caminho/ID divergentes antes do acesso à conta em init/status/
reconcile/planejamento. A validação detectou alteração do runtime. O teste de
mismatch entre modos rejeitou prova fixture na avaliação de modo real.

Os cinco checkers aprovaram os exemplos e respectivas 64/7/9/10/12
contraprovas. Há **25 relatórios anteriores verificáveis** no commit-base
(18 warm, três observed 1.1, dois R2, dois R3 incluindo o exemplo dourado 1.4
e o desenvolvimento real). Os 25 foram confrontados byte a byte com Git e
validados no checker de origem. O protótipo 1.0 foi comparado byte a byte à
base separadamente. As 12 fontes congeladas R3 e 7 R4 também foram comparadas
à base. Nenhuma alteração no orçamento/schema, diretórios históricos de
dados/evidências ou runtime da candidata. A contagem inicial de 24 no brief
omitia o exemplo dourado 1.4.

Condições das repetições:

- O ambiente restrito negou escrita no socket local de IPC dos testes do
  transporte (`PermissionError`). Os nove testes de transporte passaram com
  essa comunicação local liberada e conexão HTTPS simulada, mantendo a chave
  removida do ambiente.
- Em um primeiro teste da guarda real, o Git simulado devolvia um caminho no
  lugar do hash HEAD. A simulação foi corrigida para distinguir os dois
  comandos, e o teste passou nos seis cenários de status/reconcile/run.
- Uma edição no checker durante a suíte R3 mudou o hash entre o planejamento e
  a execução da fixture de prazo expirado. A etapa foi recusada antes de abrir
  o run. Com os arquivos finais estáveis, o teste de interrupções e o percurso
  CLI R4 voltaram a passar. O carregamento de configurações foi conferido
  novamente após fixar o escopo padrão da subclasse R4.

Comandos de reprodução na raiz da worktree, com a chave removida do ambiente:

```sh
rtk proxy env -u FEITA_API_KEY python3 -B -m unittest discover -s script/classification_comparison
rtk proxy env -u FEITA_API_KEY python3 -B -m unittest discover -s script/classification_comparison/c05
rtk proxy env -u FEITA_API_KEY python3 -B -m unittest discover -s script/classification_comparison/r2
rtk proxy env -u FEITA_API_KEY python3 -B -m unittest discover -s script/classification_comparison/adapters/qwen
rtk proxy env -u FEITA_API_KEY PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen python3 -B -m unittest adapters.luna.test_adapter adapters.luna.test_transport
rtk proxy env -u FEITA_API_KEY PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna.test_round luna_r4.test_round
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-luna-r4
rtk proxy python3 -B docs/evidencias/c05/r4-instrucao/conferir_historico.py
```

Para os outros quatro checkers, os perfis usados foram `warm-1.0`,
`observed-total-1.1`, `observed-total-r2` e `observed-total-luna-1.0`.
Na execução original de D3, o inventário foi chamado com
`rtk proxy python3 -B /tmp/cw-r4-d3-history.py`. O
[verificador versionado](conferir_historico.py) reproduz essa conferência a partir
da raiz do checkout. Ele enumera os relatórios da base `f9445ed`, compara os
bytes atuais com o Git e verifica os 25 relatórios nos perfis de origem.
Confere separadamente os bytes do protótipo 1.0 e as fontes congeladas R3 e R4.
A comparação dos diretórios protegidos usa a base e o commit da entrega D3,
`5aa4955`, para delimitar a mudança auditada. O guia público reproduz o percurso completo em uma conta temporária.

## Pendências

Revisão por tarefa e revisão ampla R4 pelo integrador. Um pré-voo privado
futuro precisa reconfirmar fontes de preço/limites/unidade e situação da
mesma conta global. O consumo para as etapas oficiais depende de nova
autorização humana. Avaliar os 16 diagnósticos na Luna requer autorização
específica para experimento posterior. A qualidade e a adoção permanecem
indecididas.
