# C05-R2 · Proposta para melhorar a abstenção

**Estado:** investigação e planejamento autorizados pelo responsável em
24/11/2026 («boa, vamos prosseuguir»). A escolha entre as abordagens abaixo
ainda não foi confirmada. Este documento não autoriza novas chamadas pagas
nem muda o classificador do produto.

Tarefa C05-R2; base `1a7cd4235ce44b01213f685439af3523989e5097`.
Planejamento no checkout principal, branch `main`, diretório
`/home/inteli/Documents/projetos/case-CLOUDWALK-IA`. Nenhuma worktree de
implementação R2 foi criada. O primeiro resultado continua
[não elegível](../../c05-resultado.md), e C06 permanece bloqueada.

## O problema a resolver

O modelo devolveu códigos válidos, mas aplicou categorias sem informação
suficiente. O schema JSON garante o formato e os códigos permitidos; ele não
garante que o texto sustente a escolha. A rubrica já oferece
`informacao_insuficiente`. Portanto, adicionar essa opção novamente não resolve
o problema observado. A nova versão precisa tornar mais clara a decisão entre
classificar e se abster, e provar que não passou a recusar os casos claros.

Não houve confiança numérica retornada que permita escolher um limiar, e uma
autoavaliação de confiança não será tratada como probabilidade calibrada.
Extrair uma frase do relato também não comprova, por si, que ela implica o rótulo.

## Abordagens para escolha

| Opção | Mudança concreta | Vantagem | Limite e custo |
| --- | --- | --- | --- |
| **A — instruções mais conservadoras, uma chamada** | Nova versão de prompt/política que verifica suporte de cada campo e permite abstenção; resposta JSON com os mesmos campos/códigos. | Menor mudança no classificador; mantém uma chamada e o IPC. | O modelo ainda pode desobedecer ou recusar casos claros. Mais instruções podem aumentar tokens/latência; tudo precisa ser medido novamente. |
| **B — regras determinísticas adicionais** | Além do modelo, regras locais configuradas barram aplicações quando não houver suporte definido para a categoria. | Bloqueios auditáveis nos padrões conhecidos, sem segunda chamada. | Exige manter regras e tratar contexto, negação e linguagem indireta. Regras estreitas deixam erros passar; regras amplas reduzem cobertura. Não usar exceções para IDs do teste. |
| **C — segunda chamada verificadora** | Uma chamada classifica e outra pode vetar a classificação; desacordo leva à revisão. | Separa proposta e conferência como etapas rastreáveis. | Acrescenta chamadas e latência serial; o segundo modelo pode repetir o erro. Exige novos estados/observações e demonstrar novamente p95 ≤3 s. |

**Recomendação: começar por A.** É uma hipótese de melhoria, não garantia de
aprovação. B e C ficam como alternativas, sem implementação automática se A
falhar. A decisão sobre outra abordagem volta ao responsável.

## Desenho proposto para A

- Mesmo Qwen e catálogo. O formato da resposta e o IPC 1.1 permanecem.
- Antes de escolher um código, verificar se o próprio relato sustenta a
  distinção da categoria ou do nível de impacto/prazo. Não transformar
  plausibilidade em fato. Linguagem semanticamente clara pode bastar; não
  exigir uma palavra literal como condição universal.
- Avaliar categoria e prioridade separadamente: impacto urgente não revela o
  assunto, e conhecer o assunto não fornece automaticamente impacto/prazo.
  Campos válidos recebidos continuam preservados e disponíveis como contexto.
- Quando faltar suporte em um campo solicitado, retornar
  `informacao_insuficiente`. O avaliador mantém a regra existente de revisão
  integral, sem aplicar parcialmente as outras predições.
- Nova versão/hash de instruções e política, em arquivos próprios. Sem exemplos
  ou exceções derivados dos casos finais antigos; sem rótulos do teste no prompt.
- Até uma versão candidata nesta rodada, com uma tentativa por caso. Não criar
  um ciclo automático de ajuste, consumo e repetição até obter aprovação.

As instruções atuais são curtas, mas a rubrica já contém regras de abstenção.
Só acrescentar texto não prova efeito. É necessário verificar cobertura,
urgência, abstenção e tempo na nova população.

## Nova avaliação prospectiva

Proposta enxuta: **36 relatos finais inéditos**, 12 por máscara de omissão,
com 29 casos classificáveis, sete de revisão obrigatória e seis urgentes com
prioridade omitida. Mantém o tamanho e os denominadores principais da primeira
rodada. Não é uma comparação pareada antes/depois.

Composição proposta para os sete casos de revisão: dois na máscara categoria,
dois na máscara prioridade e três na máscara dupla. Nos três duplos falta base
para a categoria; um deles tem prioridade urgente determinável, outro tem
prioridade não urgente determinável e outro também não permite definir a
prioridade. Assim há cinco alvos de categoria insuficiente e três de prioridade
insuficiente, com uma sobreposição. Os demais 29 casos são classificáveis.
Os seis urgentes omitidos incluem o caso de categoria desconhecida, além de
três na máscara prioridade e dois classificáveis na máscara dupla.

