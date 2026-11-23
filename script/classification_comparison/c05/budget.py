"""Conta cumulativa local da C05. Cada mutação usa uma transação SQLite."""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, localcontext
import json
import os
from pathlib import Path
import sqlite3
import uuid

MAX_CAP = Decimal("10")
SCHEMA_VERSION = 1
SCHEMA = """
CREATE TABLE account (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('real', 'fixture')),
    cap TEXT NOT NULL,
    previous_spend TEXT NOT NULL,
    frozen_reason TEXT
);
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    manifest_id TEXT NOT NULL UNIQUE,
    manifest_sha256 TEXT NOT NULL UNIQUE,
    binding_sha256 TEXT NOT NULL UNIQUE,
    configuration TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('claimed', 'active', 'finished', 'interrupted')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE reservations (
    run_id TEXT NOT NULL REFERENCES runs(id),
    case_id TEXT NOT NULL,
    reserved TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('reserved', 'dispatched', 'staged', 'settled', 'violation')),
    observed TEXT,
    receipt TEXT UNIQUE,
    prior_observed TEXT,
    prior_receipt TEXT UNIQUE,
    gateway_usage TEXT,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, case_id),
    CHECK (state != 'settled' OR (observed IS NOT NULL AND receipt IS NOT NULL)),
    CHECK (state != 'violation' OR detail IS NOT NULL)
);
"""


class BudgetError(ValueError):
    pass


def usd(value):
    """Persistimos decimais exatos, com limites explícitos para a representação."""
    if not isinstance(value, (str, Decimal)):
        raise BudgetError("valor USD exige representação decimal exata")
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise BudgetError("valor USD inválido") from None
    if (not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -30
            or amount.adjusted() > 12):
        raise BudgetError("valor USD inválido ou fora da precisão aceita")
    return amount


def total_usd(*amounts):
    with localcontext() as ctx:
        ctx.prec = 64
        return sum(amounts, Decimal(0))


def cap_usd(value):
    cap = usd(value)
    if not 0 < cap <= MAX_CAP:
        raise BudgetError("teto global deve estar entre US$ 0 (exclusivo) e US$ 10")
    return cap


def reference(value):
    if not isinstance(value, str) or not value.strip():
        raise BudgetError("recibo exige referência explícita")
    return value


