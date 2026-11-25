"""Consulta os dois casos F10-A na publicação, com um contexto Chromium por analista."""

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from playwright.sync_api import Error as BrowserError, sync_playwright

WORKTREE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKTREE / "script"))
from publish import ORIGIN as TUNNEL_ORIGIN, PASSWORD_KEY, PublishError, private_env

MANIFEST = "docs/evidencias/f10/fluxo-publico/cases.json"
PUBLIC_ORIGIN = re.compile(TUNNEL_ORIGIN)
AURORA = "11111111-1111-4111-8111-111111111111"
HORIZONTE = "22222222-2222-4222-8222-222222222222"
DENIED = {"error": {"code": "not_found", "message": "Atendimento não encontrado."}}

# No painel, o socket só abre após carregar o detalhe. Para o controle negativo,
# observamos a decisão do canal diretamente, com o cookie do mesmo contexto.
SUBSCRIBE = """({id, allowed}) => new Promise(resolve => {
  const ws = new WebSocket('wss://' + location.host + '/cable', 'actioncable-v1-json');
  const identifier = JSON.stringify({channel: 'CaseUpdatesChannel', case_id: id, audience: 'staff'});
  let settled = false;
  const finish = result => {
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    resolve(result);
    try { ws.close(); } catch {}
  };
  const timer = setTimeout(() => finish('timeout'), 12000);
  ws.onerror = () => finish('erro de transporte');
  ws.onclose = () => finish('fechamento sem decisão');
  ws.onmessage = event => {
    if (settled) return;
    let frame;
    try { frame = JSON.parse(event.data); } catch { return finish('quadro inválido'); }
    if (!frame || typeof frame !== 'object') return finish('quadro inválido');
    if (frame.type === 'welcome') ws.send(JSON.stringify({command: 'subscribe', identifier}));
    if (frame.identifier !== identifier) return;
    if (!allowed && Object.hasOwn(frame, 'message')) return finish('dados da assinatura restrita');
    if (['confirm_subscription', 'reject_subscription'].includes(frame.type)) finish(frame.type);
  };
})"""


class CheckError(Exception):
    def __init__(self, phase, status=None):
        self.phase = phase
        self.status = status
        super().__init__(phase if status is None else f"{phase} (HTTP {status})")


def git(*args, raw=False):
    output = subprocess.check_output(["rtk", "proxy", "git", *args], cwd=WORKTREE, stderr=subprocess.DEVNULL)
    return output if raw else output.decode().strip()


def publication_origin(data):
    if (not isinstance(data, dict) or data.get("task") != "F10-I" or data.get("state") != "restored"
            or data.get("public_https_health") != "passed" or data.get("images_unchanged") is not True):
        raise ValueError("Registro de restabelecimento inválido.")
    origin = data.get("origin")
    if not isinstance(origin, str) or not PUBLIC_ORIGIN.fullmatch(origin):
        raise ValueError("Origem HTTPS inválida no registro de restabelecimento.")
    return origin


def api_response(send, url, phase, **kwargs):
    try:
        return send(url, max_redirects=0, **kwargs)
    except BrowserError:
        raise CheckError(phase) from None


def json_body(response, phase, expected_status=None):
    if expected_status is not None and response.status != expected_status:
        raise CheckError(phase, response.status)
    try:
        data = response.json()
    except (BrowserError, ValueError):
        raise CheckError(phase, response.status) from None
    if not isinstance(data, dict):
        raise CheckError(phase, response.status)
    return data


def login_actor(context, actor, password, origin):
    if not isinstance(origin, str) or not PUBLIC_ORIGIN.fullmatch(origin):
        raise CheckError("origem da publicação")
    client = context.request
    url = origin + "/api/v1/session"
    phase = "sessão anônima"
    bootstrap = api_response(client.get, url, phase)
    anonymous = json_body(bootstrap, phase, expected_status=200)
    token = anonymous.get("csrf_token")
    if "user" not in anonymous or anonymous["user"] is not None or not isinstance(token, str) or not token:
        raise CheckError(phase, bootstrap.status)

    phase = "login"
    login = api_response(client.post, url, phase, data={"email": actor.lower() + "@example.test", "password": password},
                         headers={"Origin": origin, "X-CSRF-Token": token})
    if login.status != 200:
        raise CheckError(phase, login.status)

    phase = "confirmação de identidade"
    identity = api_response(client.get, url, phase)
    session = json_body(identity, phase, expected_status=200)
    user = session.get("user")
    if not isinstance(user, dict) or user.get("name") != actor or user.get("role") != "analyst":
        raise CheckError(phase, identity.status)
    return session


