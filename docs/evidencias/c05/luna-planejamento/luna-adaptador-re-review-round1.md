# C05-R3 · Task 3-A · Re-revisão do orçamento Luna

**SPEC e QUALITY aprovados para congelamento em `cda8fc8`.** O bloqueio da primeira revisão foi resolvido na correção dirigida.

- Base da Task 3-A `eaca1c6b64f407e628929023145d5cf1479973d2`.
- Intervalo revisado `dc74cd321f769db49123b018c9e5c8e1ca264c83..cda8fc83d82cfc9c8cf4b746732fb11088edf751`.
- Branch `feat/luna-feita`, worktree `.worktrees/r3-luna-adaptador`.

## SPEC

`LunaAdapter.classify` chama `_validate_budget` antes de delegar a classificação ao adaptador comum. Os testes registraram zero chamadas ao gateway para orçamento falso, protocolo de orçamento incompleto e tarifa ausente ou inválida, em ambos os modos. Os casos de tarifa inválida também tiveram zero reservas e registros de uso.

Com orçamento válido, o teste no modo real com transporte sintético viu a reserva antes do único envio e o registro de uso depois da resposta. O modo real rejeita `None`. A fixture isolada continua aceitando `None` e publica o uso sem estimativa nem tarifa Qwen.

## QUALITY

- A guarda é local à Luna e usa a função histórica `rates` para verificar fonte, data, unidade e valores da tarifa. O limite inteiro de 128 tokens está alinhado ao corpo fixo. A segunda classificação com tarifa removida encerra a sessão antes de outro envio.
- O diff da correção contém apenas o adaptador Luna e seus testes. Os hashes de `candidate.json`, `operational.json`, `transport.py` e do adaptador Qwen permanecem iguais aos da primeira revisão. Os novos hashes do adaptador e de seus testes conferem com o apêndice da implementação. A verificação dos bytes do corpo Qwen passou.
- A Task 3-B fica responsável pela procedência da tarifa real, pela conciliação sobre os bytes originais, pelo prazo externo e pelo `close()` em `finally`, incluindo o gateway quando a captura não propagar o fechamento. As demais conclusões da revisão anterior continuam aplicáveis ao código preservado.

## Verificações executadas

```sh
rtk proxy env PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen \
  python3 -B -m unittest -v adapters.luna.test_adapter adapters.luna.test_transport
rtk proxy git diff --check dc74cd3..cda8fc8
rtk proxy git diff --check eaca1c6..cda8fc8
```

23 testes passaram em 10,002 s. O diff passou nas duas verificações e a worktree estava limpa. A revisão ficou restrita à guarda pré-POST e às interfaces afetadas. Casos finais, gabaritos, saídas finais, preflight, planos de execução e serviços reais ficaram fora da verificação.
