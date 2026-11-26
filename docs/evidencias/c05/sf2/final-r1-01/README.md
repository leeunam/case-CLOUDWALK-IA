# SF2-FINAL-R1 · resultado do teste independente

Em 26/11/2026, o executor rodou a política R1 congelada uma vez nos 120 casos reservados e em cinco controles. Os dez critérios passaram. Um segundo auditor reconstruiu as decisões a partir da coleta e produziu um relatório idêntico em bytes ao primeiro. O responsável havia autorizado a integração se todos os critérios passassem. C05 encerrou a seleção e C06 recebeu o SetFit R1 para integração. [Decisão de adoção](../../../../planejamento/classificacao-comparativa/sf2/decisao-adocao-r1.md) · [Protocolo do final](../../../../planejamento/classificacao-comparativa/sf2/sf2-final-r1-protocolo.json)

| Critério congelado | Observado | Aceite |
| --- | --- | --- |
| Categoria correta entre as categorias aplicadas | 40/40 | ≥90% |
| Prioridade correta entre as prioridades aplicadas | 47/48 | ≥90% |
| Conclusões automáticas entre os classificáveis | 69/96 | ≥68/96 |
| Urgentes reconhecidos pelo rótulo bruto | 17/17 | ≥14/17 |
| Campos válidos do canal preservados | 80/80 | 100% |
| Conclusões em casos com revisão esperada | 0/24 | 0 |
| Urgentes com prioridade inferior aplicada | 0/17 | 0 |
| Casos com aplicação parcial | 0/120 | 0 |
| Chamadas a especialistas nos controles completo e inválido | 0 nos dois controles | 0 |
| p95 de latência total do adaptador nos casos | 71,960936 ms | ≤3.000 ms |

Dos 120 casos, 40 precisavam somente de categoria, 40 somente de prioridade e 40 dos dois campos. Havia 80 alvos por campo. Dos 96 classificáveis, 69 foram concluídos, 68 corretamente. Um caso recebeu prioridade incorreta. Dos 17 alvos urgentes, 13 receberam prioridade urgente e quatro foram à revisão. As 51 revisões compreendem os 24 casos previstos e 27 classificáveis. Os intervalos de Wilson de 95% constam no [relatório agregado](task-4-publico/audit.json).

O p95 corresponde à 114ª duração ordenada. A mediana foi 38,46 ms e o máximo 110,90 ms. A inicialização levou 19.381,06 ms, medida à parte, assim como os cinco controles. Os picos de CPU e RAM registrados foram 198,80% e 1.708.331.008 bytes no worker, 79,36% e 529.989.632 bytes no supervisor. Essas medições descrevem dois processos no equipamento da coleta. A espera no Solid Queue, o HTTP Rails, o Kafka, a memória da pilha e o tempo até a resposta visível serão medidos em C06/C07. [Execução](task-4-report.md) · [Revisão independente](task-4-review.md)

## Trilha pública de verificação

A [liberação revisada](../final-r1-preparacao-02/final-fix-publico/release.json) ancora o [mapa dos metadados](task-4-custody-metadata.json), a [autorização operacional](task-4-production-authorization-copy.json), o [recibo](task-4-publico/execution.json) e o [selo da execução](task-4-publico/seal.json). Os caminhos nos vetores [execute](task-4-command.json) e [audit](task-4-audit-command.json) identificam o ambiente histórico. Relatos, gabaritos e observações individuais permanecem na custódia local.

É possível conferir os oito digests e a igualdade entre as duas auditorias com Python padrão, a partir deste diretório. O comando lê somente arquivos públicos.

```sh
rtk proxy python3 - <<'PYTHON'
import hashlib, json
from pathlib import Path

public = Path("task-4-publico")
for name, expected in json.loads(Path("task-4-public-artifacts-sha256.json").read_bytes()).items():
    assert hashlib.sha256((public / name).read_bytes()).hexdigest() == expected, name
assert (public / "audit-independent.json").read_bytes() == (public / "audit.json").read_bytes()
print("Oito digests conferidos. Auditorias idênticas.")
PYTHON
```

A [adoção registrada](task-5-adoption.json) vincula autorização, liberação, recibo, selo e resultado auditado. O complemento real na plataforma e sua reprodução em instalação limpa estão pendentes.
