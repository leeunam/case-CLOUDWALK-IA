"""API de supervisão serial SF2-FINAL-R1, carregada após atestar as dependências."""
__all__ = ["supervise"]


def __getattr__(name):
    if name == "supervise":
        from .runner import supervise
        return supervise
    raise AttributeError(name)
