"""Injeção para testar IPC e roteamento do C02 sem instalar o motor real."""
from adapter import run


def load_fake(policy, on_forward):
    def pipeline(text, labels, **options):
        on_forward()
        groups = labels if isinstance(labels, dict) else {"": labels}
        return [[dict(label=f"{field}.{label}" if field else label, score=0.9 if index == 0 else 0.1)
                 for field, values in groups.items() for index, label in enumerate(values)]]
    return pipeline, {"runtime": "pipeline-falso-sem-pesos"}


if __name__ == "__main__":
    run(load_fake, mode="fixture", model="gliclass-fake", revision=None)
