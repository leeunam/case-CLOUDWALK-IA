# Relatório 1.2 para o tempo total observado

O responsável aprovou a medição do tempo de classificação que o usuário espera antes do teste final. O protocolo de qualidade 1.1.0 usa o gate `observed_total_latency_p95_ms_max`, com limite inclusivo de 3.000 ms. O relatório 1.2.0 declara `ipc_contract_version: "1.1.0"`. Os adaptadores, os controles e as três streams usam os envelopes IPC 1.1.0. [Protocolo congelado](../../protocolo-comparacao-1.1.json) · [Plano e aprovação](../../plano-latencia-total.md)

| Perfil | Protocolo de qualidade | Relatório | IPC | População do percentil |
| --- | --- | --- | --- | --- |
| `warm-1.0` | 1.0.0 | 1.1.0 | 1.1.0 | Tentativas reais aquecidas com tempo observado |
| `observed-total-1.1` | 1.1.0 | 1.2.0 | 1.1.0 | Relatos reais concluídos com uma duração do candidato, em qualquer estado térmico |

## Medição

C02 inicia o relógio monotônico antes de validar a entrada e lê a duração depois de validar a decisão de aplicar ou revisar. A duração do relato abrange o despacho, a espera do fornecedor, todas as perguntas e o processamento da resposta. Um relato com dois campos gera uma amostra. Um timeout com resposta validada conserva a duração medida. O limite da tentativa é 5 s, a tolerância de entrega de timeout é 250 ms e a concorrência é 1.

O avaliador registra em separado o provisionamento, o download e a inicialização local que antecedem READY. Atrasos dentro da tentativa integram a duração. O estado térmico pode ser `warm`, `cold` ou `unknown`. Um erro, saída inválida ou abstenção com duração observada também entra no percentil. Os controles ficam nas métricas de integridade e uso pertinentes. O encerramento do processo antes de entregar uma observação validada mantém a tentativa pendente e a execução inconclusiva.

O verificador ordena os tempos dos IDs concluídos e confere os postos `ceil(0,50 × n)` e `ceil(0,95 × n)` das duas métricas do relatório. Em desenvolvimento a população prevista corresponde aos relatos concluídos. Para `final_test`, a população prevista continua 36 inclusive em prefixos. Um lote com todas as durações esperadas fica `measured`. Uma amostra incompleta fica `partial`, com o número de durações disponíveis no denominador. Zero amostras resulta em `unmeasured`, com valor e numerador nulos e população prevista no denominador. As fixtures usam essa mesma regra de zero amostras. Somente um teste final real com todos os critérios de evidência e qualidade verificados pode receber um resultado decisório.

O teto financeiro global aprovado é US$ 10. O piloto C03 já executado teve autorização específica. Neste novo protocolo `paid_execution_authorized` é falso. A autorização e o executor de C05 exigem escopo próprio, incluindo IDs, versão e limites. O golden deste diretório é uma fixture estática de controles e reutiliza os três arquivos IPC 1.1 identificados no inventário. Seu resultado é inconclusivo.

## API para o avaliador

O registro fechado fica em `script/check_classification_contracts.py`. Cada perfil fixa o caminho e SHA do protocolo e do lock. O lock fixa os schemas e o relatório de referência. O schema 1.2 reutiliza os campos e definições estáveis do schema histórico pelo seu identificador local. O carregamento resolve as referências offline.

```python
import check_classification_contracts as c01

profile = c01.get_profile("observed-total-1.1")
validation, protocol, split, catalog, cases = c01.profile_context(profile.name)
example = c01.load_bundle(validation, profile.golden_path)
c01.verify_run(example, validation, protocol, split, catalog, cases)
```

- `get_profile()`, `validators()` e `profile_context()` usam o perfil histórico por padrão. `profile.name`, `report_version`, `ipc_version`, `latency_gate`, `protocol_path`, `golden_path` e `protocol_source()` identificam o formato selecionado e a fonte para o plano.
- `profile_context(name)` entrega os cinco argumentos de contexto de `verify_run`. O preflight do avaliador pode acrescentar o golden como sexto valor ao manter suas checagens de projeção, máscaras, conjunto total de IDs e versões. `load_bundle(validation)` conserva seu default de fixture histórica. Para o perfil novo passar o caminho explícito.
- O seletor de geração de C02 deve levar o perfil à invocação, ao plano, ao relatório e aos registros de interrupção. Para entrada/saída do processo usar `profile.ipc_version`. Os arquivos de configuração dos adaptadores atuais fixam essa versão do IPC.
- Para evidência salva, `verify_report(path)` seleciona o perfil pela combinação exata entre versão de relatório e caminho, versão e SHA do protocolo, verifica os arquivos locais fixados e valida todas as streams. O retorno é o perfil aceito. `verify_report(path, name)` também exige que o perfil encontrado seja o solicitado.

## Reprodução offline

Na raiz do checkout, usando as dependências de C02 já instaladas, três comandos exercitam o novo contrato.

```sh
rtk proxy python3 -B script/check_classification_contracts.py --profile observed-total-1.1
rtk proxy python3 -B docs/planejamento/classificacao-comparativa/contratos/relatorio-1.2/test_latency_profile.py -v
rtk proxy python3 -B script/check_classification_contracts.py --report docs/planejamento/classificacao-comparativa/contratos/relatorio-1.2/report.json
```

O comando do checker sem argumentos e a suíte em `contratos/test_regressions.py` continuam exercitando o perfil histórico. O exemplo C02 de contrato técnico 1.0 anterior a esses dois perfis continua vinculado à sua revisão de origem.

**Exercício.** Em uma amostra de 36 relatos, ordene 34 tempos de 1.500 ms, um de 3.000 ms e um timeout de 5.000 ms. Identifique os postos 18 e 35, depois troque 3.000 por 3.001 ms e compare o resultado do gate.
