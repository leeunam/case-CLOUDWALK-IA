"""Compromisso local das saídas originais. Permanece junto da conta R2."""
import os
import stat

from plan import canonical_digest
from budget import BudgetError
from common import decode, encode
from journal import sync_directory


def path_for(plan, account):
    return account.path.parent / f".{plan.manifest_id(account)}.development-seal.json"


def commitment(plan, account, gate, proof_sha):
    return dict(version=1, account_id=account.id, mode=account.scope, stage=plan.stage,
                run_id=gate["run_id"], manifest_id=plan.manifest_id(account),
                manifest_sha256=gate["manifest_sha256"], binding_sha256=gate["binding_sha256"],
                config_sha256=plan.settings.sha256, candidate_sha256=plan.sources["candidate"]["sha256"],
                proof_sha256=proof_sha,
                output_sha256={name: entry["sha256"] for name, entry in gate["artifacts"].items()})


def create(plan, account, gate, proof_sha):
    path = path_for(plan, account)
    content = (encode(commitment(plan, account, gate, proof_sha), indent=2) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(path.parent)


def verify(plan, account, gate, proof_sha):
    try:
        descriptor = os.open(path_for(plan, account), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            mode = os.fstat(stream.fileno()).st_mode
            if not stat.S_ISREG(mode) or mode & 0o077:
                raise BudgetError("selo de development exige arquivo privado")
            recorded = decode(stream.read())
        expected = commitment(plan, account, gate, proof_sha)
        if canonical_digest(recorded) != canonical_digest(expected):
            raise BudgetError("selo de development divergente: prova ou saídas adulteradas")
    except BudgetError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise BudgetError("selo de development ausente ou corrompido") from error
