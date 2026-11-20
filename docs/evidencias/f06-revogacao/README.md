# Reprodução do complemento administrativo F06/F07

Este é o suporte do ensaio externo de revogação, separado do runner dos cinco
cenários F07-A. Use somente uma pilha descartável de desenvolvimento com o
seed do projeto, `api` acessível na rede Docker e categorias `pix` e `payouts`
ativas na Aurora. O fixture acrescenta fila, duas equipes e um caso próprios.
Não o execute em um banco compartilhado de desenvolvimento ou produção.

1. Suba a pilha e prepare os bancos em sequência conforme [F06](../../f06.md).
   Configure apenas senhas sintéticas de Bia e supervisor em
   `CLOUDWALK_DEMO_PASSWORDS` da API. A API deve poder emitir avisos via Cable.
2. No contêiner da API, execute `bundle exec rails runner -`, fornecendo
   [fixture.rb](fixture.rb) pela entrada padrão. Copie o arquivo gerado
   `/tmp/cloudwalk-f06-admin-fixture.json` para o host.
3. Construa a imagem `probe` com a configuração [F07-A](../../../script/f07/compose.yml).
   Execute-a na rede da sua pilha, montando o repositório em `/workspace:ro`,
   o JSON em `/fixture.json:ro` e [probe.py](probe.py) em `/probe.py:ro`.
   Defina `PYTHONPATH=/workspace/script/f07` e execute
   `python -B /probe.py /fixture.json`.
4. Forneça pela entrada padrão um objeto JSON com somente as senhas
   sintéticas dos e-mails `bia@example.test` e `supervisor@example.test`.
   Não grave esse objeto na evidência nem no histórico do terminal.
5. Salve stdout em JSON. Exija `status: aprovado`, três controles posteriores
   auditados, sessão do analista ainda autenticada, REST negado e a observação
   da assinatura anterior. Se faltar uma condição, conserve o diagnóstico;
   não conte o ensaio como aprovado.
6. Remova somente a pilha descartável e seus volumes após o ensaio.

O resultado de 2026-11-20 está em [f06-revogacao-2026-11-20.json](../f06-revogacao-2026-11-20.json).
O probe usa o mesmo cliente HTTP e WebSocket do verificador. A janela finita
observada é evidência de isolamento nesse ensaio, sem representar um SLA.
