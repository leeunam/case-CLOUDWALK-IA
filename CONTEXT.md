# Help desk multimarca

Vocabulário de domínio confirmado durante o planejamento da plataforma de
atendimento. Decisões técnicas e critérios de entrega ficam nos documentos de
planejamento.

## Linguagem

**Marca**:
Identidade de negócio à qual um atendimento pertence, como InfinitePay ou JIM.
Uma marca pode habilitar várias equipes para atuar em seus atendimentos.

**Equipe**:
Grupo operacional de suporte responsável por um conjunto de atendimentos.
Uma equipe pode atuar em várias marcas mediante autorização explícita e pode
ser responsável por várias filas dessas marcas.
_Evitar_: time como nome alternativo em documentos do projeto.

**Autorização de equipe por marca**:
Vínculo explícito que habilita uma equipe a atuar nos atendimentos de uma marca.
Uma equipe pode possuir esse vínculo com várias marcas.

**Atendimento**:
Caso de suporte associado a uma marca, com o histórico das mensagens e decisões
relacionadas à solicitação do cliente. Durante seu andamento, possui uma única
fila operacional ativa pertencente à mesma marca.

**Fila de atendimento**:
Destino operacional configurável para os atendimentos de uma marca. Cada fila
pertence a exatamente uma marca e pode ter várias equipes responsáveis,
autorizadas para essa marca.
_Evitar_: fila de mensageria como sinônimo de fila de atendimento.

**Atendente**:
Participante que pode assumir a responsabilidade principal por um atendimento.
Pode ser um analista humano ou o atendente de IA simulado.

**Responsável principal**:
Atendente atualmente atribuído à condução de um atendimento. Existe no máximo
um responsável principal ativo por caso, independentemente da quantidade de
equipes responsáveis pela fila.

**Transferência de responsabilidade**:
Mudança do responsável principal de um atendimento, com preservação do histórico
da atribuição anterior.

**Responsabilidade de equipe por fila**:
Vínculo explícito de uma equipe com uma fila de atendimento da marca em que está
autorizada a atuar. A autorização na marca, sozinha, não estabelece esse vínculo.

**Fila atual**:
Única fila operacional na qual um atendimento está ativo em determinado momento.
Filas anteriores permanecem no histórico de transferências.

**Transferência de fila**:
Mudança da fila atual de um atendimento para outra fila, preservando o histórico
da passagem entre origem e destino.

**Visualização unificada**:
Listagem que reúne atendimentos de filas e marcas distintas respeitando as
permissões do analista e preservando a identificação da marca e da fila de cada
caso.

**Perfil de capacidade**:
Configuração operacional das combinações de prioridade e categoria que um
analista pode conduzir simultaneamente. Substitui a soma de pesos numéricos do
desenho anterior.

**Prioridade**:
Nível de urgência de um atendimento, usado na priorização e nas regras de
combinações configuradas pela operação. Não constitui medida de esforço ou
complexidade; os nomes e a ordem dos níveis ainda serão definidos.

**Categoria**:
Classificação do assunto de um atendimento, como Pix, repasse ou funcionamento
da maquininha. É usada junto da prioridade nas combinações; o catálogo definitivo
ainda será definido.

**Classificação do atendimento**:
Prioridade e categoria atribuídas a um caso. Esses valores alimentam as regras
de encaminhamento e de combinações de atendimento.

**Triagem**:
Caracterização inicial de uma solicitação para orientar sua classificação e
encaminhamento no atendimento.

**Carteira do analista**:
Conjunto de casos não concluídos sob responsabilidade principal de um analista,
incluindo trabalho ativo, espera pelo cliente e casos aguardando retomada.

**Limite de carteira**:
Teto de casos que o analista pode manter sob sua responsabilidade, incluindo
pendências. É distinto das combinações permitidas para trabalho simultâneo.

**Trabalho ativo**:
Atendimentos sob condução humana no contexto de marca em operação, sujeitos ao
perfil de capacidade. Distingue-se da responsabilidade por casos em espera.

**Retomada**:
Volta de um caso atribuído ao trabalho ativo após uma espera. Depende de
disponibilidade, marca em operação e compatibilidade com o perfil de capacidade.

**Desempate por maior tempo sem nova atribuição**:
Entre analistas empatados pelo critério principal de distribuição, preferência
por quem está há mais tempo sem receber uma atribuição.

**Marca em operação**:
Contexto de marca no qual o analista humano atua e pode receber novos casos
naquele momento. A autorização para várias marcas não implica atuação simultânea
em todas elas.

**Troca de marca em operação**:
Mudança do contexto operacional do analista para outra marca autorizada. Na V2,
pode preservar pendências de cliente de outra marca sem permitir atuação humana
simultânea em ambas.
