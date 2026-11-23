# Pré-voo público dos candidatos

Consulta do integrador em **23 de novembro de 2026**, sem autenticação,
chamada de inferência, criação de chave ou consumo de créditos. Este registro
prepara C03/C04; não substitui seus pilotos nem autoriza gasto.

## Qwen pela Feita

A [página oficial do candidato](https://feita.ai/models/qwen/qwen3.8-27b)
foi consultada no navegador, nas abas Overview, API e Parameters. O catálogo
mostrava o identificador `qwen/qwen3.8-27b` e suporte anunciado a saída
estruturada. A presença no catálogo não comprova disponibilidade numa conta
ou uma chamada bem-sucedida.

- Base HTTP: `https://api.feita.ai/gateway/v1`.
- Operação documentada: `POST /chat/completions`, com autenticação Bearer
  pela variável local `FEITA_API_KEY`.
- A resposta de exemplo contém o modelo retornado e `usage.prompt_tokens`,
  `completion_tokens`, `total_tokens`, `cost` e `credits`. São campos do
  exemplo documental, ainda sem observação de uma cobrança real.
- Parâmetros anunciados incluem `response_format`, `structured_outputs`,
  `max_tokens`, `temperature`, `seed` e controles de raciocínio. C03 deve
  validar o formato e o efeito efetivamente suportados antes do piloto.

| Tarifa exibida | USD por milhão de tokens |
| --- | ---: |
| Entrada | 0,425 |
| Saída | 2,55 |
| Leitura de cache | 0,085 |
| Escrita de cache | 0,531 |

O catálogo informa conversão de um crédito para US$ 0,01. Não foi consultado
saldo da conta. Tarifas podem mudar: confirmar antes de estimar e autorizar
o lote. O teto monetário do protocolo permanece nulo e a autorização de
execução paga permanece falsa. A chave não está configurada no ambiente
do integrador.

## GLiClass local

O [model card oficial](https://huggingface.co/knowledgator/gliclass-multilang-mini)
e os metadados públicos do Hugging Face informavam:

- Modelo: `knowledgator/gliclass-multilang-mini`.
- Revisão: `0bd888b6c3ef9fca5f0a9d407bddfbbc7623486b`.
- Licença anunciada: Apache-2.0; repositório público, sem aprovação de acesso.
- Metadados Safetensors: 283.736.833 parâmetros em BF16. O tamanho efetivo
  dos arquivos ainda deve ser registrado no download, sem substituir bytes
  medidos por uma estimativa a partir dos parâmetros.
- O model card inclui português, descrições de rótulos e instruções de tarefa.
  O adaptador deve registrar como representa a rubrica comum e suas limitações.

O [projeto da biblioteca](https://github.com/Knowledgator/GLiClass) e seu
[manifesto de dependências](https://github.com/Knowledgator/GLiClass/blob/main/pyproject.toml)
foram consultados. A versão observada da linha principal exige Python 3.10
ou superior, PyTorch 2 ou superior e Transformers 5 ou superior. Isso não
constitui um lockfile: C04 deve fixar versões compatíveis e verificadas.

O host dispõe de Python 3.11, mas não tem `torch`, `transformers` ou
`gliclass` instalados. Na inspeção inicial havia aproximadamente 18 GB livres
em disco e 15 GiB de RAM total. Revalidar recursos antes do piloto, instalar
em ambiente isolado e preferir dependências CPU quando não houver GPU
confirmada. Nenhum peso foi baixado e nenhuma inferência foi executada neste
pré-voo. A instalação e o piloto dependem do aceite C02 e devem ser seriais
com os outros ensaios de desempenho.
