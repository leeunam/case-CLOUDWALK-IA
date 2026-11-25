"""Respostas privadas sintéticas. O final simula abstenção sem consultar rótulos."""
from adapters.qwen.fixture import completion
from common import c01, decode, encode

# Propostas sobre os seis relatos públicos de desenvolvimento, na ordem do protocolo.
# A saída passa integralmente pela política congelada, inclusive quando ela veta.
DEVELOPMENT = (
    {"category": ("payouts", "sales_settlement")},
    {},
    {"priority": ("urgent", "immediate_harm")},
    {},
    {"category": ("terminal", "terminal_operation"), "priority": ("basic", "routine")},
    {},
)


def fixture_for(plan):
    proposals = {}
    if plan.stage == "development":
        proposals = {item["text"]: proposal for item, proposal in zip(
            plan.candidates.values(), DEVELOPMENT, strict=True)}

    def gateway(body, deadline, dispatched):
        request = decode(body)
        item = decode(request["messages"][1]["content"])
        answers = {}
        for field in item["missing"]:
            proposed = proposals.get(item["text"], {}).get(field)
            if proposed is None:
                answers[field] = dict(code=c01.ABSTENTION, criterion="none", quote="")
            else:
                code, criterion = proposed
                answers[field] = dict(code=code, criterion=criterion, quote=item["text"])
        dispatched()
        return 200, completion(request["model"], encode(answers), usage={
            "prompt_tokens": 1000, "completion_tokens": 100, "cost": "0.000547", "cost_unit": "USD"})

    return gateway