def record(actor, case, operation, expected, observed, state):
    print(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "ator": actor,
                      "caso": case, "operação": operation, "esperado": expected,
                      "observado": observed, "resultado": state}, ensure_ascii=False), flush=True)
    return state == "passou"


def case_list(client, api):
    cases = {}
    params = {"limit": 100}
    cursors = set()
    phase = "listagem unificada completa"
    while True:
        response = api_response(client.get, api + "/cases", phase, params=params)
        data = json_body(response, phase, expected_status=200)
        try:
            cases.update((item["id"], item["brand_id"]) for item in data["items"])
            cursor = data["next_cursor"]
        except (KeyError, TypeError):
            raise CheckError(phase, response.status) from None
        if cursor is None:
            return cases
        if not isinstance(cursor, str) or not cursor or cursor in cursors:
            raise CheckError(phase, response.status)
        cursors.add(cursor)
        params["cursor"] = cursor


def history_contains(client, url, marker):
    after_sequence = 0
    phase = "histórico"
    while True:
        response = api_response(client.get, url, phase, params={"after_sequence": after_sequence})
        if response.status != 200:
            return response.status, False
        data = json_body(response, phase)
        try:
            if any(marker in item["text"] for item in data["items"]):
                return response.status, True
            next_sequence = data["next_after_sequence"]
        except (KeyError, TypeError):
            raise CheckError(phase, response.status) from None
        if next_sequence is None:
            return response.status, False
        if type(next_sequence) is not int or next_sequence <= after_sequence:
            raise CheckError("paginação do histórico", response.status)
        after_sequence = next_sequence