Isso deixa 24 alvos de categoria e 24 de prioridade, como antes. A distribuição
factual de temas, prioridades e marcas é registrada e congelada antes de
inferência; não se escolhem casos depois de ver respostas. A amostra continua
exploratória e pequena, sem certificação de segurança em produção.

Manter os 13 controles: oito naturais podem chamar o modelo; quatro completos
ou inválidos têm zero chamadas, e um é injetado pelo avaliador. Os controles
não entram no p95 ou nos acertos dos 36 relatos.

Os limites continuam: preservação 100%, zero aplicação parcial, zero conclusão
automática nos sete casos de revisão, zero urgente automaticamente rebaixado,
acerto aplicado ≥90% por campo, cobertura ≥21/29, reconhecimento urgente ≥5/6
e p95 total ≤3.000 ms. Ausência de métrica ou execução incompleta não aprova.
Zero urgente automaticamente rebaixado e reconhecimento bruto ≥5/6 são
critérios diferentes, preservados do protocolo: uma abstenção/erro não é
rebaixamento aplicado, mas conta como não reconhecimento. O relatório mostra
separadamente os seis urgentes classificados, rebaixados, abstidos e com erro;
não declara reconhecimento de 100% se apenas o limite de 5/6 foi cumprido.

Um autor e um revisor de dados independentes da frente de instruções criam e
revisam os novos relatos a partir da rubrica e das quotas, sem receber os erros
ou os 60 textos antigos. Um terceiro conferente de semelhanças fica fora da
frente de instruções e da autoria. Ele pode comparar os textos antigos e os
novos, mas não recebe respostas/erros do Qwen. Devolve ao autor/revisor somente
os novos IDs que precisam ser substituídos por outros cenários, sem expor os
textos antigos; nenhum texto novo ou par de semelhança vai à frente de prompt.
A conferência ocorre antes do congelamento e não é uma garantia matemática
de independência.

Como proposta para esta amostra exploratória, os rótulos são escritos por um
agente e revisados por outro a partir da rubrica, antes de qualquer resposta do
Qwen. Não derivar o gabarito das respostas do candidato avaliado. Essa revisão
por IA é declarada; não será chamada de gabarito humano ou validação em
produção. Uma divergência entre revisores não prova insuficiência do relato:
o caso precisa ser conciliado pela rubrica e, se persistir a dúvida, levado ao
responsável antes do congelamento. Não editar rótulos após observar respostas.
O responsável aprova o protocolo e pode optar por revisão humana adicional.

A frente que ajusta instruções não lê o novo final. Trabalha apenas com os
24 casos de desenvolvimento anteriores. O integrador não abre os textos do
novo final para ajudar a ajustar o candidato. A separação é de papéis, branches
e instruções; não será descrita como isolamento de segurança do sistema.
Prompt/política e gabarito são congelados antes da primeira chamada final.
O executor projeta somente texto, catálogo, campos recebidos e ausentes para a
API; gabarito e justificativas continuam fora da requisição.

## Trabalho necessário no avaliador

O avaliador e o executor atuais prendem as fontes e os 36 IDs antigos. Por isso,
mesmo escolhendo A, trocar só o arquivo de prompt não permite executar outro
teste. Preparar um perfil R2 separado, sem reescrever os perfis históricos.
Proposta: protocolo de qualidade 1.2, relatório 1.3 e IPC 1.1; a nova versão do
relatório distingue o novo vínculo de fontes no seletor atual de perfis.
Prompt e política propostos 1.1.0, adaptador experimental R2 1.2.0.
Os significados dos limites acima permanecem.

O novo perfil fixa fontes, versões, IDs e exemplos contratuais próprios,
preservando cronômetro, decisões, diário e guardas financeiras já verificados.
O pacote da avaliação combina os 24 relatos de desenvolvimento preservados
com os 36 novos finais, sem importar os 36 finais antigos. O autor do novo
final prepara apenas os novos relatos; a integração copia os 24 de
desenvolvimento sem alteração depois de congelar a candidata. A divisão e o
inventário conferem que não há ID repetido ou caso fora da partição.
Verificações futuras incluem rejeitar fonte errada, perfil antigo apresentado
como R2, prompt alterado após congelamento, repetição e gabarito na requisição.
Fixtures verificam integração e relatório; não aprovam o modelo.

## Fatias SDD propostas e paralelismo

