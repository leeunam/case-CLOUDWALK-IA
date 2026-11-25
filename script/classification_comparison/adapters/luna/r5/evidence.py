"""Contrato privado e política determinística de evidência da Luna R5."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata

from adapters.qwen.adapter import choice, parse_object
from common import c01

POLICY_VERSION = "2.0.0"
POLICY_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
QUOTE_LIMIT = 160

# Só estas definições têm política revisada. A versão do catálogo, sozinha, não
# indica se o significado de um código mudou. Valores recebidos não passam aqui.
CATALOG_POLICY = {
    "category": {
        "pix": ("pix_operation", "Transferência ou pagamento por Pix, prazo, estorno ou falha."),
        "payouts": ("sales_settlement", "Repasse, recebimento ou liquidação de valores de vendas."),
        "terminal": ("terminal_operation", "Instalação, uso ou defeito da maquininha de cartão."),
    },
    "priority": {
        "basic": ("routine", "Orientação de rotina, sem operação prejudicada."),
        "intermediate": ("localized_impact", "Impacto moderado com operação ainda disponível."),
        "advanced": ("broad_impact", "Impacto relevante sem necessidade de ação imediata."),
        "urgent": ("immediate_harm", "Necessidade de ação imediata, como operação totalmente interrompida."),
    },
}
CRITERIA = {field: tuple(criterion for criterion, _ in codes.values()) + ("none",)
            for field, codes in CATALOG_POLICY.items()}


def input_sha256(item):
    data = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return sha256(data.encode("utf-8")).hexdigest()


def normalized(text):
    return "".join(char for char in unicodedata.normalize("NFKD", text.casefold())
                   if not unicodedata.combining(char))


def relations(left, right, *, gap=5, reverse=True):
    """Constrói relações locais com distância em palavras e escopo de oração."""
    middle = rf"(?:[\s'\"“”/-]+(?!(?:e|ou|enquanto|embora)\b)[a-z0-9]+){{0,{gap}}}[\s'\"“”/-]+"
    forward = rf"\b(?:{left})\b{middle}\b(?:{right})\b"
    return rf"(?:{forward}|\b(?:{right})\b{middle}\b(?:{left})\b)" if reverse else forward


PIX_ACTION = (
    r"(?:faz(?:er|ia)|fiz|faco|envi(?:ar|ei|o)|mand(?:ar|ei|o)|transfer(?:ir|i)|pag(?:ar|uei|o)|"
    r"receb(?:er|i|o)|consult(?:ar|ei)|confirm(?:ar|ei)|estorn(?:ar|ei|o)|cancel(?:ar|ei)|"
    r"rastrear|comprovante|prazo|transferencia|pagamento|cobranca)"
)
OPERATION_FAILURE = (
    r"(?:nao (?:entrou|caiu|chegou|passou|funciona|funcionou|completou|concluiu|processa)|"
    r"foi (?:rejeitad[oa]|devolvid[oa]|cancelad[oa])|falh(?:ou|a)|ficou (?:pendente|travado)|"
    r"esta (?:pendente|em analise|em atraso)|sumiu|deu erro)"
)
PIX_KEY = r"chave (?:pix|do (?:destinatario|favorecido|recebedor)|de quem (?:vai )?receber)"
KEY_TRANSFER = (
    r"(?:envi(?:ar|ei|o)|mand(?:ar|ei|o)|transfer(?:ir|i)|pag(?:ar|uei|o))"
    r"(?:\s+(?:um|o|esse|este|algum))?\s+(?:valor|dinheiro|quantia|pagamento)"
)
SALES_SOURCE = (
    r"(?:(?:repasses?|valor(?:es)?|dinheiro|recebiveis?|recebimento|liquidacao)"
    r"\s+(?:das?|de|pelas?)\s+(?:(?:minhas?|nossas?|suas?)\s+)?vendas|"
    r"vendas?\s+(?:a|no?|com)\s+(?:(?:cartao|parcelas?)\s+)?(?:credito|debito|cartao)|"
    r"(?:vendi|vendemos|vendido|vendida)\s+(?:a|no?|com)\s+(?:credito|debito|cartao)|"
    r"faturamento\s+(?:das?|de)\s+vendas)"
)
SETTLEMENT_ACTION = (
    r"(?:receb(?:er|i|emos|imento)|liquid(?:ar|acao|ad[oa])|credit(?:ar|ad[oa]|ou)|"
    r"(?:cair|cai|caiu|entrar|entra|entrou|depositar|depositado)\s+(?:na|em minha|em nossa)\s+conta|"
    r"(?:caiu|entrou)\s+no\s+saldo|prazo|data|quando|atras(?:[oa]|ou|ado)|"
    rf"{OPERATION_FAILURE}|ainda nao (?:recebi|recebemos)|qual (?:o|e o) valor|"
    r"onde (?:cai|entra|recebo)|consult(?:ar|ei)|acompanhar)"
)
TERMINAL = (
    r"(?:maquininhas?|(?:leitor[ae]s?|terminal|terminais|maquina|equipamento)\s+"
    r"(?:de (?:cart(?:ao|oes)|pagamentos?|vendas)|do cartao))"
)
TERMINAL_ACTION = (
    r"(?:instal(?:ar|acao|ei)|ativ(?:ar|acao|ei)|configur(?:ar|acao|ei)|"
    r"pare(?:ar|amento|ei)|conect(?:ar|ei)|vincul(?:ar|ei)|reinici(?:ar|ei)|"
    r"us(?:ar|o|ei)|(?:troc(?:ar|a|o)|coloc(?:ar|o))\s+(?:a\s+)?bobina|"
    r"(?:imprim(?:ir|e|iu)|emit(?:ir|e|iu))\s+(?:os?\s+)?comprovantes?|"
    r"(?:nao\s+(?:liga|ligou|conecta|le|imprime|reconhece|aceita)|"
    r"deixou de\s+(?:ligar|conectar|ler|imprimir|emitir)|"
    r"parou de\s+(?:ligar|conectar|ler|imprimir|emitir)|"
    rf"travou|quebrou|{OPERATION_FAILURE}))"
)
CATEGORY_SUBJECTS = {"pix_operation": rf"pix|{PIX_KEY}", "sales_settlement": SALES_SOURCE,
                     "terminal_operation": TERMINAL}
CATEGORY_RELATIONS = {
    "pix_operation": re.compile(
        rf"{relations(PIX_ACTION + '|' + OPERATION_FAILURE, 'pix', gap=4)}|"
        rf"{relations(KEY_TRANSFER, PIX_KEY, gap=4, reverse=False)}"
    ),
    "sales_settlement": re.compile(relations(SALES_SOURCE, SETTLEMENT_ACTION, gap=8)),
    "terminal_operation": re.compile(relations(TERMINAL, TERMINAL_ACTION, gap=6)),
}

SENTENCE = re.compile(r"[^.!?;\n]+[.!?;]*")
TRANSITION = re.compile(r"\b(?:mas|porém|porem|contudo|no entanto|só que|so que)\b", re.I)
HYPOTHETICAL = re.compile(
    r"^\s*[,:\s]*(?:se\b|caso\b|supondo\b|na hipotese\b)|"
    r"\b(?:talvez|possivelmente|hipoteticamente|pode ser que|pode ser|"
    r"acho que|suspeito que|suspeito de|imagino que|acredito que)\b"
)
EXCLUDED_FOCUS = re.compile(
    r"\bnao (?:e|era) (?:sobre|referente a|a respeito de)\b|"
    r"\b(?:nao (?:pergunto|preciso|quero|estou perguntando|estou falando) (?:sobre|saber|de)|"
    r"sem (?:relacao com|duvidas? (?:sobre|de)))\b"
)
INCIDENTAL = re.compile(
    r"\b(?:a proposito|por sinal|so mencionei|so citei|somente mencionei|"
    r"como exemplo|por exemplo|de passagem|apenas (?:um exemplo|para ilustrar))\b"
)
NORMAL_OR_RECOVERED = re.compile(
    r"\b(?:(?:caiu|entrou|funcionou|funciona|passou|esta funcionando|opera|ocorreu|"
    r"foi (?:enviad[oa]|pag[oa]|confirmad[oa])) (?:normalmente|sem (?:falhas?|problemas?))|"
    r"(?:ja )?(?:voltou|voltaram|retornou|normalizou)\b|"
    r"(?:ja )?(?:esta|estao) (?:normal|normais|resolvid[oa]s?)\b|"
    r"(?:falha|problema|situacao) (?:ja )?(?:passou|cessou|acabou))\b"
)
FOCUS = re.compile(
    r"\b(?:(?:o problema|a questao|(?:a|a minha|minha) (?:duvida|solicitacao)|(?:o|o meu|meu) pedido) (?:e|era)\b|"
    r"o que (?:preciso|quero) (?:e|saber)\b|(?:preciso|quero|gostaria de) (?:saber|entender|"
    r"resolver|aprender|configurar|consultar|rastrear)\b)"
)
INQUIRY = re.compile(
    r"\b(?:como|quando|onde|qual|quanto tempo|quero|queria|gostaria|preciso|podem me "
    r"(?:orientar|explicar|ajudar)|podem dizer|estou (?:preparando|aprendendo))\b|\?"
)
FUTURE = re.compile(
    r"\b(?:amanha|no futuro|na proxima|no proximo|semana que vem|mes que vem|"
    r"(?:vou|vamos|irei|iremos) (?:usar|configurar|instalar|receber|vender|fazer|enviar)|"
    r"quando (?:eu )?(?:usar|configurar|instalar|receber|vender|fizer|enviar))\b"
)
CONTRAST_WORDS = re.compile(r"^(?:mas|porem|contudo|no entanto|so que)\b[\s,]*")


@dataclass(frozen=True)
class Clause:
    text: str
    excerpt: str
    contrast: bool


def clauses(text, start, end):
    """Mantém ordem e extrai a parte realmente citada de cada oração."""
    for sentence in SENTENCE.finditer(text):
        left, right = sentence.span()
        cuts = [left, *(m.start() for m in TRANSITION.finditer(text, left, right) if m.start() > left), right]
        for begin, stop in zip(cuts, cuts[1:]):
            body = normalized(text[begin:stop]).strip(" ,:")
            excerpt = normalized(text[max(begin, start):min(stop, end)])
            yield Clause(CONTRAST_WORDS.sub("", body), excerpt, bool(CONTRAST_WORDS.match(body)))


def excluded(clause):
    return any(pattern.search(clause.text) for pattern in (HYPOTHETICAL, EXCLUDED_FOCUS, INCIDENTAL))


def category_reason(criterion, context):
    selected = CATEGORY_RELATIONS[criterion]
    if not any(selected.search(clause.excerpt) for clause in context):
        return "insufficient_relation"

    active = set()
    evidence_seen = False
    for clause in context:
        if EXCLUDED_FOCUS.search(clause.text):
            denied = {name for name, subject in CATEGORY_SUBJECTS.items() if re.search(rf"\b(?:{subject})\b", clause.text)}
            active.difference_update(denied)
            if criterion in denied:
                evidence_seen = False
            continue
        if excluded(clause):
            continue
        asks = bool(INQUIRY.search(clause.text))
        if ((NORMAL_OR_RECOVERED.search(clause.text) or FUTURE.search(clause.text)) and not asks):
            continue
        matched = {name for name, pattern in CATEGORY_RELATIONS.items() if pattern.search(clause.text)}
        if FOCUS.search(clause.text) or clause.contrast and (asks or matched):
            active.clear()
            evidence_seen = False
        active.update(matched)
        evidence_seen |= criterion in matched and bool(selected.search(clause.excerpt))

    if not evidence_seen or active != {criterion}:
        return "context_conflict"
    return "supported_relation"


ROUTINE = re.compile(
    r"\b(?:como (?:posso |podemos |devo )?(?:usar|fazer|enviar|mandar|transferir|pagar|receber|consultar|confirmar|"
    r"configurar|instalar|ativar|conectar|trocar|imprimir|emitir|acompanhar|identificar|"
    r"liquidar|visualizar|acessar|consulto|configuro|instalo|faco|envio|troco|acompanho)|"
    r"(?:quero|queria|gostaria de|preciso) (?:aprender|entender|me preparar|uma orientacao|"
    r"saber (?:como|onde|quando|qual))|quanto tempo (?:leva|demora)|"
    r"qual (?:e |seria )?o prazo|quando (?:cai|entra|recebo|vou receber)|"
    r"(?:preparacao|treinamento|manutencao) (?:preventiv[oa]|programad[oa]|da equipe)|"
    r"(?:ainda )?nao comecei a (?:usar|vender|receber)|"
    r"(?:tudo|o atendimento|a operacao|as vendas) (?:segue[m]?|continua[m]?|funciona[m]?) "
    r"(?:normalmente|sem (?:falhas?|problemas?|impacto)))\b"
)
LOCALIZED = re.compile(
    r"\b(?:(?:so|apenas|somente) (?:uma|um|algumas|parte d[ao]s?) "
    r"(?:vendas?|lojas?|filiais?|unidades?|caixas?|turnos?|terminais?|maquininhas?|"
    r"leitor[ae]s?|pagamentos?|transferencias?|clientes?)\b[^,!?;.]{0,68}"
    r"(?:falh(?:a|aram|ou)|par(?:ou|aram)|atras(?:ou|aram)|(?:esta|ficou) bloquead[oa]|"
    r"nao (?:funciona|funcionou|passou|passaram|conclui|consegue|conseguem)|"
    r"(?:deu|da|dao) erro)|"
    r"(?:falha|erro|atraso|problema|lentidao) (?:apenas |so |restrit[oa] |isolad[oa] )?"
    r"(?:em|numa?|no) (?:uma |um )?(?:loja|caixa|unidade|filial|turno|terminal|"
    r"maquininha|leitor[ae]|venda|pagamento|transferencia|cliente)|"
    r"(?:uma|um) (?:loja|caixa|unidade|filial|turno|terminal|maquininha|leitor[ae]|venda|"
    r"pagamento|transferencia) (?:falhou|parou|atrasou|nao (?:funciona|passou|concluiu)|deu erro))\b"
)
ALTERNATIVE = re.compile(
    r"\b(?:(?<!nao )(?:ainda )?(?<!nao )(?<!nao ainda )(?:consigo|conseguimos|podemos) (?:continuar|atender|vender|"
    r"receber|cobrar|pagar|operar|processar)(?:\s+\w+){0,8}|"
    r"(?:o(?:s)? (?:outros?|demais)|a(?:s)? (?:outras?|demais)) "
    r"(?:caixas?|postos?|lojas?|unidades?|filiais?|terminais?|maquininhas?|leitor[ae]s?|"
    r"vendas?|pagamentos?|cobrancas?|transferencias?) "
    r"(?:ainda )?(?:funciona[m]?|opera[m]?|passa[m]?|segue[m]?|continua[m]?)|"
    r"(?<!nao )(?:temos|tenho|ha|existe) (?:uma |um )?(?:outra (?:forma|opcao|alternativa)|"
    r"alternativa|outro (?:caixa|terminal|leitor)|maquininha reserva)|"
    r"(?:operacao|atendimento|vendas?) (?:segue[m]?|continua[m]?|permanece[m]?) "
    r"(?:disponivel|disponiveis|funcionando|pelos?|com))\b"
)
BROAD = re.compile(
    r"\b(?:(?:varias|varios|diversas|diversos|muitas|muitos|todas as|todos os|"
    r"quase todas as|quase todos os|(?:[2-9]\d*|duas|dois|tres|quatro|cinco|seis)) "
    r"(?:lojas|unidades|filiais|caixas|equipes|clientes|turnos|vendas|transacoes|pagamentos|"
    r"transferencias|terminais|maquininhas|leitoras)"
    r"[^,!?;.]{0,65}(?:pararam|nao (?:conseguem|funcionam|passam|passaram|receberam)|"
    r"(?:foram|estao|seguem) (?:afetad[oa]s|bloquead[oa]s|pendentes)|"
    r"ficaram (?:sem|parad[oa]s)|falh(?:aram|am)|sofreram|deu erro)|"
    r"(?:impact[oa]|afetou|atingiu|comprometeu) (?:toda a|boa parte da|varias|varios) "
    r"(?:rede|equipe|operacao|unidades|lojas|filiais|clientes|vendas)|"
    r"(?:precisamos|tenho que|teremos de|temos de|vai exigir) (?:refazer|reprocessar|"
    r"reconciliar|conferir) (?:todas as|todos os|cada|muitas|varias|varios|todo o) "
    r"(?:contas|vendas|lancamentos|registros|transacoes|pagamentos|fechamento|lote)|"
    r"(?:horas|dias) (?:de|para) (?:retrabalho|refazer|reprocessar))\b"
)
TOTAL_STOP = re.compile(
    r"\b(?:(?:a operacao|o atendimento|as vendas|os pagamentos|as cobrancas) "
    r"(?:parou|pararam|esta|estao|ficou|ficaram) "
    r"(?:inteiramente|totalmente|completamente|interrompid[oa]s?|parad[oa]s?)|"
    r"(?:nenhuma|nenhum) (?:venda|cobranca|transferencia|pagamento|caixa|terminal|"
    r"leitor[ae]|maquininha) (?:passa|funciona|liga|conclui|esta disponivel)|"
    r"nao (?:consigo|conseguimos|da para) (?:atender|vender|cobrar|pagar|receber|"
    r"processar) (?:nad[ae]|de jeito nenhum|de forma alguma|nenhum[am]?)|"
    r"(?:so |apenas )?(?:o unico|a unica) (?:caixa|terminal|maquininha|leitor[ae]|"
    r"forma de (?:vender|receber|cobrar)) (?:parou|nao (?:liga|funciona)))\b"
)
NO_ALTERNATIVE = re.compile(
    r"\b(?:sem (?:nenhuma )?(?:alternativa|opcao|outro meio|outra forma|equipamento reserva)|"
    r"nao (?:ha|temos|tenho|existe) (?:mais |nenhuma |uma )?(?:alternativa|outra (?:opcao|"
    r"forma|maneira)|outro (?:meio|caixa|terminal)|maquininha reserva)|"
    r"(?:nenhuma outra forma|nenhum outro meio) (?:funciona|esta disponivel))\b"
)
IMMEDIATE_LOSS = re.compile(
    r"\b(?:(?:estou|estamos|seguimos|continuo|continuamos) perdendo "
    r"(?:vendas|clientes|pagamentos|dinheiro|receita)(?: agora| neste momento| a cada [a-z]+)?|"
    r"(?:perdemos|perco) (?:vendas|clientes|pagamentos|dinheiro|receita) "
    r"(?:a cada [a-z]+|neste momento|agora)|"
    r"(?:pagamentos|cobrancas|debitos) (?:indevidos|duplicados|nao autorizados) "
    r"(?:continuam|seguem|estao acontecendo|ainda ocorrem))\b"
)
CONSEQUENCE = (
    r"(?:vou perder|vamos perder|perderei|perderemos|cancela(?:m|ra|rao)?|"
    r"(?:ser(?:a|ao)|fica(?:ra|rao)?) (?:bloquead[oa]s?|cancelad[oa]s?)|"
    r"(?:nao (?:consigo|conseguiremos|poderei|poderemos)) "
    r"(?:abrir|pagar|fechar|entregar|atender)|"
    r"(?:vence|expira|fecha|termina) o prazo (?:de|para) "
    r"(?:pagamento|folha|liquidacao|entrega|fechamento)|"
    r"multa(?: de [a-z]+)?|interrupcao (?:da|do) (?:operacao|atendimento))"
)
IMMEDIATE_DEADLINE = (
    r"(?:agora|imediatamente|nos proximos minutos|"
    r"em (?:[1-9]|[1-5]\d|60|dez|quinze|trinta) minutos|ate hoje|ainda hoje|hoje)"
)
IMMEDIATE_CONSEQUENCE = re.compile(relations(CONSEQUENCE, IMMEDIATE_DEADLINE, gap=7))
NOW = re.compile(r"\b(?:agora|imediatamente|neste momento|nos proximos minutos)\b")
CURRENT_PROBLEM = re.compile(
    rf"\b(?:{OPERATION_FAILURE}|(?:nao|mal) (?:consigo|conseguimos)|travou|quebrou|"
    r"lentidao|bloquead[oa]s?|parad[oa]s?|perdendo|deixou de|parou de|"
    r"(?:nao (?:liga|conecta|le|imprime|reconhece|aceita))|vou perder)\b"
)
PAST_OR_RESTORED = re.compile(
    r"\b(?:ja (?:voltou|retomamos|retomei|resolveram|resolvemos|resolveu|normalizou)|"
    r"(?:tudo|a operacao|o atendimento|as vendas|os pagamentos) "
    r"(?:voltou|voltaram|retomou|retomaram|normalizou|normalizaram)|"
    r"(?:o problema|a falha|o erro) ja (?:passou|acabou|cessou|foi resolvid[oa])|"
    r"(?:ontem|antes|na semana passada) (?:tivemos|tive|fiquei|ficamos|houve|ocorreu))\b"
)
NEGATED_IMPACT = re.compile(
    r"\b(?:sem (?:urgencia|pressa|prejuizo|impacto|risco|perdas?)|"
    r"nao (?:estou|estamos|seguimos) perdendo|nao (?:vou|vamos) perder|"
    r"nao ha (?:impacto|risco|pressa|urgencia|prejuizo)|pode esperar)\b"
)
URGENT_PATTERNS = (IMMEDIATE_LOSS, IMMEDIATE_CONSEQUENCE, TOTAL_STOP)
PRIORITY_EVIDENCE = {
    "routine": (ROUTINE, NORMAL_OR_RECOVERED),
    "localized_impact": (LOCALIZED,),
    "broad_impact": (BROAD,),
    "immediate_harm": URGENT_PATTERNS,
}


def any_match(patterns, text):
    return any(pattern.search(text) for pattern in patterns)


def priority_reason(criterion, context):
    proof = PRIORITY_EVIDENCE[criterion]
    if not any(any_match(proof, clause.excerpt) for clause in context):
        return "insufficient_relation"

    active = [clause for clause in context if not excluded(clause)]
    recovery = max((i for i, clause in enumerate(active) if PAST_OR_RESTORED.search(clause.text)), default=-1)
    current = [clause for clause in active[recovery + 1:] if not FUTURE.search(clause.text)]
    # Orientação futura é suporte de rotina. Fatos futuros por si sós não são
    # prova de prejuízo atual. Um prazo futuro explícito pode ser imediato.
    immediate = [clause for clause in active[recovery + 1:] if IMMEDIATE_CONSEQUENCE.search(clause.text)]
    no_impact = any(NEGATED_IMPACT.search(clause.text) for clause in current)
    alternative = any(ALTERNATIVE.search(clause.text) and not NO_ALTERNATIVE.search(clause.text)
                      for clause in current)
    no_alternative = any(NO_ALTERNATIVE.search(clause.text) for clause in current)
    total = [clause for clause in current if TOTAL_STOP.search(clause.text)]
    total_without_alternative = total if no_alternative and not alternative else []
    loss = [clause for clause in current if IMMEDIATE_LOSS.search(clause.text)
            and not NEGATED_IMPACT.search(clause.text)]
    immediate = [clause for clause in immediate if not NEGATED_IMPACT.search(clause.text)]
    urgent = [] if no_impact else loss + immediate + total_without_alternative
    broad = [clause for clause in current if BROAD.search(clause.text) and not NEGATED_IMPACT.search(clause.text)]
    local = [clause for clause in current if LOCALIZED.search(clause.text) and not NEGATED_IMPACT.search(clause.text)]
    if urgent:
        found, support = "immediate_harm", urgent
    elif (no_alternative and alternative and total) or (no_impact and (loss or immediate or total)):
        return "context_conflict"
    elif broad and not any(NOW.search(clause.text) for clause in broad):
        found, support = "broad_impact", broad
    elif local and alternative and not total and not broad and not no_alternative:
        found, support = "localized_impact", local
    elif not (local or total or broad or loss or immediate or any(CURRENT_PROBLEM.search(c.text) for c in current)):
        routine = [clause for clause in active[max(0, recovery):]
                   if any_match(PRIORITY_EVIDENCE["routine"], clause.text)]
        found, support = "routine", routine
    else:
        return "context_conflict"

    if found == criterion and any(any_match(proof, clause.excerpt) for clause in support):
        return "supported_relation"
    return "context_conflict"


def literal_span(text, quote):
    if not quote:
        return None, None, "no_literal_span"
    start = text.find(quote)
    if start == -1:
        return None, None, "no_literal_span"
    if text.find(quote, start + 1) != -1:
        return None, None, "ambiguous_span"
    return start, start + len(quote), None


def field_data(raw, text):
    entry = raw if isinstance(raw, dict) else {}
    values = {key: entry.get(key) if isinstance(entry.get(key), str) else None
              for key in ("code", "criterion", "quote")}
    start, end, span_error = literal_span(text, values["quote"])
    return {"value": values["code"], "criterion": values["criterion"], "quote": values["quote"],
            "start": start, "end": end}, span_error


def format_error(item, field, result):
    if field not in result:
        return "missing_output"
    entry = result[field]
    if not isinstance(entry, dict) or entry.keys() - {"code", "criterion", "quote"}:
        return "invalid_output"
    if entry.keys() != {"code", "criterion", "quote"}:
        return "missing_output"
    if not all(isinstance(value, str) for value in entry.values()):
        return "invalid_output"
    code, criterion, quote = (entry[key] for key in ("code", "criterion", "quote"))
    if code == c01.ABSTENTION:
        return None if criterion == "none" and quote == "" else "invalid_output"
    if (code not in item["catalog"][field] or criterion not in CRITERIA[field] or criterion == "none"
            or not quote.strip() or len(quote) > QUOTE_LIMIT):
        return "invalid_output"
    return None


def verdict(item, field, data, span_error):
    code, criterion = data["value"], data["criterion"]
    if code == c01.ABSTENTION:
        return "explicit", "explicit_abstention"
    policy = CATALOG_POLICY[field].get(code)
    if policy is None or policy[1] != item["catalog"][field][code]:
        return "veto", "unsupported_code"
    if criterion != policy[0]:
        return "veto", "criterion_mismatch"
    if span_error is not None:
        return "veto", span_error

    context = list(clauses(item["text"], data["start"], data["end"]))
    semantic_check = category_reason if field == "category" else priority_reason
    reason = semantic_check(criterion, context)
    return ("accepted" if reason == "supported_relation" else "veto"), reason


def build_audit(item, raw_content, finish_reason, *, refusal=None, error=None):
    """Reconstrói evidências sem fornecedor, relógio ou orçamento."""
    result = parse_object(raw_content)
    requested = item["missing"]
    if error is not None:
        failure = "error", error
    elif finish_reason == "length":
        failure = "invalid", "invalid_output"
    elif refusal is not None or finish_reason == "content_filter":
        failure = "veto", "provider_refusal"
    elif raw_content is None:
        failure = "invalid", "missing_output"
    elif result is None or result.keys() - set(requested):
        failure = "invalid", "invalid_output"
    else:
        failure = None

    result = {} if result is None else result
    errors = {field: format_error(item, field, result) for field in requested} if failure is None else {}
    malformed = any(errors.values())
    fields = {}
    for field in requested:
        data, span_error = field_data(result.get(field), item["text"])
        if failure is not None:
            outcome, reason = failure
        elif malformed:
            outcome, reason = "invalid", errors[field] or "invalid_output"
        else:
            outcome, reason = verdict(item, field, data, span_error)
        fields[field] = dict(data, verdict=outcome, reason=reason)
    return {"input_sha256": input_sha256(item), "policy_sha256": POLICY_SHA256,
            "raw_content": raw_content, "finish_reason": finish_reason, "refusal": refusal, "fields": fields}


def project_choices(audit):
    choices = {}
    for field, evidence in audit["fields"].items():
        value = evidence["value"]
        outcome = evidence["verdict"]
        if outcome == "accepted":
            choices[field] = choice("predicted", value)
        elif outcome == "explicit":
            choices[field] = choice("abstained", value, "explicit")
        elif outcome == "veto":
            choices[field] = choice("abstained", value, "policy")
        else:
            # O corpo bruto fica na auditoria. Um código válido não pode
            # ocupar raw quando o objeto privado que o carrega está inválido.
            choices[field] = choice(outcome, None, evidence["reason"])
    return choices
