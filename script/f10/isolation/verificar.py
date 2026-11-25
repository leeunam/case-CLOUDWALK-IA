"""Consulta os dois casos F10-A na publicação, com um contexto Chromium por analista."""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from playwright.sync_api import Error as BrowserError, sync_playwright

WORKTREE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKTREE / "script"))
from publish import PASSWORD_KEY, private_env

ORIGIN = "https://newbie-aqua-stem-reveal.trycloudflare.com"
API = ORIGIN + "/api/v1"
MANIFEST = "docs/evidencias/f10/fluxo-publico/cases.json"
AURORA = "11111111-1111-4111-8111-111111111111"
HORIZONTE = "22222222-2222-4222-8222-222222222222"
DENIED = {"error": {"code": "not_found", "message": "Atendimento não encontrado."}}

# No painel, o socket só abre após carregar o detalhe. Para o controle negativo,
# observamos a decisão do canal diretamente, com o cookie do mesmo contexto.
SUBSCRIBE = """id => new Promise(resolve => {
  const ws = new WebSocket('wss://' + location.host + '/cable', 'actioncable-v1-json');
  const identifier = JSON.stringify({channel: 'CaseUpdatesChannel', case_id: id, audience: 'staff'});
  const finish = result => { clearTimeout(timer); resolve(result); ws.close(); };
  const timer = setTimeout(() => finish('timeout'), 12000);
  ws.onerror = () => finish('erro de transporte');
  ws.onclose = () => finish('fechamento sem decisão');
  ws.onmessage = event => {
    const frame = JSON.parse(event.data);
    if (frame.type === 'welcome') ws.send(JSON.stringify({command: 'subscribe', identifier}));
    if (frame.identifier === identifier && ['confirm_subscription', 'reject_subscription'].includes(frame.type))
      finish(frame.type);
  };
})"""


def git(*args):
    return subprocess.check_output(["rtk", "proxy", "git", *args], cwd=WORKTREE, text=True).strip()


def record(actor, case, operation, expected, observed, state):
    print(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "ator": actor,
                      "caso": case, "operação": operation, "esperado": expected,
                      "observado": observed, "resultado": state}, ensure_ascii=False), flush=True)
    return state == "passou"


def case_list(client):
    cases = {}
    params = {"limit": 100}
    cursors = set()
    while True:
        page = client.get(API + "/cases", params=params, max_redirects=0)
        if page.status != 200:
            raise ValueError(f"HTTP {page.status}")
        data = page.json()
        cases.update((item["id"], item["brand_id"]) for item in data["items"])
        cursor = data["next_cursor"]
        if cursor is None:
            return cases
        if not cursor or cursor in cursors:
            raise ValueError("paginação incompleta")
        cursors.add(cursor)
        params["cursor"] = cursor


