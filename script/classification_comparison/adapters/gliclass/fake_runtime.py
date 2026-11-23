"""Injeção para testar IPC e roteamento do C02 sem instalar o motor real."""
from adapter import run


def load_fake(policy):
    def pipeline(text, labels, **options):
        return [[dict(label=label, score=0.9 if index == 0 else 0.1)
                 for index, label in enumerate(labels)]]
    return pipeline, {"runtime": "pipeline-falso-sem-pesos"}


if __name__ == "__main__":
    run(load_fake, mode="fixture", model="gliclass-fake", revision=None)
