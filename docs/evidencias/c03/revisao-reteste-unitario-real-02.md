# C03-P2 · Revisão do reteste autorizado

O responsável autorizou uma nova chamada real, dentro do teto total de US$ 10.
Escopo: `jev-003` de desenvolvimento, uma requisição, duas perguntas, nenhuma
retentativa. Código histórico `38348ba6a0d0037540e4075f168353d4072f9682`.

Antes da execução, a revisão independente conferiu os hashes de configuração,
autorização, launcher, protocolo, fontes e política dos controles, além da
identidade canônica do modelo. A entrada do plano estático coincide byte a
byte com o piloto anterior, e o caso pertence à divisão de desenvolvimento.
A reserva pessimista de US$ 1,4004736 cabe no teto operacional de US$ 1,50 e
no teto humano global, considerados os valores conservadores locais.

O registro exclusivo foi criado antes da leitura da chave. Houve um único
lançamento, limite externo de 30 s com encerramento do grupo e proibição de
repetir a chamada. A chave permaneceu no ambiente do filho, sem argumento de
comando nem saída. A revisão foi de leitura, sem acesso à credencial ou API.

O integrador executou uma vez e conferiu uma observação/decisão, um POST e
duas perguntas; o modelo retornou `pix` e `urgent` em 1.894,437 ms. O log
oficial confirmou o segundo registro `OK`, US$ 0,000518; o resumo exibiu duas
requisições e US$ 0,00104. Não foram armazenados nomes de chaves, saldo ou
informações da conta. A reserva desconhecida do reteste foi conciliada pelo
recibo arredondado, com custo conservador de US$ 0,000519.

O relatório foi validado no checkout central pelo comando abaixo, sem
iniciar candidato:

```sh
rtk proxy python3 -B script/check_classification_contracts.py \
  --report script/classification_comparison/adapters/qwen/evidencia-reteste-real-02/report.json
```

Resultado: `OK: warm-1.0`. Os oito arquivos foram copiados sem alterações de
bytes e passaram por varredura da credencial em memória. O recibo independente
não altera o custo nulo do IPC original. A conclusão permanece inconclusiva,
sem holdout, p95, elegibilidade ou adoção; não houve nova inferência depois.
