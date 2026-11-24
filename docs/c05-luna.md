# C05-R3 · Preparação offline da Luna

O responsável aprovou GPT-5.6 Luna pela Feita, com uma chamada por caso, para
preparação offline. O modelo ainda não foi qualificado nem adotado. Não houve
chamada real da Luna. A demonstração pública continua em fixture.

## O que está preparado

O adaptador e o transporte foram aceitos em `cda8fc8` e congelados em `7f04b9b`,
antes de executar o novo perfil. O executor foi entregue em `8580343` e corrigido
em `3b085fc`: uma conta sintética não pode ocupar o caminho reservado à conta real,
inclusive por link de diretório. A revisão por tarefa aprovou a correção. A revisão ampla encontrou uma corrida
com conciliação manual, corrigida em `aafc8ce`: custo ausente na resposta original
interrompe o lote mesmo com recibo manual já registrado. O recibo é preservado.
A re-revisão ampla aprovou SPEC e QUALITY, sem achados residuais.

O perfil `observed-total-luna-1.0` usa relatório 1.4.0 e preserva os dados,
instruções semânticas e critérios R2. Mantém o executor, o diário, o gate e o livro
financeiro existentes. Os 12 arquivos congelados da candidata foram conferidos.
As evidências de implementação e revisão estão em
[luna-planejamento](evidencias/c05/luna-planejamento/).

O autor executou 148 testes na entrega inicial; depois da correção passaram o
teste da guarda, o percurso Luna completo e a inicialização histórica R2. Na correção final passaram os três testes
dirigidos de conciliação concorrente, erros/custos e percurso completo. O
integrador também reproduziu o percurso de CLI. Foram seis chamadas sintéticas
de desenvolvimento e 44 finais, com 50 reservas sintéticas liquidadas. O resultado
permanece inconclusivo e a latência do modelo fica sem medição.

```sh
rtk proxy env PYTHONPATH=script/classification_comparison python3 -B -m unittest -v luna.test_round.LunaTest.test_cli_two_stages_and_replay
```

Esse teste cria e remove uma conta temporária. Não usa a chave Feita nem abre a
conta real. Exercício: identifique por que os 49 registros finais produzem apenas
44 chamadas, e por que `fixture_ready` não significa aprovação do modelo.

## Plano de consumo autorizado em 24/11/2026

O próximo ensaio proposto usa `openai/gpt-5.6-luna`, concorrência um, uma tentativa
por caso, esforço `none`, resposta JSON estruturada e limite solicitado de 128
tokens de conclusão. A conexão HTTPS começa dentro da medição; respostas completas
permitem reaproveitá-la. Não há sondagem, retry, segunda chamada ou ajuste usando
o final.

1. Até seis chamadas de desenvolvimento. Exigir 8/8 alvos corretos, 4/4 campos
   recebidos preservados, três conclusões corretas, três revisões integrais,
   reconhecimento do urgente, zero erros e p95 total até 3.000 ms. Todos os custos
   precisam estar conciliados.
2. Somente com o gate real e o selo original aprovados, até 44 chamadas finais:
   36 relatos e 13 controles, dos quais oito chamam o modelo. Manter todos os
   critérios do [protocolo](planejamento/classificacao-comparativa/luna/protocol.json),
   incluindo acerto aplicado por campo, cobertura, abstenção, urgência,
   preservação e p95 total.
3. Falha técnica interrompe o lote. Custo conhecido é registrado; custo incerto
   retém a reserva e impede continuar. Uma reprovação não libera o final nem
   permite repetir a etapa com outro nome de saída.

O modelo e o formato são publicados na [rota Feita](https://feita.ai/models/openai/gpt-5.6-luna).
A compatibilidade efetiva, o modelo retornado, a qualidade, o tempo e o custo
observado só podem ser comprovados pelo ensaio autorizado.

## Proteção de custo

O [pré-voo público](evidencias/c05/luna-preflight-2026-11-24/financial-evidence.json)
registra preços, limites e conversão de créditos, com fontes e hashes. A reserva
conservadora é **US$ 1,239 por chamada pendente**, usando limites máximos e as
maiores faixas de contexto/cache derivadas das notas oficiais. Esse valor é uma
trava financeira, não uma estimativa do custo de um relato curto. A reserva é
substituída pelo custo conciliado antes de avançar.

O [estado da conta existente](evidencias/c05/luna-preflight-2026-11-24/account-status.json)
foi consultado sem alteração: acumulado conservador US$ 0,02687405, teto global
US$ 10, 50 reservas liquidadas e nenhuma pendência. A diferença para o teto não
é uma consulta ao saldo da Feita. Não se cria outra conta nem se reinicia o gasto.

A preparação offline está aceita. O responsável autorizou até seis chamadas
reais e até 44 adicionais somente se o gate real passar, conforme o
[registro de autorização](evidencias/c05/luna-preflight-2026-11-24/autorizacao-real.json).
O integrador gera e confere o manifesto vinculado à mesma conta, configuração,
fontes e revisão. Essa autorização não declara o modelo qualificado ou adotado. A chave local fica privada e não é enviada aos
agentes, ao frontend ou à demonstração pública.

C06 depende de qualificação real e decisão de adoção. O atendente conversacional
real continua no trabalho posterior E01; não faz parte desta classificação.
