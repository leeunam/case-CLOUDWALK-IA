# Decisão de adoção do SetFit R1 para C06

Em 26/11/2026, o SetFit R1 foi adotado para completar categoria e prioridade ausentes no help desk. O responsável autorizou antes da execução a conferência dos metadados, uma única exposição dos 120 casos e a continuidade direta para integração se **todos** os critérios congelados passassem. O resultado independente foi `eligible` nos dez critérios e a segunda auditoria reproduziu os mesmos bytes sem inferência. Essa condição cumprida libera a implementação. O backend e a publicação fixture continuam no marco anterior até o aceite do novo fluxo. [Registro de adoção](../../../evidencias/c05/sf2/final-r1-01/task-5-adoption.json) · [Execução e limites](../../../evidencias/c05/sf2/final-r1-01/README.md)

## Identidades aprovadas

| Papel | SHA-256 |
| --- | --- |
| Liberação do preparo revisado | `1d4396aa3ea665f6ed6c8d2743cabdc3f1e9f0f966d405c070f65f06862fd52a` |
| Congelamento referenciado na liberação | `41c25a53b46f9928fd92252caf6249a545336c9b4d1e5da49787b35a906fff5a` |
| Manifesto do pacote | `224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872` |
| Especialista de categoria | `b989492b3623dc6015e97c5d8af975950a48ce72f489d467062e07fe6996a6c5` |
| Especialista de prioridade | `8a0224ad38fa45a902a58bc25c8dbcc4c9e9aff96ec50024dfe4a01c304bcab1` |
| Política de coleta `sf2-ipc/1.0` | `09de8c13fa56bcddb8006982b0016e3452bb15de89a72a6eae6c42847cedc21f` |
| Política de decisão `sf2-r1-offline/1.0` | `127eb227ac174384700a60390272a48abdca9a81592086dde5bc132727338473` |
| Arquivo que inventaria as 17 fontes do worker original | `60b16a6772f648055f572c9a8f96ca8e654972ae6bddee2ec4050304bc18ae69` |
| Runtime R1 · `__init__.py` | `2184de73af3c09fd3814133595af758e844d8cadac0f3170ea694dd4b99209e5` |
| Runtime R1 · `context.py` | `3ff94d81446f502ebe419c7bacbe1ac94e766a34b61be15f0d3a83894b254c9c` |
| Runtime R1 · `decision.py` | `2816733b28d3b2e1b923c5081662de1500c0f1180f42a973f02dbd448d0cf5a4` |

A coleta usa τ=0,50 em ambas as cabeças e δ=0,0. O runtime deriva a decisão `sf2-final-r1/1.0` com τ=0,95 para categoria, τ=0,70 para prioridade e δ=0,0 em ambas. O recibo da liberação identifica o congelamento que atesta pacote, políticas e fontes. C06 deve carregar os mesmos bytes e conferir o inventário antes de disponibilizar o serviço. [17 fontes qualificadas](../../../evidencias/c05/sf2/qualificacao-01/execucao-02/avaliacao/adapter.json) · [Congelamento](../../../evidencias/c05/sf2/final-r1-preparacao-02/final-fix-publico/freeze.json) · [Política de coleta](../../../evidencias/c05/sf2/qualificacao-01/execucao-02/avaliacao/capture-policy.json) · [Política de decisão](../../../evidencias/c05/sf2/revisao-01/selected-policy.json)

O teste final usou os especialistas locais já treinados e os cortes definidos na validação, sem novo treino, exploração de cortes ou gasto de API. A decisão automatizou corretamente 68/96 classificáveis, concluiu um com prioridade incorreta e enviou 51/120 à revisão. A regra operacional preserva campos válidos do canal, consulta apenas os ausentes e só aplica um complemento integral após validação. Casos inconclusivos, inválidos ou incompatíveis seguem para supervisão com motivo. [Relatório independente](../../../evidencias/c05/sf2/final-r1-01/task-4-review.md)

C06 implementa proveniência por campo, revisão humana e integração com Kafka. C07/F09 final verifica uma instalação limpa com pacote fornecido sob custódia e os três canais em duas marcas. Os aceites anteriores em fixture continuam identificados como tal. [Plano e aceites](../c06-setfit-integracao.md) · [Contrato HTTP privado](../../../contratos/classification-http/README.md)
