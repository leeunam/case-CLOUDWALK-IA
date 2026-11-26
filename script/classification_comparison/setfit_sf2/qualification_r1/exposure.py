"""Reserva pública permanente e marcadores exclusivos compatíveis com a coleta histórica."""
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path

from ..contracts.core import decode
from .bootstrap import HISTORY, MAIN, SF
from .storage import canonical, encoded, exclusive, read, require, sync_directory


@dataclass(frozen=True)
class Guard:
    shared: Path
    legacy_validation: Path
    legacy_release: Path
    authorizations: Path

    @classmethod
    def production(cls):
        base = MAIN / ".superpowers/sdd/conclusao-projeto"
        historical = HISTORY / SF / ".cache/qualificacao-01/evaluation-02"
        return cls(base / "sf2-exposures", historical / "validation/final-exposure.json",
                   historical / "release/exposure.json", base / "sf2-authorizations")

    def authorization(self, release, seal):
        path = self.authorizations / (release + ".json")
        authorization = decode(read(path))
        require(authorization == {"action": "execute_once", "release_sha256": release, "final_seal_sha256": seal},
                "autorização incompatível com o digest e selo")

    def paths(self, release_dir, seal):
        return (self.shared / (seal + ".json"), self.legacy_validation, release_dir / "exposure.json")

    def reserve(self, release_dir, release, seal, destination, custody):
        self.authorization(release, seal)
        canonical(destination)
        require(not os.path.lexists(destination), "destino da execução ocupado")
        require(Path(custody).is_absolute() and ".." not in Path(custody).parts, "nome de custódia não canônico")
        paths = self.paths(release_dir, seal)
        for path in (*paths, self.legacy_release):
            canonical(path.parent)
            require(not os.path.lexists(path), "exposição já reservada")
        canonical(self.shared)
        self.shared.mkdir(exist_ok=True)
        sync_directory(self.shared.parent)
        receipt = dict(final_seal_sha256=seal, release_sha256=release, destination=str(destination),
                       custody=str(custody), opened_at=datetime.now(timezone.utc).isoformat())
        for path in paths:
            exclusive(path, encoded(receipt))
        require(not os.path.lexists(self.legacy_release), "exposição histórica concorrente")
        return receipt

    def verify(self, release_dir, release, seal, destination, custody=None):
        self.authorization(release, seal)
        paths = self.paths(release_dir, seal)
        raw = read(paths[0])
        require(all(read(path) == raw for path in paths[1:]), "recibos da exposição divergentes")
        receipt = decode(raw)
        require(set(receipt) == {"final_seal_sha256", "release_sha256", "destination", "custody", "opened_at"}
                and receipt["release_sha256"] == release and receipt["final_seal_sha256"] == seal
                and receipt["destination"] == str(destination)
                and datetime.fromisoformat(receipt["opened_at"]).utcoffset() == timezone.utc.utcoffset(None)
                and (custody is None or receipt["custody"] == str(custody)), "recibo de outra execução")
        return receipt

