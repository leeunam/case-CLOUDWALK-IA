"""Reserva pública permanente e marcadores exclusivos compatíveis com a coleta histórica."""
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import re
from pathlib import Path

from .bootstrap import CUSTODY, HISTORY, MAIN, SF
from .storage import decode, canonical, encoded, exclusive, read, require, sync_directory


@dataclass(frozen=True)
class Guard:
    shared: Path
    legacy_validation: Path
    legacy_release: Path
    authorizations: Path
    custody_root: Path

    @classmethod
    def production(cls):
        base = MAIN / ".superpowers/sdd/conclusao-projeto"
        historical = HISTORY / SF / ".cache/qualificacao-01/evaluation-02"
        return cls(base / "sf2-exposures", historical / "validation/final-exposure.json",
                   historical / "release/exposure.json", base / "sf2-authorizations", CUSTODY)

    def authorization(self, release, seal):
        require(all(type(token) is str and re.fullmatch("[0-9a-f]{64}", token) for token in (release, seal)),
                "digest inválido no marcador de autorização")
        path = self.authorizations / (release + ".json")
        authorization = decode(read(path))
        require(set(authorization) == {"action", "release_sha256", "final_seal_sha256", "custody"}
                and authorization["action"] == "execute_once" and authorization["release_sha256"] == release
                and authorization["final_seal_sha256"] == seal, "autorização incompatível com o digest e selo")
        scope = authorization["custody"]
        require(type(scope) is dict and set(scope) == {"inventory", "members"} and type(scope["members"]) is dict
                and set(scope["members"]) == {"final", "annotations", "review_receipt", "token_lengths"},
                "autorização de custódia incompleta")
        names = [scope["inventory"], *scope["members"].values()]
        require(all(type(name) is str and Path(name).parent == self.custody_root and str(Path(name)) == name
                    and Path(name).name not in ("", ".", "..") for name in names) and len(set(names)) == 5,
                "caminho fora da custódia autorizada")
        return scope


    def paths(self, release_dir, seal):
        return (self.shared / (seal + ".json"), self.legacy_validation, release_dir / "exposure.json")

    def reserve(self, release_dir, release, seal, destination, custody):
        require(Path(custody).parent == self.custody_root, "inventário fora da custódia autorizada")
        scope = self.authorization(release, seal)
        require(str(custody) == scope["inventory"], "inventário diferente da autorização")
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
                       custody=str(custody), members=scope["members"], opened_at=datetime.now(timezone.utc).isoformat())
        for path in paths:
            exclusive(path, encoded(receipt))
        require(not os.path.lexists(self.legacy_release), "exposição histórica concorrente")
        return receipt

    def verify(self, release_dir, release, seal, destination, custody=None):
        scope = self.authorization(release, seal)
        paths = self.paths(release_dir, seal)
        raw = read(paths[0])
        require(all(read(path) == raw for path in paths[1:]), "recibos da exposição divergentes")
        receipt = decode(raw)
        require(set(receipt) == {"final_seal_sha256", "release_sha256", "destination", "custody", "members", "opened_at"}
                and receipt["release_sha256"] == release and receipt["final_seal_sha256"] == seal
                and receipt["destination"] == str(destination) and receipt["members"] == scope["members"]
                and receipt["custody"] == scope["inventory"]
                and datetime.fromisoformat(receipt["opened_at"]).utcoffset() == timezone.utc.utcoffset(None)
                and (custody is None or receipt["custody"] == str(custody)), "recibo de outra execução")
        return receipt

