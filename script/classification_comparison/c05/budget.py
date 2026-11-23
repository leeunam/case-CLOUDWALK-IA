"""Conta cumulativa local da C05. Cada mutação usa uma transação SQLite."""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, localcontext
import json
import os
from pathlib import Path
import sqlite3
import uuid

MAX_CAP = Decimal("10")
SCHEMA_VERSION = 3
CORRECTIONS_SCHEMA = """
CREATE TABLE receipt_corrections (
    receipt TEXT PRIMARY KEY NOT NULL,
    run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    observed TEXT NOT NULL,
    violation TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id, case_id) REFERENCES reservations(run_id, case_id)
);
"""
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
    gateway_observed TEXT,
    gateway_receipt TEXT,
    gateway_pending TEXT,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, case_id),
    CHECK (state != 'settled' OR (observed IS NOT NULL AND receipt IS NOT NULL)),
    CHECK (state != 'violation' OR detail IS NOT NULL)
);
""" + CORRECTIONS_SCHEMA


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
    if not amount.is_finite() or amount < 0 or amount.adjusted() > 12:
        raise BudgetError("valor USD inválido ou fora da precisão aceita")
    sign, digits, exponent = amount.as_tuple()
    if exponent < -30 and not amount:
        return Decimal(0)
    if exponent < -30:
        excess = -30 - exponent
        if excess < len(digits) and not any(digits[-excess:]):
            return Decimal((sign, digits[:-excess], -30))
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
    return value.strip()


def receipt_reference(value):
    normalized = reference(value)
    if normalized.startswith("gateway:"):
        return "gateway:" + reference(normalized.removeprefix("gateway:"))
    return normalized


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
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if (version not in {1, 2, SCHEMA_VERSION} or row is None
                or row["id"] != self.id or row["scope"] != self.scope):
            raise BudgetError("identidade, escopo ou versão da conta incompatível")
        if usd(row["previous_spend"]) > cap_usd(row["cap"]):
            raise BudgetError("gasto anterior incompatível com a conta")
        if version == 1:
            self._upgrade_receipts(db)
        if version in {1, 2}:
            for column in ("gateway_observed", "gateway_receipt", "gateway_pending"):
                db.execute(f"ALTER TABLE reservations ADD COLUMN {column} TEXT")
            db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        return row

    def _upgrade_receipts(self, db):
        # A primeira versão usava a margem do recibo como parte da chave.
        db.execute(CORRECTIONS_SCHEMA)
        owners = {}
        rows = db.execute("SELECT run_id, case_id, receipt, prior_receipt FROM reservations").fetchall()
        for row in rows:
            owner = (row["run_id"], row["case_id"])
            current, prior = (receipt_reference(row[key]) if row[key] is not None else None
                              for key in ("receipt", "prior_receipt"))
            for evidence in (current, prior):
                if evidence is not None and owners.setdefault(evidence, owner) != owner:
                    raise BudgetError("conta antiga com recibo atribuído a mais de um caso")
            db.execute("""UPDATE reservations SET receipt = ?, prior_receipt = ?
                          WHERE run_id = ? AND case_id = ?""", (current, prior, *owner))

    def _expenditure(self, db, account):
        costs = [usd(account["previous_spend"])]
        corrections = {(row["run_id"], row["case_id"]): usd(row["observed"])
                       for row in db.execute("SELECT run_id, case_id, observed FROM receipt_corrections ORDER BY rowid")}
        for row in db.execute("SELECT * FROM reservations"):
            reserved = usd(row["reserved"])
            adjusted = corrections.get((row["run_id"], row["case_id"]))
            observed = self._observed_total(row, adjusted)
            if row["state"] == "settled":
                if row["observed"] is None or usd(row["observed"]) > reserved:
                    raise BudgetError("reserva conciliada inconsistente")
                floor = reserved if row["gateway_pending"] is not None else Decimal(0)
                costs.append(max(floor, observed))
            else:
                costs.append(reserved if observed is None else max(reserved, observed))
        return total_usd(*costs)

    @staticmethod
    def _observed_total(row, adjusted=None):
        return max((usd(amount) for amount in (row["observed"], row["gateway_observed"], adjusted)
                    if amount is not None), default=None)

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

    def claim(self, run_id, manifest_id, manifest_sha, binding_sha, configuration, *, prepare=None):
        with self.transaction() as db:
            account = self._account(db)
            self._check_available(db, account, Decimal(0))
            if db.execute("""SELECT 1 FROM runs
                             WHERE id = ? OR manifest_id = ? OR manifest_sha256 = ? OR binding_sha256 = ?""",
                          (run_id, manifest_id, manifest_sha, binding_sha)).fetchone():
                raise BudgetError("manifesto ou vinculação já usados")
            if prepare is not None:
                prepare()
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

    def _receipt_owners(self, db, evidence):
        return {(row["run_id"], row["case_id"]) for row in db.execute(
            """SELECT run_id, case_id FROM reservations WHERE receipt = ? OR prior_receipt = ? OR gateway_receipt = ?
               UNION ALL SELECT run_id, case_id FROM receipt_corrections WHERE receipt = ?""",
            (evidence, evidence, evidence, evidence))}

    def _above_reservation(self, row, amount):
        if amount is not None and amount > usd(row["reserved"]):
            return f"custo USD {amount} acima da reserva {row['reserved']}"
        return None

    def _freeze(self, db, run_id, case_id, reason):
        db.execute("UPDATE account SET frozen_reason = COALESCE(frozen_reason, ?) WHERE singleton = 1",
                   (f"{run_id}/{case_id}: {reason}",))

    def _record(self, db, row, amount, evidence, *, state, violation=None):
        if amount is not None:
            amount = usd(amount)
        if amount is not None or evidence is not None:
            evidence = receipt_reference(evidence)
        excessive = self._above_reservation(row, amount)
        violation = ". ".join(reason for reason in (violation, excessive) if reason) or None
        owner = (row["run_id"], row["case_id"])
        if evidence is not None and self._receipt_owners(db, evidence) - {owner}:
            if not violation:
                raise BudgetError("recibo já atribuído a um caso")
            violation += ". Recibo com atribuição duplicada"
            evidence = None
        db.execute("""UPDATE reservations SET state = ?, observed = ?, receipt = ?, detail = ?
                      WHERE run_id = ? AND case_id = ?""",
                   ("violation" if violation else state, str(amount) if amount is not None else None,
                    evidence, violation, *owner))
        if violation:
            self._freeze(db, *owner, violation)
        return violation

    def stage(self, run_id, case_id, *, amount, evidence, violation=None, gateway_usage=None, pending=None):
        """Persiste a evidência recebida, antes de a C02 avaliar o resultado."""
        with self.transaction() as db:
            account = self._account(db)
            row = self._reservation(db, run_id, case_id)
            if row["state"] == "dispatched":
                self._record(db, row, amount, evidence, state="staged", violation=violation)
            elif row["state"] in {"settled", "violation"} and row["gateway_usage"] is None:
                # O recibo manual pode chegar enquanto o transporte ainda aguarda a resposta.
                amount = usd(amount) if amount is not None else None
                if amount is not None or evidence is not None:
                    evidence = receipt_reference(evidence)
                excessive = self._above_reservation(row, amount)
                violation = ". ".join(reason for reason in (violation, excessive) if reason)
                if evidence is not None and self._receipt_owners(db, evidence) - {(run_id, case_id)}:
                    if not violation:
                        raise BudgetError("recibo já atribuído a um caso")
                    violation += ". Recibo com atribuição duplicada"
                    amount, evidence = None, None
                db.execute("""UPDATE reservations SET gateway_observed = ?, gateway_receipt = ?
                              WHERE run_id = ? AND case_id = ?""",
                           (str(amount) if amount is not None else None, evidence, run_id, case_id))
            else:
                raise BudgetError("resposta sem despacho registrado ou já preservada")
            if pending is not None:
                recorded = self._known_cost(db, row)
                if recorded is not None and recorded >= pending:
                    pending = None
            db.execute("""UPDATE reservations SET gateway_usage = ?, gateway_pending = ?
                          WHERE run_id = ? AND case_id = ?""",
                       (json.dumps(gateway_usage or {}), str(pending) if pending is not None else None,
                        run_id, case_id))
            if row["state"] in {"settled", "violation"}:
                cap_violation = self._above_cap(db, account)
                violation = ". ".join(reason for reason in (violation, cap_violation) if reason)
                if violation:
                    self._freeze(db, run_id, case_id, violation)

    def complete_case(self, run_id, case_id, *, timed_out=False):
        with self.transaction() as db:
            account = self._account(db)
            row = self._reservation(db, run_id, case_id)
            if row["state"] == "violation":
                raise BudgetError(f"{case_id}: {row['detail']}")
            if account["frozen_reason"] is not None:
                raise BudgetError(f"conta congelada: {account['frozen_reason']}")
            if timed_out:
                raise BudgetError(f"{case_id}: custo USD inconciliável automaticamente após timeout")
            if row["gateway_pending"] is not None:
                raise BudgetError(f"{case_id}: custo USD inconciliável na precisão aceita")
            if row["state"] == "settled":
                return
            if row["state"] != "staged" or row["observed"] is None:
                raise BudgetError(f"{case_id}: custo USD inconciliável. Reserva mantida")
            db.execute("UPDATE reservations SET state = 'settled' WHERE run_id = ? AND case_id = ?",
                       (run_id, case_id))

    def reconcile(self, receipt):
        if (not isinstance(receipt, dict)
                or set(receipt) != {"unit", "cost_usd", "reference", "run_id", "case_id"}
                or receipt["unit"] != "USD"):
            raise BudgetError("recibo exige moeda USD e atribuição explícita a execução e caso")
        amount = usd(receipt["cost_usd"])
        evidence = receipt_reference(receipt["reference"])
        run_id, case_id = reference(receipt["run_id"]), reference(receipt["case_id"])
        with self.transaction() as db:
            account = self._account(db)
            row = self._reservation(db, run_id, case_id)
            pending = row["gateway_pending"]
            if pending is not None:
                if amount < Decimal(pending):
                    raise BudgetError("recibo inferior ao custo informado pelo gateway")
                db.execute("""UPDATE reservations SET gateway_pending = NULL
                              WHERE run_id = ? AND case_id = ?""", (run_id, case_id))
            if row["state"] in {"settled", "violation"}:
                violation = self._correct_observed_cost(db, account, row, amount, evidence)
            elif row["state"] in {"dispatched", "staged"}:
                if row["observed"] is not None and amount < usd(row["observed"]):
                    raise BudgetError("recibo inferior ao custo já observado")
                if self._receipt_owners(db, evidence) - {(run_id, case_id)}:
                    raise BudgetError("recibo já atribuído a um caso")
                if row["receipt"] is not None and row["receipt"] != evidence:
                    db.execute("""UPDATE reservations SET prior_receipt = receipt, prior_observed = observed
                                  WHERE run_id = ? AND case_id = ?""", (run_id, case_id))
                violation = self._record(db, row, amount, evidence, state="settled")
            else:
                raise BudgetError("reserva sem despacho confirmado")
        if violation:
            raise BudgetError(violation)

    def _known_cost(self, db, row):
        latest = db.execute("""SELECT observed FROM receipt_corrections WHERE run_id = ? AND case_id = ?
                               ORDER BY rowid DESC LIMIT 1""", (row["run_id"], row["case_id"])).fetchone()
        return self._observed_total(row, latest["observed"] if latest is not None else None)

    def _correct_observed_cost(self, db, account, row, amount, evidence):
        owner = (row["run_id"], row["case_id"])
        observed = self._known_cost(db, row)
        if observed is not None and amount <= observed:
            raise BudgetError("reserva já conciliada ou com custo observado igual ou superior")
        if self._receipt_owners(db, evidence):
            raise BudgetError("recibo já atribuído a um caso")
        # O recibo tardio revisa o total do mesmo caso. Ele não liquida de novo a reserva.
        db.execute("""INSERT INTO receipt_corrections (receipt, run_id, case_id, observed)
                      VALUES (?, ?, ?, ?)""", (evidence, *owner, str(amount)))
        violation = ". ".join(reason for reason in (self._above_reservation(row, amount),
                                                       self._above_cap(db, account)) if reason)
        if violation:
            db.execute("UPDATE receipt_corrections SET violation = ? WHERE receipt = ?", (violation, evidence))
            self._freeze(db, *owner, violation)
        return violation

    def _above_cap(self, db, account):
        expenditure = self._expenditure(db, account)
        cap = cap_usd(account["cap"])
        if expenditure > cap:
            return f"total USD {expenditure} acima do teto global {cap}"
        return None

    def status(self):
        with self.transaction() as db:
            account = self._account(db)
            expenditure = self._expenditure(db, account)
            return {"account_id": self.id, "scope": self.scope, "cap_usd": account["cap"],
                    "previous_spend_usd": account["previous_spend"],
                    "accounted_usd": str(expenditure),
                    "available_usd": str(total_usd(cap_usd(account["cap"]), expenditure.copy_negate())),
                    "frozen_reason": account["frozen_reason"],
                    "receipt_corrections": [dict(row) for row in db.execute(
                        "SELECT * FROM receipt_corrections ORDER BY rowid")],
                    "runs": [dict(row, configuration=json.loads(row["configuration"]))
                             for row in db.execute("SELECT * FROM runs ORDER BY rowid")],
                    "reservations": [dict(row, gateway_usage=json.loads(row["gateway_usage"] or "null"))
                                     for row in db.execute("SELECT * FROM reservations ORDER BY rowid")]}
