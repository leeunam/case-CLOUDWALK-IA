"""Instala o arquivo portátil entregue pelo custodiante em um diretório novo."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import tarfile
from tempfile import TemporaryDirectory

ARCHIVE_SHA = "a06d4eb0fdf26f06a86b6fe6fa1f8e1bdab49fbed01647a0b8431193473e4f01"
MANIFEST_SHA = "224c572b0a2c6ce93b1dd1b90317df131cbb47b897b4de38e97659fbc7e57872"


def install(archive, destination):
    if destination.exists():
        raise ValueError("escolha um diretório novo")
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != ARCHIVE_SHA:
            raise ValueError("SHA-256 do arquivo de entrega divergente")
        stream.seek(0)
        with TemporaryDirectory(dir=destination.parent) as temporary:
            stage = Path(temporary)
            with tarfile.open(fileobj=stream, mode="r|gz") as members:
                for entry in members:
                    path = PurePosixPath(entry.name)
                    if (path.parts[:1] != ("package",) or ".." in path.parts or str(path) != entry.name
                            or not (entry.isdir() or entry.isfile())):
                        raise ValueError("membro inválido no pacote")
                    target = stage / path
                    if entry.isdir():
                        target.mkdir(mode=0o755)
                    else:
                        with members.extractfile(entry) as source, target.open("xb") as output:
                            shutil.copyfileobj(source, output)
                        target.chmod(0o444)
            package = stage / "package"
            if hashlib.sha256((package / "manifest.json").read_bytes()).hexdigest() != MANIFEST_SHA:
                raise ValueError("manifesto divergente da adoção")
            # Reserva o destino antes de substituí-lo pelo diretório completo, no mesmo filesystem.
            destination.mkdir()
            package.replace(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        install(args.archive, args.destination)
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.exit(1, f"Falha ao instalar pacote: {error}\n")
    print(f"Pacote instalado em {args.destination.resolve()}")
