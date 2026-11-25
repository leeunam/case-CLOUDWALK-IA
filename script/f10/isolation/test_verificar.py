import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from hashlib import sha256
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import verificar


ORIGIN = "https://test-restored.trycloudflare.com"
CREATION_URL = "https://test-original.trycloudflare.com/"
RECORD = {"task": "F10-I", "origin": ORIGIN, "state": "restored",
          "public_https_health": "passed", "images_unchanged": True}
CASES = (("ad4a4699-5d96-4cce-a248-96b3568447fc", verificar.AURORA, "F10-CLIENTE"),
         ("32ab943b-2bea-428f-adb7-a802fe53bfaf", verificar.HORIZONTE, "F10-HORIZONTE"))
MANIFEST = {"url": CREATION_URL, "aurora_chat": {"case_id": CASES[0][0], "marker": CASES[0][2]},
            "horizonte_control": {"case_id": CASES[1][0], "marker": CASES[1][2]}}


def response(data, status=200):
    return Mock(status=status, json=Mock(return_value=data))


class VerificadorTests(unittest.TestCase):
    def test_rejeita_destino_invalido_antes_de_abrir_credenciais(self):
        invalid_origins = [ORIGIN + suffix for suffix in ("/", ":443", "/path", "?a=b", "#x", ".evil.test", "\n")]
        invalid_origins += [ORIGIN.replace("https:", "http:"), ORIGIN.replace("://", "://user@"),
                            "https://trycloudflare.com", "https://multi.label.trycloudflare.com", None]
        invalid_records = [dict(RECORD, origin=origin) for origin in invalid_origins]
        invalid_records += [None, [], dict(RECORD, state="stopped"), dict(RECORD, public_https_health="failed"),
                            dict(RECORD, images_unchanged=1), dict(RECORD, task="F10-A")]
        payloads = [json.dumps(record) for record in invalid_records] + ["{ JSON incompleto"]
        with tempfile.TemporaryDirectory() as directory:
            record_path = Path(directory) / "restabelecimento.json"
            with (patch.object(verificar, "private_env") as load_private,
                  patch.object(verificar, "sync_playwright") as playwright,
                  patch.object(sys, "argv", ["verificar.py", "manifesto", "--publication-record", str(record_path)]),
                  redirect_stderr(io.StringIO())):
                for payload in payloads:
                    with self.subTest(payload=payload), self.assertRaises(SystemExit) as error:
                        record_path.write_text(payload, encoding="utf-8")
                        verificar.main()
                    self.assertEqual(error.exception.code, 2)
                load_private.assert_not_called()
                playwright.assert_not_called()

    def test_login_antes_do_painel_em_contextos_separados(self):
        manifest_bytes = json.dumps(MANIFEST).encode()
        publication_bytes = json.dumps(RECORD).encode()
        contexts = [self.actor_context(actor) for actor in ("Bia", "Cris", "Alex")]
        playwright = MagicMock()
        browser = playwright.__enter__.return_value.chromium.launch.return_value
        browser.new_context.side_effect = contexts
        passwords = {f"{actor}@example.test": f"senha-falsa-{actor}" for actor in ("bia", "cris", "alex")}
        settings = {verificar.PASSWORD_KEY: json.dumps(passwords)}
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            record_path = Path(directory) / "restabelecimento.json"
            record_path.write_bytes(publication_bytes)
            with (patch.object(verificar, "git", side_effect=["rev", manifest_bytes, directory]),
                  patch.object(verificar, "private_env", return_value=nullcontext(settings)),
                  patch.object(verificar, "sync_playwright", return_value=playwright),
                  patch.object(sys, "argv", ["verificar.py", "manifesto", "--publication-record", str(record_path)]),
                  redirect_stdout(output)):
                self.assertEqual(verificar.main(), 1)
        header, *entries = map(json.loads, output.getvalue().splitlines())
        self.assertEqual(header["url_criacao"], CREATION_URL)
        self.assertEqual(header["url_consulta"], ORIGIN)
        self.assertEqual(header["manifesto_sha256"], sha256(manifest_bytes).hexdigest())
        self.assertEqual(header["registro_publicacao_sha256"], sha256(publication_bytes).hexdigest())
        self.assertEqual(browser.new_context.call_count, 3)
        for context, actor in zip(contexts, ("bia", "cris", "alex")):
            session_url = f"{ORIGIN}/api/v1/session"
            email = f"{actor}@example.test"
            self.assertEqual(context.mock_calls[1:4], [
                call.request.get(session_url, max_redirects=0),
                call.request.post(session_url, max_redirects=0, data={"email": email, "password": passwords[email]},
                                  headers={"Origin": ORIGIN, "X-CSRF-Token": f"csrf-{actor}"}),
                call.request.get(session_url, max_redirects=0),
            ])
            self.assertGreater(context.mock_calls.index(call.new_page()), 3)
            self.assertTrue(all(request.kwargs["max_redirects"] == 0 for request in context.request.get.call_args_list))
            context.close.assert_called_once_with()
        failed = [entry for entry in entries if entry["resultado"] != "passou"]
        self.assertEqual([(entry["ator"], entry["caso"], entry["operação"], entry["resultado"]) for entry in failed],
                         [("Bia", CASES[1][0], "Action Cable", "falhou")])
        self.assertNotIn("senha-falsa", output.getvalue())
        self.assertNotIn("csrf-", output.getvalue())

    @staticmethod
    def actor_context(actor):
        context = MagicMock()
        brands = [verificar.AURORA] if actor == "Bia" else [verificar.AURORA, verificar.HORIZONTE]
        replies = [
            response({"user": None, "csrf_token": f"csrf-{actor.lower()}"}),
            response({"user": {"name": actor, "role": "analyst", "brand_ids": brands}, "operation": None}),
            response({"brands": [{"id": brand} for brand in brands], "queues": [{"brand_id": brand} for brand in brands]}),
            response({"items": [{"id": case_id, "brand_id": brand} for case_id, brand, _ in CASES if brand in brands],
                      "next_cursor": None}),
        ]
        for case_id, brand, marker in CASES:
            if brand in brands:
                replies += [response({"id": case_id, "brand_id": brand}),
                            response({"items": [{"text": marker}], "next_after_sequence": None})]
            else:
                replies += [response(verificar.DENIED, 404), response(verificar.DENIED, 404)]
        context.request.get.side_effect = replies
        context.request.post.return_value = response({})
        page = context.new_page.return_value
        page.goto.side_effect = lambda url, **_: setattr(page, "url", url)
        page.get_by_role.return_value.get_by_role.return_value.count.return_value = 0
        page.locator.return_value.count.return_value = 0
        page.evaluate.side_effect = lambda _, args: (
            "confirm_subscription" if args["allowed"] else "dados da assinatura restrita"
        )
        return context

    def test_redirect_no_login_preserva_fase_e_status_sem_corpo(self):
        context = Mock()
        context.request.get.return_value = response({"user": None, "csrf_token": "csrf-falso"})
        unexpected = response({"private": "conteúdo sintético"}, 307)
        context.request.post.return_value = unexpected
        with self.assertRaises(verificar.CheckError) as error:
            verificar.login_actor(context, "Bia", "senha-falsa", ORIGIN)
        self.assertEqual(str(error.exception), "login (HTTP 307)")
        context.request.get.assert_called_once()
        unexpected.json.assert_not_called()
        context.new_page.assert_not_called()

    def test_historico_encontra_marcador_na_pagina_seguinte_e_protege_cursor(self):
        client = Mock()
        url = ORIGIN + "/api/v1/cases/id/messages"
        first_page = response({"items": [{"text": "outra mensagem"}], "next_after_sequence": 25})
        client.get.side_effect = [first_page, response({"items": [{"text": "F10"}], "next_after_sequence": None})]
        self.assertEqual(verificar.history_contains(client, url, "F10"), (200, True))
        self.assertEqual(client.get.call_args_list, [call(url, max_redirects=0, params={"after_sequence": cursor})
                                                    for cursor in (0, 25)])
        for next_cursor in (25, 24, -1, False, "26"):
            with self.subTest(cursor=next_cursor):
                client.get.side_effect = [first_page, response({"items": [], "next_after_sequence": next_cursor})]
                with self.assertRaises(verificar.CheckError) as error:
                    verificar.history_contains(client, url, "F10")
                self.assertEqual(str(error.exception), "paginação do histórico (HTTP 200)")
        client.get.side_effect = [first_page, response({}, 429)]
        self.assertEqual(verificar.history_contains(client, url, "F10"), (429, False))

    def test_action_cable_resolve_pela_decisao_do_identificador(self):
        javascript = "const subscribe = " + verificar.SUBSCRIBE + ";\n" + r"""
const assert = require('node:assert/strict');
let socket, timeout;
global.location = {host: 'test-restored.trycloudflare.com'};
global.setTimeout = callback => { timeout = callback; return 1; };
global.clearTimeout = () => {};
global.WebSocket = class {
  constructor(url, protocol) {
    assert.equal(url, 'wss://test-restored.trycloudflare.com/cable');
    assert.equal(protocol, 'actioncable-v1-json');
    socket = this;
  }
  send(raw) { this.identifier = JSON.parse(raw).identifier; }
  close() { this.onclose(); throw new Error('falha simulada ao fechar'); }
};
const probe = async (allowed, frames, expected) => {
  const result = subscribe({id: 'case-id', allowed});
  socket.onmessage({data: JSON.stringify({type: 'welcome'})});
  assert.deepEqual(JSON.parse(socket.identifier), {channel: 'CaseUpdatesChannel', case_id: 'case-id', audience: 'staff'});
  for (const frame of frames) {
    if (frame === 'timeout') timeout();
    else if (frame === 'erro') socket.onerror();
    else if (frame === 'fechamento') socket.onclose();
    else socket.onmessage({data: JSON.stringify({identifier: socket.identifier, ...frame})});
  }
  assert.equal(await result, expected);
};
process.exitCode = 1;
(async () => {
  const confirm = {type: 'confirm_subscription'};
  const reject = {type: 'reject_subscription'};
  const data = {message: {private: 'conteúdo sintético'}};
  await probe(false, [data, reject], 'dados da assinatura restrita');
  await probe(false, [reject], 'reject_subscription');
  await probe(false, [confirm], 'confirm_subscription');
  await probe(true, [data, confirm], 'confirm_subscription');
  await probe(false, [{...data, identifier: 'outra assinatura'}, reject], 'reject_subscription');
  await probe(false, [{...reject, identifier: 'outra assinatura'}, 'timeout'], 'timeout');
  await probe(false, ['erro'], 'erro de transporte');
  await probe(false, ['fechamento'], 'fechamento sem decisão');
  process.exitCode = 0;
})().catch(console.error);
"""
        subprocess.run(["rtk", "proxy", "node", "-"], input=javascript, text=True, check=True, timeout=5)
