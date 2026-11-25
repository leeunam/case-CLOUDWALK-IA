# C05-R2 · revisão independente da Task 2

**Especificação — aprovada para a autoria do conjunto final. Qualidade dos rótulos — aprovada como referência exploratória de IA.** O agente revisor concordou com os 48 alvos dos 36 casos. Nenhuma divergência requer decisão do responsável. A similaridade com os casos antigos tem revisão própria. Esta verificação não representa aprovação humana nem mede comportamento de candidato.

A revisão ocorreu em `.worktrees/r2-dados`, branch `docs/r2-protocolo-dados`, entre a base `c00ac5431630c92d30349c13529d5071ad9879b4` e a entrega `29973d74209796c54076fcaf9348c14a37ab1743`. O pacote de diff identifica dois novos arquivos. Seus identificadores de blob correspondem aos do commit. Os SHA-256 calculados coincidem com os relatados e a autoria fixa o SHA-256 do conjunto.

| Arquivo | SHA-256 |
| --- | --- |
| `final-cases.json` | `de29a2de28e9b643dfe82eff97ef54263afa3eca7ad0b8642f5c3fc4ee22d4b8` |
| `data-authorship.json` | `e52d30e64d6579f8893d7625fea6d0b02ba758b5bf6454d19d4ae689e1ddc2eb` |

## Especificação

O cabeçalho registra versão 2.0.0, língua pt-BR e estado de autoria pendente. Os IDs percorrem r2-001 a r2-036. Os alvos solicitados, a ordem de `expected` e os campos recebidos concordam com as três máscaras após considerar omissão, nulo e texto em branco. Os 24 valores fornecidos pertencem ao catálogo. A documentação de autoria identifica o agente, a base, as fontes, o método e as restrições declaradas. Essa origem é autodeclarada pelo autor.

| Máscara | Casos | Classificáveis | Revisão | Urgentes entre os alvos |
| --- | ---: | ---: | ---: | ---: |
| Categoria | 12 | 10 | 2 | 0 |
| Prioridade | 12 | 10 | 2 | 3 |
| Dupla | 12 | 9 | 3 | 3 |

Há cinco categorias insuficientes e três prioridades insuficientes, com uma sobreposição. Dos seis urgentes com prioridade omitida, dois são duplos classificáveis e um é duplo para revisão. Os estratos totalizam 24 de rotina, cinco urgentes e sete ambíguos. A diferença entre as seis prioridades urgentes e os cinco casos de estrato urgente decorre da abstenção em categoria de r2-034.

## Qualidade semântica

O revisor `/root/r2_revisar_dados` examinou os relatos, os campos recebidos, os alvos e as justificativas de autoria. Confrontou cada alvo com a rubrica comum 1.0.0 e o catálogo 1.0.0. O arquivo `task-2-label-review.json` registra por ID os códigos conferidos, a decisão e a evidência. A revisão avaliou as classificações já propostas com acesso ao gabarito. A autoria é do agente distinto `/root/r2_autor_dados`. A revisão aconteceu após o congelamento comunicado pelo integrador e sem executar candidatos.

| Relevância | Referências | Fundamentação |
| --- | --- | --- |
| Alta · abstenções | r2-011, 012, 017, 024, 034–036 · rubrica, linhas 14–15 e 27–29 | Nos cinco alvos de categoria falta o serviço específico. Nos três alvos de prioridade faltam fatos que permitam avaliar impacto ou prazo. Em r2-034 e r2-035 há evidência independente para a prioridade e a abstenção em categoria mantém o caso em revisão. |
| Alta · urgentes | r2-014, 019, 022, 028, 032, 034 · rubrica, linhas 25–26 | Cada urgência decorre de perda em curso, paralisação sem alternativa ou consequência relevante com prazo imediato. |
| Média · fronteira de impacto | r2-015, 016, 020, 021, 023, 026, 027, 030, 031, 033 · rubrica, linhas 22–24 e 31–34 | Nos casos intermediários, o relato circunscreve o prejuízo e preserva uma via de operação. Nos avançados, a abrangência ou o retrabalho do cliente sustentam o nível mesmo com continuidade do serviço. |
| Média · linguagem e assunto | r2-003, 006, 011 · rubrica, linhas 11–15 | A finalidade e o mecanismo de transferência sustentam as duas classificações em Pix. O QR isolado em r2-011 deixa a função indeterminada. |

Nenhum achado bloqueador, importante ou menor requer alteração da entrega. Esta revisão usou leitura semântica, inspeção dos campos e verificação dos pins. Os testes estruturais registrados no relatório de autoria não foram reexecutados. A revisão de similaridade e as etapas de integração são responsabilidades separadas.