def inspect_actor(context, actor, password, cases):
    page = context.new_page()
    page.goto(ORIGIN + "/analista", wait_until="domcontentloaded")
    # Confere a origem antes de fornecer o acesso sintético.
    if page.url != ORIGIN + "/analista":
        raise ValueError("origem inesperada")
    client = context.request
    bootstrap = client.get(API + "/session", max_redirects=0)
    token = bootstrap.json()["csrf_token"]
    login = client.post(API + "/session", max_redirects=0,
                        data={"email": actor.lower() + "@example.test", "password": password},
                        headers={"Origin": ORIGIN, "X-CSRF-Token": token})
    if login.status != 200:
        raise ValueError(f"login HTTP {login.status}")
    session = client.get(API + "/session", max_redirects=0).json()
    user = session["user"]
    if user["name"] != actor or user["role"] != "analyst":
        raise ValueError("identidade inesperada")
    expected_brands = {AURORA} if actor == "Bia" else {AURORA, HORIZONTE}
    catalog = client.get(API + "/case-filters", max_redirects=0).json()
    brands = set(user["brand_ids"])
    queue_brands = {q["brand_id"] for q in catalog["queues"]}
    matches = brands == queue_brands == {b["id"] for b in catalog["brands"]} == expected_brands
    ok = record(actor, None, "sessão e filas", sorted(expected_brands),
                {"brand_ids": sorted(brands), "marcas_das_filas": sorted(queue_brands),
                 "ativa": (session["operation"] or {}).get("active_brand_id")}, "passou" if matches else "divergiu")
    if not matches:
        return False

    visible = case_list(client)
    ok &= record(actor, None, "listagem unificada completa", "somente marcas autorizadas",
                 {"há_marca_fora_do_escopo": bool(set(visible.values()) - brands)},
                 "passou" if set(visible.values()) <= brands else "falhou")
    for case_id, brand, marker in cases:
        allowed = brand in brands
        present = case_id in visible
        correct = (visible.get(case_id) == brand) if allowed else not present
        ok &= record(actor, case_id, "listagem", allowed, present, "passou" if correct else "falhou")
        for suffix in ("", "/messages"):
            response = client.get(API + "/cases/" + case_id + suffix, max_redirects=0)
            data = response.json()
            if not allowed:
                valid = response.status == 404 and data == DENIED
                observed = {"HTTP": response.status, "somente_erro_genérico": data == DENIED}
                expected = "404 not_found genérico"
            elif suffix:
                items = data.get("items", [])
                has_marker = any(marker in item.get("text", "") for item in items)
                valid = response.status == 200 and has_marker
                observed = {"HTTP": response.status, "marcador_do_manifesto": has_marker}
                expected = "200 com mensagem do caso"
            else:
                same = data.get("id") == case_id and data.get("brand_id") == brand
                valid = response.status == 200 and same
                observed = {"HTTP": response.status, "id_e_marca_conferem": same}
                expected = "200 com ID e marca do manifesto"
            state = "passou" if valid else "falhou"
            if response.status >= 500 or response.status in (401, 429):
                state = "inconclusivo"
            ok &= record(actor, case_id, "histórico" if suffix else "detalhe direto",
                         expected, observed, state)
        page.goto(ORIGIN + "/analista?case=" + case_id, wait_until="domcontentloaded")
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
        ok &= record(actor, case_id, "link direto no painel", expected_text, ui_result, ui_state)
        if page.url != ORIGIN + "/analista?case=" + case_id:
            raise ValueError("link do caso redirecionado")
        frame = page.evaluate(SUBSCRIBE, case_id)
        expected = "confirm_subscription" if allowed else "reject_subscription"
        state = "passou" if frame == expected else "falhou"
        if frame not in ("reject_subscription", "confirm_subscription"):
            state = "inconclusivo"
        ok &= record(actor, case_id, "Action Cable", expected, frame, state)
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit", help="commit do manifesto F10-A")
    args = parser.parse_args()
    revision = git("rev-parse", "--verify", "--end-of-options", args.commit + "^{commit}")
    manifest = json.loads(git("show", revision + ":" + MANIFEST))
    if manifest["url"].rstrip("/") != ORIGIN:
        parser.error("O manifesto aponta para outra publicação.")
    cases = []
    for key, brand in (("aurora_chat", AURORA), ("horizonte_control", HORIZONTE)):
        item = manifest[key]
        if not item["marker"]:
            parser.error("Marcador ausente no manifesto.")
        cases.append((str(UUID(item["case_id"])), brand, item["marker"]))
    if cases[0][0] == cases[1][0]:
        parser.error("Os dois casos precisam ter IDs distintos.")
    print(json.dumps({"manifesto": revision, "url": ORIGIN, "origem": "computador de execução",
                      "método": "Chromium, HTTPS e WSS, contextos independentes"}), flush=True)
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
                ok &= inspect_actor(context, actor, passwords[actor.lower() + "@example.test"], cases)
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
    except (BrowserError, OSError, ValueError) as error:
        sys.exit("Execução bloqueada antes de concluir a matriz: " + type(error).__name__)
