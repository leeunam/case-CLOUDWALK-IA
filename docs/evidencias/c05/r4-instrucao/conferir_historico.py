"""Reproduz a auditoria histórica de D3 a partir da raiz do checkout."""
from collections import Counter
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path.cwd() / "script"))
import check_classification_contracts as contracts

BASE = "f9445ed4a05036c81d624123c0fe696e12822511"
ENTREGA = "5aa4955d62f2fdf1f51fe9d22b02f778e29f33e6"
PROTO = "script/classification_comparison/example/report.json"
PLANO = "docs/planejamento/classificacao-comparativa"


def git(*args):
    return subprocess.check_output(["rtk", "proxy", "git", *args])


def conferir_bytes(nome):
    if Path(nome).read_bytes() != git("show", f"{BASE}:{nome}"):
        raise ValueError(f"Arquivo diferente da base: {nome}")


def conferir_relatorios():
    nomes = git("ls-tree", "-r", "--name-only", BASE, "--", "script/classification_comparison",
                f"{PLANO}/contratos", "docs/evidencias/c05").decode().splitlines()
    encontrados = Counter()
    for nome in nomes:
        arquivo = Path(nome)
        if arquivo.name not in {"report.json", "prefix-report.json"}:
            continue
        conferir_bytes(nome)
        if nome == PROTO:
            if contracts.read(arquivo)["contract_version"] != "1.0.0":
                raise ValueError("Versão inesperada do protótipo")
            continue
        perfil = contracts.verify_report(arquivo)
        encontrados[perfil.name] += 1
    esperados = {contracts.LEGACY: 18, contracts.OBSERVED: 3, contracts.R2: 2, contracts.LUNA: 2}
    if encontrados != esperados or PROTO not in nomes:
        raise ValueError(f"Inventário histórico divergente: {dict(encontrados)}")
    print(f"{sum(encontrados.values())} relatórios verificados, mais o protótipo 1.0 idêntico à base.")


def conferir_entrega():
    protegidos = ("script/classification_comparison/c05/budget.py", "script/classification_comparison/adapters",
                  "docs/evidencias", f"{PLANO}/r2", f"{PLANO}/luna", f"{PLANO}/r4/diagnostico",
                  f"{PLANO}/contratos/relatorio-1.4")
    if git("diff", "--name-only", BASE, ENTREGA, "--", *protegidos):
        raise ValueError("A entrega D3 modificou arquivos do conjunto histórico protegido.")
    for pasta, chave in (("luna-planejamento", "runtime_and_semantic_sources_sha256"),
                         ("r4-instrucao", "sources_sha256")):
        manifesto = Path("docs/evidencias/c05") / pasta / "candidate-freeze.json"
        conferir_bytes(manifesto)
        fontes = contracts.read(manifesto)[chave]
        for nome, esperado in fontes.items():
            conferir_bytes(nome)
            if contracts.digest(Path(nome)) != esperado:
                raise ValueError(f"SHA-256 divergente: {nome}")
        print(f"{pasta}: {len(fontes)} fontes conferidas contra a base e o congelamento.")


if __name__ == "__main__":
    conferir_relatorios()
    conferir_entrega()