| Fatia | Entrega verificável | Dependência e ambiente propostos |
| --- | --- | --- |
| R2-01 — contrato e dados independentes | Novo protocolo, quotas exatas, revisão, projeção sem gabarito e fontes congeladas; candidato não vê o final. | Desenho aprovado. `docs/r2-protocolo-dados`, `.worktrees/r2-dados`. |
| R2-02 — instruções candidatas | Prompt/política novos, interface igual, fixtures de abstenção/preservação e congelamento da versão. | Desenho aprovado; pode andar em paralelo com dados. `feat/r2-instrucoes-qwen`, `.worktrees/r2-qwen`. |
| R2-03 — execução R2 | Perfil novo, dry-run, prova de proteção financeira, simulação completa e compatibilidade dos históricos. | Contrato comum aprovado; integra fontes das duas frentes após congelamento. `feat/r2-avaliador`, `.worktrees/r2-avaliador`. |
| R2-04 — ensaio e decisão | Execução autorizada, resultados brutos, custos, auditorias e conclusão de elegibilidade; C06 somente após aprovação válida. | Três fatias aceitas, fonte integrada e autorização específica. Chat central. |

Branches e diretórios foram conferidos livres durante a preparação, mas não
foram criados nem reservados. O integrador fixa uma nova base comum contendo o
contrato aprovado antes de despachar; não usar a base desta proposta como se
já contivesse o contrato R2. Não criar novas issues públicas até fechar o
desenho; usar este documento e o card C05 para acompanhar a escolha.

## Chamadas e orçamento

Nesta preparação: **zero chamadas ao fornecedor**. O total contabilizado segue
US$ 0,02300927. Restam US$ 9,97699073 sob o teto cumulativo, que é diferente do
saldo comercial da conta e não é uma meta de gasto.

Proposta de ensaio futuro: seis dos 24 casos de desenvolvimento, escolhidos
antes das novas respostas, dois por máscara:

| Máscara | IDs de desenvolvimento | Cobertura do ensaio pequeno |
| --- | --- | --- |
| Categoria | `jev-004`, `jev-013` | Uma categoria determinável e uma insuficiente. |
| Prioridade | `jev-002`, `jev-023` | Um urgente determinável e uma prioridade insuficiente. |
| Ambos | `jev-006`, `jev-039` | Dois campos determináveis e dois campos insuficientes. |

Executá-los uma vez; o primeiro também confere formato e coleta de uso, sem
sondagem extra. Somente se a execução e o comportamento no desenvolvimento
forem compatíveis com o desenho congelado, executar 36 finais + oito controles
naturais. **Máximo planejado: 50 novas chamadas**, sem retentativas. Não repetir
baseline nem controles naturais na etapa de desenvolvimento.

Gate proposto dos seis: os oito campos-alvo devem coincidir com o gabarito
congelado, incluindo abstenções; três casos classificáveis devem completar
corretamente e três devem ir integralmente à revisão. Preservar os quatro
campos válidos fornecidos, reconhecer o único urgente omitido, não apresentar
saída inválida/erro/timeout, obter custo conciliável em todas as chamadas e
p95 total observado ≤3.000 ms (n=6, nearest-rank). Esta verificação pequena é
deliberadamente conservadora e não substitui a avaliação final. Se a candidata
não atender, registrar e interromper esta rodada para nova decisão, sem gastar
automaticamente outro lote de ajustes. Não alterar esses seis IDs com base nas
respostas.
Nesse piloto de seis, o p95 nearest-rank é o maior tempo observado. O máximo de
50 chamadas vem de 6 de desenvolvimento + 36 finais + 8 controles naturais;
os outros cinco controles não fazem chamadas reais.

Reutilizar a conta financeira existente em
`.worktrees/c05-comparacao/.superpowers/financial/c05-qwen/account-v4.sqlite3`,
com o histórico completo. Não abrir uma conta nova com mais US$ 10. Verificar
tarifas e reservar por despacho; custo desconhecido ou timeout conserva a
reserva e interrompe. Não reduzir a reserva usando a média do primeiro lote.
Não fracionar um novo orçamento de US$ 10 entre as fases nem pressupor que um
teto de piloto menor que a reserva permite despachar uma chamada.

A aprovação da abordagem libera preparar e verificar a implementação offline.
O consumo futuro fica para autorização concreta após o contrato, os dados,
o candidato e o executor estarem revisados. A autorização do primeiro lote foi
consumida. Nenhum resultado novo, melhoria de acerto ou custo futuro é afirmado.

## Decisão solicitada

Escolher A, B ou C. A recomendação é **A com novo teste independente**, mantendo
os limites e a regra de revisão integral. Após a escolha, consolidar o contrato
e liberar as frentes offline antes de solicitar qualquer consumo adicional.
[Revisão documental e esclarecimentos](../../evidencias/c05/r2-planejamento/revisao-proposta.md).

**Exercício.** Um relato pode deixar claro que há urgência e ainda não informar
o assunto. Explique por que, nesse caso, a classificação completa deve continuar
em revisão e por que isso não equivale a ignorar o sinal de urgência.
