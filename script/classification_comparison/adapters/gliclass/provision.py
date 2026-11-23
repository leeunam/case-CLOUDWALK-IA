"""Baixa somente o snapshot público fixado, fora do caminho de inferência."""
import json
import os
from pathlib import Path
import shutil
import time

from model import FILES, HERE, MODEL, REVISION, SNAPSHOT, verify_snapshot


def main():
    cache = HERE / ".cache"
    os.environ.update(HF_HOME=str(cache / "hf"), HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
                      HF_HUB_DISABLE_TELEMETRY="1", HF_HUB_DISABLE_XET="1", HF_HUB_OFFLINE="0",
                      HF_ENDPOINT="https://huggingface.co")
    from huggingface_hub import HfApi, snapshot_download

    started = time.monotonic()
    info = HfApi(token=False).model_info(MODEL, revision=REVISION, files_metadata=True, token=False)
    sizes = {file.rfilename: file.size for file in info.siblings if file.rfilename in FILES}
    if (info.sha != REVISION or info.gated or info.private or set(sizes) != set(FILES) or
            any(size is None for size in sizes.values()) or sum(sizes.values()) > 700_000_000):
        raise ValueError("metadados do snapshot público divergentes ou fora do orçamento")
    if shutil.disk_usage(HERE).free < 2_000_000_000:
        raise OSError("disco insuficiente para provisionar o snapshot")
    before = {name for name in FILES if (SNAPSHOT / name).is_file()}
    download_started = time.monotonic()
    path = Path(snapshot_download(MODEL, revision=REVISION, local_dir=SNAPSHOT, token=False,
                                  allow_patterns=list(FILES), max_workers=1))
    download_ms = (time.monotonic() - download_started) * 1000
    actual = {name: (path / name).stat().st_size for name in FILES}
    if actual != sizes:
        raise ValueError("tamanhos locais divergem dos arquivos públicos fixados")
    result = dict(model=MODEL, revision=REVISION, license="Apache-2.0", files=actual,
                  snapshot_bytes=sum(actual.values()), weights_sha256=verify_snapshot(path),
                  first_population=not before, snapshot_download_or_reuse_ms=download_ms,
                  public_metadata_ms=(download_started - started) * 1000,
                  network_transfer_bytes=None, api_usd=0)
    (cache / "snapshot.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
