# C05-R5 · Candidata Luna com evidência

A candidata mantém o modelo Luna e faz uma chamada por caso elegível. O
catálogo, o relato e os campos válidos do canal compõem a entrada. O modelo
propõe código, critério e citação por campo ausente. O IPC 1.1.0 vai dentro de
um envelope privado R5 1.0.0 com a auditoria. A decisão comum preserva
os campos do canal e envia o caso para revisão se faltar uma predição.

## Auditoria

O hash de entrada usa JSON com chaves ordenadas, separadores sem espaços e
UTF-8. As posições são índices de caracteres no relato original, com início
inclusivo e fim exclusivo. O envelope guarda a string original de
`message.content`, o `finish_reason` e o `message.refusal` quando acessíveis.
Uma recusa explícita da API pode chegar apenas em `message.refusal`. Esse
metadado permite reproduzir a abstenção de política com conteúdo nulo.

Uma resposta malformada encerra a sessão. Quando o formato privado de algum
campo falha, a auditoria conserva as partes acessíveis de todos os campos e a
política deixa de interpretar as relações daquele conjunto. Respostas bem
formadas com suporte insuficiente seguem como abstenção com motivo de veto.
Mesmo em revisão, o envelope guarda as propostas e seus motivos por campo.

## Alcance da política

As relações buscam operações de Pix, recebimento associado a vendas e funções
de um equipamento de pagamento identificável. A parte citada precisa conter
uma relação reconhecida em uma oração. A leitura do relato inteiro verifica
hipóteses, exclusões de assunto, transições de foco, impactos e alternativas.
Urgência por prazo exige uma consequência e expressão de tempo reconhecidas.
Os prazos numéricos em minutos cobrem de 1 a 60. O catálogo só habilita
predição para definições reconhecidas textualmente. Novos códigos e
definições diferentes vão para revisão quando preditos.

Os padrões são limitados ao português e às construções registradas no módulo.
Sarcasmo, elipse, referência indireta e escopo incomum de negação podem causar
veto indevido ou passar pelo filtro. A citação e sua posição atestam origem
textual. A suficiência semântica continua sujeita aos rótulos da avaliação.

O prazo monotônico inclui reserva, transporte, interpretação e validação do
envelope. Quando a verificação local ultrapassa o prazo, a observação vira
erro de timeout e preserva a resposta e o uso disponíveis. A requisição pede
384 tokens de saída. O orçamento injetado mantém a reserva faturável máxima.
O ensaio sintético injeta um gateway sem uso de rede, com eventos de reserva,
recepção e encerramento observáveis.

## Reprodução offline

Na raiz do repositório, execute

~~~sh
rtk proxy env PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=script/classification_comparison:script/classification_comparison/adapters/qwen \
    python -m unittest adapters.luna.r5.test_evidence -v
~~~

Para ver a diferença entre citação e suporte, rode
`test_trecho_e_contexto_mudam_veto_e_independem_do_id` isoladamente e compare
as entradas que repetem a mesma citação com continuações diferentes.