def inspect_actor(context, actor, password, cases, origin):
    session = login_actor(context, actor, password, origin)
    api = origin + "/api/v1"
    client = context.request
    expected_brands = {AURORA} if actor == "Bia" else {AURORA, HORIZONTE}
    phase = "sessão e filas"
    response = api_response(client.get, api + "/case-filters", phase)
    catalog = json_body(response, phase, expected_status=200)
    try:
        brands = set(session["user"]["brand_ids"])
        queue_brands = {q["brand_id"] for q in catalog["queues"]}
        matches = brands == queue_brands == {b["id"] for b in catalog["brands"]} == expected_brands
        active = (session["operation"] or {}).get("active_brand_id")
    except (AttributeError, KeyError, TypeError):
        raise CheckError(phase, response.status) from None
    ok = record(actor, None, "sessão e filas", sorted(expected_brands),
                {"brand_ids": sorted(brands), "marcas_das_filas": sorted(queue_brands),
                 "ativa": active}, "passou" if matches else "divergiu")
    if not matches:
        return False

    visible = case_list(client, api)
    ok &= record(actor, None, "listagem unificada completa", "somente marcas autorizadas",
                 {"há_marca_fora_do_escopo": bool(set(visible.values()) - brands)},
                 "passou" if set(visible.values()) <= brands else "falhou")
    try:
        page = context.new_page()
    except BrowserError:
        raise CheckError("abertura do painel") from None
    for case_id, brand, marker in cases:
        allowed = brand in brands
        present = case_id in visible
        correct = (visible.get(case_id) == brand) if allowed else not present
        ok &= record(actor, case_id, "listagem", allowed, present, "passou" if correct else "falhou")
        for suffix in ("", "/messages"):
            phase = "histórico" if suffix else "detalhe direto"
            url = api + "/cases/" + case_id + suffix
            if allowed and suffix:
                status, has_marker = history_contains(client, url, marker)
                valid = status == 200 and has_marker
                observed = {"HTTP": status, "marcador_do_manifesto": has_marker}
                expected = "200 com mensagem do caso"
            elif not allowed:
                response = api_response(client.get, url, phase)
                status = response.status
                try:
                    generic_error = status == 404 and json_body(response, phase) == DENIED
                except CheckError:
                    generic_error = False
                valid = generic_error
                observed = {"HTTP": status, "somente_erro_genérico": generic_error}
                expected = "404 not_found genérico"
            else:
                response = api_response(client.get, url, phase)
                status = response.status
                data = json_body(response, phase) if status == 200 else {}
                same = data.get("id") == case_id and data.get("brand_id") == brand
                valid = status == 200 and same
                observed = {"HTTP": status, "id_e_marca_conferem": same}
                expected = "200 com ID e marca do manifesto"
            state = "passou" if valid else "falhou"
            if status >= 500 or 300 <= status < 400 or status in (401, 429):
                state = "inconclusivo"
            ok &= record(actor, case_id, phase, expected, observed, state)
        panel_url = origin + "/analista?case=" + case_id
        phase = "link direto no painel"
        try:
            navigation = page.goto(panel_url, wait_until="domcontentloaded")
        except BrowserError:
            raise CheckError(phase) from None
        if page.url != panel_url:
            raise CheckError(phase, navigation.status if navigation else None)
        history = page.get_by_role("region", name="Histórico da conversa")
        expected_text = marker if allowed else DENIED["error"]["message"]
        try:
            history.get_by_text(expected_text, exact=False).first.wait_for(timeout=8000)
            exposed = history.get_by_role("listitem").count() > 0 or page.locator("#case-context").count() > 0
            valid = allowed or not exposed
            ui_result = "histórico do caso" if allowed else ("dados exibidos" if exposed else "erro genérico")
            ui_state = "passou" if valid else "falhou"
        except BrowserError:
            exposed = history.get_by_role("listitem").count() > 0 or page.locator("#case-context").count() > 0
            ui_result = "dados exibidos" if not allowed and exposed else "resultado esperado ausente"
            ui_state = "falhou" if not allowed and exposed else "inconclusivo"
        ok &= record(actor, case_id, phase, expected_text, ui_result, ui_state)
        if page.url != panel_url:
            raise CheckError(phase)
        try:
            frame = page.evaluate(SUBSCRIBE, {"id": case_id, "allowed": allowed})
        except BrowserError:
            frame = "erro de transporte"
        expected = "confirm_subscription" if allowed else "reject_subscription"
        state = "passou" if frame == expected else "falhou"
        if frame not in ("reject_subscription", "confirm_subscription", "dados da assinatura restrita"):
            state = "inconclusivo"
        ok &= record(actor, case_id, "Action Cable", expected, frame, state)
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit", help="commit do manifesto F10-A")
    parser.add_argument("--publication-record", required=True, type=Path,
                        help="JSON do registro confiável de restabelecimento do túnel")
    args = parser.parse_args()
    try:
        publication_bytes = args.publication_record.read_bytes()
        origin = publication_origin(json.loads(publication_bytes))
    except (OSError, ValueError):
        parser.error("O registro de publicação precisa comprovar o restabelecimento em uma origem HTTPS trycloudflare.com.")

    try:
        revision = git("rev-parse", "--verify", "--end-of-options", args.commit + "^{commit}")
        manifest_bytes = git("show", revision + ":" + MANIFEST, raw=True)
        manifest = json.loads(manifest_bytes)
        creation_url = manifest["url"]
        if not isinstance(creation_url, str) or not PUBLIC_ORIGIN.fullmatch(creation_url.removesuffix("/")):
            parser.error("O manifesto precisa informar a URL de criação dos casos.")
        cases = []
        for key, brand in (("aurora_chat", AURORA), ("horizonte_control", HORIZONTE)):
            item = manifest[key]
            marker = item["marker"]
            if not isinstance(marker, str) or not marker.strip():
                parser.error("Marcador ausente no manifesto.")
            cases.append((str(UUID(item["case_id"])), brand, marker))
    except (subprocess.CalledProcessError, AttributeError, KeyError, TypeError, ValueError):
        parser.error("O manifesto precisa conter os dois IDs válidos no commit informado.")
    if cases[0][0] == cases[1][0]:
        parser.error("Os dois casos precisam ter IDs distintos.")
    print(json.dumps({"manifesto": revision, "manifesto_sha256": sha256(manifest_bytes).hexdigest(),
                      "registro_publicacao_sha256": sha256(publication_bytes).hexdigest(),
                      "url_criacao": creation_url, "url_consulta": origin, "origem": "computador de execução",
                      "método": "Chromium, HTTPS e WSS, contextos independentes"}, ensure_ascii=False), flush=True)
    root = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir")).parent
    with private_env(root / ".env.publish.local") as settings:
        passwords = json.loads(settings[PASSWORD_KEY])
    ok = True
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome" if shutil.which("google-chrome") else None)
        for actor in ("Bia", "Cris", "Alex"):
            context = browser.new_context()
            context.set_default_timeout(12000)
            try:
                ok &= inspect_actor(context, actor, passwords[actor.lower() + "@example.test"], cases, origin)
            except CheckError as error:
                observed = {"fase": error.phase}
                if error.status is not None:
                    observed["HTTP"] = error.status
                ok &= record(actor, None, "execução interrompida", "sessão e consultas completas",
                             observed, "inconclusivo")
            except (BrowserError, ValueError, KeyError, TypeError) as error:
                ok &= record(actor, None, "execução interrompida", "sessão e consultas completas",
                             type(error).__name__, "inconclusivo")
            finally:
                context.close()
        browser.close()
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (BrowserError, OSError, PublishError, ValueError) as error:
        sys.exit("Execução bloqueada antes de concluir a matriz: " + type(error).__name__)