class Account:
    def __init__(self, path, account_id, scope):
        self.path = Path(path).resolve()
        self.id = account_id
        self.scope = scope

    @classmethod
    def initialize(cls, path, *, scope, cap, previous_spend):
        cap = cap_usd(cap)
        previous = usd(previous_spend)
        if scope not in {"real", "fixture"} or previous > cap:
            raise BudgetError("escopo ou gasto anterior incompatível com a conta")
        account = cls(path, uuid.uuid4().hex, scope)
        # mode=rw bloqueia a criação acidental em qualquer outra operação.
        fd = os.open(account.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with account.transaction() as db:
            for statement in SCHEMA.strip().removesuffix(";").split(";"):
                db.execute(statement)
            db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            db.execute("INSERT INTO account VALUES (1, ?, ?, ?, ?, NULL)",
                       (account.id, scope, str(cap), str(previous)))
        return account

    @contextmanager
    def transaction(self):
        try:
            db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True)
            try:
                db.row_factory = sqlite3.Row
                db.execute("PRAGMA foreign_keys = ON")
                db.execute("PRAGMA synchronous = FULL")
                db.execute("BEGIN IMMEDIATE")
                with db:
                    yield db
            finally:
                db.close()
        except sqlite3.Error as exc:
            raise BudgetError("conta SQLite ausente, ocupada, danificada ou incompatível") from exc

    def _account(self, db):
        row = db.execute("SELECT * FROM account WHERE singleton = 1").fetchone()
        if (db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION or row is None
                or row["id"] != self.id or row["scope"] != self.scope):
            raise BudgetError("identidade, escopo ou versão da conta incompatível")
        if usd(row["previous_spend"]) > cap_usd(row["cap"]):
            raise BudgetError("gasto anterior incompatível com a conta")
        return row

    def _expenditure(self, db, account):
        costs = [usd(account["previous_spend"])]
        for row in db.execute("SELECT state, reserved, observed FROM reservations"):
            reserved = usd(row["reserved"])
            observed = usd(row["observed"]) if row["observed"] is not None else None
            if row["state"] == "settled":
                if observed is None or observed > reserved:
                    raise BudgetError("reserva conciliada inconsistente")
                costs.append(observed)
            elif row["state"] == "violation" and observed is not None:
                costs.append(max(reserved, observed))
            else:
                costs.append(reserved)
        return total_usd(*costs)

    def validate(self, cap):
        with self.transaction() as db:
            account = self._account(db)
            if (db.execute("PRAGMA quick_check").fetchone()[0] != "ok"
                    or db.execute("PRAGMA foreign_key_check").fetchone() is not None
                    or cap_usd(account["cap"]) != cap):
                raise BudgetError("integridade ou teto global da conta incompatível")
            self._check_available(db, account, Decimal(0))

    def _check_available(self, db, account, additional):
        if account["frozen_reason"] is not None:
            raise BudgetError(f"conta congelada: {account['frozen_reason']}")
        if total_usd(self._expenditure(db, account), additional) > cap_usd(account["cap"]):
            raise BudgetError("saldo global insuficiente para a reserva")

    def claim(self, run_id, manifest_id, manifest_sha, binding_sha, configuration):
        with self.transaction() as db:
            account = self._account(db)
            self._check_available(db, account, Decimal(0))
            if db.execute("""SELECT 1 FROM runs
                             WHERE id = ? OR manifest_id = ? OR manifest_sha256 = ? OR binding_sha256 = ?""",
                          (run_id, manifest_id, manifest_sha, binding_sha)).fetchone():
                raise BudgetError("manifesto ou vinculação já usados")
            db.execute("""INSERT INTO runs (id, manifest_id, manifest_sha256, binding_sha256, configuration, state)
                          VALUES (?, ?, ?, ?, ?, 'claimed')""",
                       (run_id, manifest_id, manifest_sha, binding_sha, json.dumps(configuration)))

    def activate(self, run_id, manifest_sha):
        with self.transaction() as db:
            account = self._account(db)
            self._check_available(db, account, Decimal(0))
            if db.execute("""UPDATE runs SET state = 'active'
                             WHERE id = ? AND manifest_sha256 = ? AND state = 'claimed'""",
                          (run_id, manifest_sha)).rowcount != 1:
                raise BudgetError("execução não registrada, já iniciada ou encerrada")

    def close_run(self, run_id, *, finished):
        with self.transaction() as db:
            self._account(db)
            db.execute("UPDATE runs SET state = ? WHERE id = ? AND state IN ('claimed', 'active')",
                       ("finished" if finished else "interrupted", run_id))

    def reserve(self, run_id, case_id, amount):
        amount = usd(amount)
        with self.transaction() as db:
            account = self._account(db)
            config = db.execute("SELECT configuration FROM runs WHERE id = ? AND state = 'active'",
                                (run_id,)).fetchone()
            if config is None:
                raise BudgetError("execução sem autorização ativa")
            binding = json.loads(config["configuration"])
            if case_id not in binding["candidate_ids"]:
                raise BudgetError("caso fora da execução autorizada")
            if usd(binding["reservation_usd"]) != amount or amount <= 0:
                raise BudgetError("valor da reserva diverge da configuração autorizada")
            if db.execute("SELECT 1 FROM reservations WHERE run_id = ? AND case_id = ?",
                          (run_id, case_id)).fetchone():
                raise BudgetError("caso já reservado nesta execução")
            self._check_available(db, account, amount)
            db.execute("""INSERT INTO reservations (run_id, case_id, reserved, state)
                          VALUES (?, ?, ?, 'reserved')""", (run_id, case_id, str(amount)))

    def mark_dispatched(self, run_id, case_id):
        with self.transaction() as db:
            account = self._account(db)
            self._check_available(db, account, Decimal(0))
            if db.execute("""UPDATE reservations SET state = 'dispatched'
                             WHERE run_id = ? AND case_id = ? AND state = 'reserved'
                               AND EXISTS (SELECT 1 FROM runs WHERE id = ? AND state = 'active')""",
                          (run_id, case_id, run_id)).rowcount != 1:
                raise BudgetError("despacho sem reserva ativa ou já registrado")

    def _reservation(self, db, run_id, case_id):
        row = db.execute("SELECT * FROM reservations WHERE run_id = ? AND case_id = ?",
                         (run_id, case_id)).fetchone()
        if row is None:
            raise BudgetError("caso sem reserva vinculada")
        return row

    def _record(self, db, row, amount, evidence, *, state, violation=None):
        if amount is not None:
            amount = usd(amount)
            reference(evidence)
        if amount is not None and amount > usd(row["reserved"]):
            excessive = f"custo USD {amount} acima da reserva {row['reserved']}"
            violation = f"{violation}; {excessive}" if violation else excessive
        if evidence is not None and db.execute(
                """SELECT 1 FROM reservations WHERE (receipt = ? OR prior_receipt = ?)
                   AND (run_id != ? OR case_id != ?)""",
                (evidence, evidence, row["run_id"], row["case_id"])).fetchone():
            if not violation:
                raise BudgetError("recibo já atribuído a um caso")
            violation += "; recibo com atribuição duplicada"
            evidence = None
        db.execute("""UPDATE reservations SET state = ?, observed = ?, receipt = ?, detail = ?
                      WHERE run_id = ? AND case_id = ?""",
                   ("violation" if violation else state, str(amount) if amount is not None else None,
                    evidence, violation, row["run_id"], row["case_id"]))
        if violation:
            db.execute("UPDATE account SET frozen_reason = COALESCE(frozen_reason, ?) WHERE singleton = 1",
                       (f"{row['run_id']}/{row['case_id']}: {violation}",))
        return violation

    def stage(self, run_id, case_id, *, amount, evidence, violation=None, gateway_usage=None):
        """Guarda evidência do gateway. Só o caso verificado pode reduzir saldo reservado."""
        with self.transaction() as db:
            self._account(db)
            row = self._reservation(db, run_id, case_id)
            if row["state"] != "dispatched":
                raise BudgetError("resposta sem despacho registrado")
            self._record(db, row, amount, evidence, state="staged", violation=violation)
            if gateway_usage:
                db.execute("""UPDATE reservations SET gateway_usage = ?
                              WHERE run_id = ? AND case_id = ?""",
                           (json.dumps(gateway_usage), run_id, case_id))

    def complete_case(self, run_id, case_id):
        with self.transaction() as db:
            self._account(db)
            row = self._reservation(db, run_id, case_id)
            if row["state"] == "violation":
                raise BudgetError(f"{case_id}: {row['detail']}")
            if row["state"] == "settled":
                return
            if row["state"] != "staged" or row["observed"] is None:
                raise BudgetError(f"{case_id}: custo USD inconciliável; reserva mantida")
            db.execute("UPDATE reservations SET state = 'settled' WHERE run_id = ? AND case_id = ?",
                       (run_id, case_id))

    def reconcile(self, receipt):
        if (not isinstance(receipt, dict)
                or set(receipt) != {"unit", "cost_usd", "reference", "run_id", "case_id"}
                or receipt["unit"] != "USD"):
            raise BudgetError("recibo exige moeda USD e atribuição explícita a execução e caso")
        amount = usd(receipt["cost_usd"])
        evidence = reference(receipt["reference"])
        run_id, case_id = reference(receipt["run_id"]), reference(receipt["case_id"])
        with self.transaction() as db:
            self._account(db)
            row = self._reservation(db, run_id, case_id)
            if row["state"] not in {"dispatched", "staged"}:
                raise BudgetError("reserva sem despacho confirmado, já conciliada ou em violação")
            if row["observed"] is not None and amount < usd(row["observed"]):
                raise BudgetError("recibo inferior ao custo já observado")
            if row["receipt"] is not None and row["receipt"] != evidence:
                db.execute("""UPDATE reservations SET prior_receipt = receipt, prior_observed = observed
                              WHERE run_id = ? AND case_id = ?""", (run_id, case_id))
            violation = self._record(db, row, amount, evidence, state="settled")
        if violation:
            raise BudgetError(violation)

    def status(self):
        with self.transaction() as db:
            account = self._account(db)
            expenditure = self._expenditure(db, account)
            return {"account_id": self.id, "scope": self.scope, "cap_usd": account["cap"],
                    "previous_spend_usd": account["previous_spend"],
                    "accounted_usd": str(expenditure),
                    "available_usd": str(total_usd(cap_usd(account["cap"]), expenditure.copy_negate())),
                    "frozen_reason": account["frozen_reason"],
                    "runs": [dict(row, configuration=json.loads(row["configuration"]))
                             for row in db.execute("SELECT * FROM runs ORDER BY rowid")],
                    "reservations": [dict(row, gateway_usage=json.loads(row["gateway_usage"] or "null"))
                                     for row in db.execute("SELECT * FROM reservations ORDER BY rowid")]}
