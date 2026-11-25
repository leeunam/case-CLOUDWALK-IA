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


def relations(left, right, *, gap):
    """Liga a consequência ao prazo e marca onde começa a consequência."""
    middle = rf"(?:[\s'\"“”/-]+(?!(?:e|ou|enquanto|embora)\b)[a-z0-9]+){{0,{gap}}}[\s'\"“”/-]+"
    return (rf"(?:\b(?P<effect_first>{left})\b{middle}\b(?:{right})\b|"
            rf"\b(?:{right})\b{middle}\b(?P<effect_last>{left})\b)")


PIX_ACTION = (
    r"(?:faz(?:er|ia)|fiz|faco|envi(?:ar|ei|o)|mand(?:ar|ei|o)|transfer(?:ir|i)|pag(?:ar|uei|o)|"
    r"receb(?:er|i|o)|consult(?:ar|ei)|confirm(?:ar|ei)|estorn(?:ar|ei|o)|cancel(?:ar|ei)|"
    r"rastrear)"
)
OPERATION_FAILURE = (
    r"(?:nao (?:entrou|caiu|chegou|passou|funciona|funcionou|completou|concluiu|processa)|"
    r"foi (?:rejeitad[oa]|devolvid[oa]|cancelad[oa])|falh(?:ou|a)|ficou (?:pendente|travado)|"
    r"esta (?:pendente|em analise|em atraso)|sumiu|deu erro)"
)
PIX_KEY = r"chave (?:pix|do (?:destinatario|favorecido|recebedor)|de quem (?:vai )?receber)"
KEY_TRANSFER = (
    r"(?:envi(?:ar|ei|o)|mand(?:ar|ei|o)|transfer(?:ir|i)|pag(?:ar|uei|o))"
    r"(?: (?:um|o|esse|este|algum))? (?:valor|dinheiro|quantia|pagamento)"
)
SALES_FUNDS = (
    r"(?:repasses?|valor(?:es)?|dinheiro|recebiveis?|recebimento|liquidacao|faturamento) "
    r"(?:das?|de|pelas?) (?:(?:minhas?|nossas?|suas?) )?vendas"
)
SALES_MEDIA = (
    r"(?:"
    r"vendas?\s+(?:a|no?|com)\s+(?:(?:cartao|parcelas?)\s+)?(?:credito|debito|cartao)|"
    r"(?:vendi|vendemos|vendido|vendida)\s+(?:a|no?|com)\s+(?:credito|debito|cartao))"
)
SALES_MEDIA_OBJECT = rf"(?:(?:o que|das vendas que) )?{SALES_MEDIA}"
BANK_RECEIPT = (
    r"(?:cair|cai|caiu|entrar|entra|entrou|depositar|depositad[oa]) "
    r"(?:na (?:minha |nossa )?conta|em (?:minha|nossa) conta|no saldo)"
)
SETTLEMENT_FAILURE = (
    r"(?:nao (?:foi (?:creditad[oa]|depositad[oa]|liquidad[oa])|caiu|entrou|creditou|liquidou)|"
    r"atrasou|esta atrasad[oa]|ficou pendente|continua pendente)"
)
TERMINAL = (
    r"(?:maquininhas?|(?:leitor[ae]s?|terminal|terminais|maquina|equipamento)\s+"
    r"(?:de (?:cart(?:ao|oes)|pagamentos?|vendas)|do cartao))"
)
TERMINAL_USE = (
    r"(?:instal(?:ar|acao|ei)|ativ(?:ar|acao|ei)|configur(?:ar|acao|ei)|"
    r"pare(?:ar|amento|ei)|conect(?:ar|ei)|vincul(?:ar|ei)|reinici(?:ar|ei)|"
    r"us(?:ar|o|ei))"
)
TERMINAL_FAULT = (
    r"(?:nao (?:liga|ligou|conecta|funciona|le|imprime|reconhece|aceita)|"
    r"(?:deixou|parou) de (?:ligar|conectar|ler|imprimir|emitir)|"
    r"(?:ficou |esta )?sem (?:impressao|imprimir)|travou|quebrou|desligou|deu erro)"
)

# A ação rege seu objeto ou o nome da operação é o sujeito da falha. Ancorar
# este sujeito evita ler "Pix não chegou" dentro de "o adesivo do Pix não chegou".
DETERMINER = r"(?:(?:[oa]s?|um[as]?|meu|minha|nosso|nossa|esse|essa|este|esta|seu|sua) )?"
SUBJECT_START = rf"(?:^|[,:\u2014])\s*{DETERMINER}"
ASPECT = r"(?:(?:ainda|ja|hoje|agora) ){0,2}"
OBJECT_GAP = rf"[\s'\"“”]+{DETERMINER}"
PIX_OPERATION = r"(?:pix|(?:transferencia|pagamento|cobranca) (?:por|via|em) pix)"
CATEGORY_SUBJECTS = {"pix_operation": rf"pix|{PIX_KEY}", "sales_settlement": rf"{SALES_FUNDS}|{SALES_MEDIA}",
                     "terminal_operation": TERMINAL}
CATEGORY_RELATIONS = {
    "pix_operation": re.compile(
        rf"\b{PIX_ACTION}{OBJECT_GAP}{PIX_OPERATION}\b|"
        rf"\b{KEY_TRANSFER}[\s'\"“”]+(?:por|via|com|pel[ao]|usando)(?: a)? (?:pix|{PIX_KEY})\b|"
        rf"\b(?:comprovante|prazo|estorno|falha) (?:do|de|desse|deste|no) pix\b|"
        rf"{SUBJECT_START}(?P<subject_relation>{PIX_OPERATION} {ASPECT}{OPERATION_FAILURE})\b"
    ),
    "sales_settlement": re.compile(
        rf"\b(?:receb(?:er|i|o|imento)|consult(?:ar|ei)|acompanhar|liquidar|creditar)"
        rf"(?: das?| do| de)?{OBJECT_GAP}{SALES_FUNDS}\b|"
        rf"\b(?:prazo|data|saldo) (?:do|da|de) {SALES_FUNDS}\b|"
        rf"\b(?:{BANK_RECEIPT}){OBJECT_GAP}(?:{SALES_FUNDS}|{SALES_MEDIA_OBJECT})\b|"
        rf"{SUBJECT_START}(?P<subject_relation>(?:{SALES_FUNDS}|{SALES_MEDIA_OBJECT}) {ASPECT}"
        rf"(?:{BANK_RECEIPT}|{SETTLEMENT_FAILURE}))\b"
    ),
    "terminal_operation": re.compile(
        rf"\b{TERMINAL_USE}(?: (?:do|da|de|na|no))?{OBJECT_GAP}{TERMINAL}\b|"
        rf"\b(?:troc(?:ar|a|o)|coloc(?:ar|o)|substitu(?:ir|o|i)) (?:a )?bobina "
        rf"(?:da|do|na|no) {TERMINAL}\b|"
        rf"\b(?:imprimir|emitir) (?:os? )?comprovantes? (?:na|no|pela|pelo) {TERMINAL}\b|"
        rf"{SUBJECT_START}(?P<subject_relation>{TERMINAL} {ASPECT}{TERMINAL_FAULT})\b"
    ),
}

SENTENCE = re.compile(r"[^.!?;\n]+[.!?;]*")
TRANSITION = re.compile(r"\b(?:mas|porém|porem|contudo|no entanto|só que|so que)\b", re.I)
GUIDANCE_QUESTION = (
    r"(?:como|o que)\s+(?:(?:eu|n[oó]s)\s+)?"
    r"(?:posso|podemos|devo|devemos|preciso|fa[çc]o|fazemos|resolvo|resolvemos|"
    r"configuro|configuramos|[^\W\d_]+(?:ar|er|ir))\b"
)
REQUEST_START = re.compile(rf"[:,]\s*(?=(?:e\s+)?{GUIDANCE_QUESTION})", re.I)
POSSIBLE_QUESTION_BOUNDARY = re.compile(rf"[:,]|\b{GUIDANCE_QUESTION}", re.I)
HYPOTHETICAL = re.compile(r"^\s*[,:\s]*(?:se\b|caso\b|supondo\b|na hipotese\b)")
UNCERTAINTY = re.compile(
    r"\b(?:talvez|possivelmente|hipoteticamente|pode ser que|pode ser|"
    r"acho que|suspeito que|suspeito de|imagino que|acredito que|nao (?:sei|sabemos) se)\b"
)
EXCLUDED_FOCUS = re.compile(
    r"\bnao (?:e|era) (?:sobre|referente a|a respeito de)\b|"
    r"\bnao (?:quero|preciso|pretendo|planejo|desejo|vim para|estou (?:perguntando|falando|pedindo))\b|"
    r"\b(?:nao pergunto sobre|sem (?:relacao com|duvidas? (?:sobre|de)))\b"
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
DIRECT_REQUEST = re.compile(
    r"^(?:(?:eu )?(?:preciso|quero|queria|gostaria de|pode[m]?|poderiam) "
    r"(?!(?:saber|entender|resolver|ter|receber ajuda)\b)"
    r"(?:[a-z]+(?:ar|er|ir) |(?:de )?(?:uma|um|outra|outro) (?!orientacao\b|ajuda\b))|"
    r"como (?:eu )?(?:posso |podemos |devo )?"
    r"(?!(?:resolver|resolvo|continuar|prossigo)\b)[a-z]+ (?!isso\b|isto\b|agora\b)[a-z])"
)
INQUIRY = re.compile(
    r"\b(?:como|quando|onde|qual|quanto tempo|quero|queria|gostaria|preciso|podem me "
    r"(?:orientar|explicar|ajudar)|podem dizer|estou (?:preparando|aprendendo))\b|\?"
)
DEFERRED_TIME = r"(?:amanha|no futuro|na proxima|no proximo|semana que vem|mes que vem)"
FUTURE = re.compile(
    rf"\b(?:{DEFERRED_TIME}|"
    r"(?:vou|vamos|irei|iremos) (?:usar|configurar|instalar|receber|vender|fazer|enviar)|"
    r"quando (?:eu )?(?:usar|configurar|instalar|receber|vender|fizer|enviar))\b"
)
CONTRAST_WORDS = re.compile(r"^(?:mas|porem|contudo|no entanto|so que)\b[\s,]*")


@dataclass(frozen=True)
class Clause:
    text: str
    quote_start: int
    quote_end: int
    contrast: bool

    @property
    def excerpt(self):
        return self.text[self.quote_start:self.quote_end]


def clauses(text, start, end, *, priority=False):
    """Mapeia o recorte para a mesma oração usada no casamento de padrões."""
    for sentence in SENTENCE.finditer(text):
        left, right = sentence.span()
        cuts = {left, right, *(m.start() for m in TRANSITION.finditer(text, left, right))}
        if priority and "?" in sentence.group():
            # Vírgula e dois-pontos só separam aqui quando iniciam um pedido
            # de orientação reconhecível. Uma condição mantém a própria oração.
            cuts.update(m.end() for m in REQUEST_START.finditer(text, left, right))
        ordered_cuts = sorted(cuts)
        for begin, stop in zip(ordered_cuts, ordered_cuts[1:]):
            original = text[begin:stop]
            normal = normalized(original)
            body = normal.strip(" ,:")
            leading = len(normal) - len(normal.lstrip(" ,:"))
            contrast = CONTRAST_WORDS.match(body)
            offset = leading + (contrast.end() if contrast else 0)
            quote_start = max(0, len(normalized(original[:max(0, start - begin)])) - offset)
            quote_end = max(0, len(normalized(original[:max(0, end - begin)])) - offset)
            yield Clause(normal[offset:].rstrip(" ,:"), quote_start, quote_end, bool(contrast))


def excluded(clause):
    return any(pattern.search(clause.text) for pattern in (HYPOTHETICAL, UNCERTAINTY, EXCLUDED_FOCUS, INCIDENTAL))


def category_evidence_in_quote(pattern, clause):
    for match in pattern.finditer(clause.text):
        span = match.span("subject_relation") if match.group("subject_relation") else match.span()
        if clause.quote_start <= span[0] and span[1] <= clause.quote_end:
            return True
    return False


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
        changes_focus = FOCUS.search(clause.text) or DIRECT_REQUEST.search(clause.text)
        if (changes_focus and matched != active) or clause.contrast and (asks or matched):
            active.clear()
            evidence_seen = False
        active.update(matched)
        evidence_seen |= criterion in matched and category_evidence_in_quote(selected, clause)

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
LOCAL_ENTITY = (
    r"(?:vendas?|lojas?|filiais?|unidades?|caixas?|turnos?|terminais?|maquininhas?|"
    r"leitor[ae]s?|pagamentos?|transferencias?|clientes?)"
)
LOCALIZED = re.compile(
    r"\b(?:(?:so|apenas|somente) (?:uma|um|algumas|parte d[ao]s?) "
    rf"(?:d[ao]s (?:(?:duas|dois|tres|quatro|cinco|\d+) )?)?{LOCAL_ENTITY} {ASPECT}"
    r"(?:falh(?:a|aram|ou)|par(?:ou|aram)|atras(?:ou|aram)|desligou|(?:esta|ficou) bloquead[oa]|"
    r"nao (?:funciona|funcionou|passou|passaram|conclui|consegue|conseguem)|"
    r"(?:deu|da|dao) erro)|"
    r"(?:falha|erro|atraso|problema|lentidao) (?:apenas |so |restrit[oa] |isolad[oa] )?"
    r"(?:em|numa?|no) (?:uma |um )?(?:loja|caixa|unidade|filial|turno|terminal|"
    r"maquininha|leitor[ae]|venda|pagamento|transferencia|cliente)|"
    r"(?:uma|um) (?:loja|caixa|unidade|filial|turno|terminal|maquininha|leitor[ae]|venda|"
    r"pagamento|transferencia) (?:falhou|parou|atrasou|nao (?:funciona|passou|concluiu)|deu erro))\b"
)
CONTINUED_SERVICE = (
    r"(?<!nao )(?<!nao mais )(?:sigo|seguimos|continuo|continuamos) "
    r"(?:vendendo|cobrando|atendendo|operando|recebendo|processando|pagando)|"
    r"(?:clientes|compradores|equipe) (?:ainda )?(?:continua[m]?|segue[m]?) "
    r"(?:pagando|comprando|vendendo|cobrando|atendendo|recebendo)"
)
ALTERNATIVE = re.compile(
    rf"\b(?:{CONTINUED_SERVICE}|"
    r"(?<!nao )(?<!nao ainda )(?:consigo|conseguimos|posso|podemos) "
    r"(?:atender|vender|receber|cobrar|pagar|operar|processar)|"
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
    r"(?:precisamos|tenho que|teremos de|temos de|vai exigir|exige[m]?|obriga[m]? a) "
    r"(?:refazer|reprocessar|reconciliar|conferir) "
    r"(?:(?:todas as|todos os|cada|muitas|varias|varios|todo o) "
    r"(?:contas|vendas|lancamentos|registros|transacoes|pagamentos|fechamento|lote)|"
    r"o (?:fechamento|lote|balanco) (?:inteiro|completo|todo))|"
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
    r"(?:todos os|todas as) (?:caixas|terminais|maquininhas|leitoras) "
    r"(?:pararam|desligaram|sairam do ar|estao inoperantes)|"
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
PAYMENT_HARM = re.compile(
    r"\b(?:(?:sao|estao sendo|foram|e|esta sendo|foi) (?:debitad[oa]s?|cobrad[oa]s?)|"
    r"(?:esta|estao) (?:debitando|cobrando)|(?:debitou|cobrou)|"
    r"(?:debitos?|cobrancas?) (?:saiu|sairam|apareceu|apareceram)) "
    r"(?:duas vezes|em duplicidade|em dobro)\b"
)
REPEATED_OR_CURRENT = re.compile(
    r"\b(?:agora|neste momento|a cada (?:nova )?(?:tentativa|venda|transacao)|"
    r"toda vez que|(?:esta|estao) (?:sendo|debitando|cobrando))\b"
)
DAMAGE_CONTINUATION = re.compile(
    r"^(?:isso|o problema|a falha|(?:os|esses) debitos|(?:as|essas) cobrancas) "
    r"(?:ainda )?(?:continua[m]?|persiste[m]?|segue[m]?)\b"
)
PAYMENT_HARM_RESOLVED = re.compile(
    r"\b(?:sem (?:debitos?|cobrancas?) (?:indevid[oa]s?|duplicad[oa]s?)|"
    r"(?:debitos?|cobrancas?) (?:indevid[oa]s?|duplicad[oa]s?) (?:cessaram|pararam))\b"
)
CONSEQUENCE = (
    r"(?:(?:vou perder|vamos perder|perderei|perderemos) "
    r"(?:(?:[oa]s?|um[as]?|meu|minha|nosso|nossa|varios|varias) )?"
    r"(?:pagamentos?|vendas?|clientes?|dinheiro|receita|estoque|lote|pedido|prazo|contrato)|"
    r"(?:vai cancelar|vao cancelar|cancelara|cancelarao) (?:o |a )?(?:pedido|lote|contrato|entrega)|"
    r"(?:pedido|lote|contrato|entrega|conta|acesso|operacao|venda|vendas) "
    r"(?:sera|serao|ficara|ficarao) (?:bloquead[oa]s?|cancelad[oa]s?)|"
    r"(?:serei|seremos) multad[oa]s?|"
    r"(?:nao (?:consigo|conseguiremos|poderei|poderemos)) "
    r"(?:abrir|pagar|fechar|entregar|atender)|"
    r"(?:receberei|receberemos|vou receber|vamos receber|levarei|levaremos|"
    r"terei|teremos|havera|vai haver) (?:uma )?multa|"
    r"(?:a multa sera aplicada|a operacao sera interrompida))"
)
IMMEDIATE_DEADLINE = (
    r"(?:agora|imediatamente|nos proximos minutos|"
    r"em (?:[1-9]|[1-5]\d|60|dez|quinze|trinta) minutos|ate hoje|ainda hoje|hoje)"
)
IMMEDIATE_CONSEQUENCE = re.compile(relations(CONSEQUENCE, IMMEDIATE_DEADLINE, gap=7))
LATER_DEADLINE = re.compile(rf"\b{DEFERRED_TIME}\b")
PENDING_CONDITION = re.compile(
    r"^(?:se|caso) (?:o |a )?(?:pagamento|repasse|transferencia|credito|venda|operacao) "
    r"nao (?:sair|cair|entrar|chegar|passar|for (?:liberad[oa]|creditad[oa]))\b[^,;]{0,60},"
)
HANDLED_DEADLINE = re.compile(
    r"\b(?:nao (?:ha|havera|vai haver|vou receber|vamos receber|receberei|receberemos) (?:uma )?multa|"
    r"nao (?:sera|serao|ficara|ficarao) (?:bloquead[oa]s?|cancelad[oa]s?|multad[oa]s?)|"
    r"a multa (?:ja )?(?:foi paga|foi retirada|foi cancelada)|"
    r"(?<!nao )(?:consigo|conseguimos|consegui|conseguiremos|podemos|poderei) "
    r"(?:pagar|quitar) (?:a |uma )?multa|"
    r"(?<!nao )(?:consegui|conseguimos|poderei|podemos) "
    r"(?:pagar|entregar|cumprir) (?:em dia|a tempo|no prazo))\b"
)
NOW = re.compile(r"\b(?:agora|imediatamente|neste momento|nos proximos minutos)\b")
CURRENT_PROBLEM = re.compile(
    rf"\b(?:{OPERATION_FAILURE}|(?:nao|mal) (?:consigo|conseguimos)|travou|quebrou|"
    r"lentidao|bloquead[oa]s?|parad[oa]s?|deixou de|parou de|"
    r"(?:nao (?:liga|conecta|le|imprime|reconhece|aceita)))\b"
)
CURRENT_LOSS = re.compile(r"\b(?:perdendo|vou perder)\b")
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
NEGATING_SCOPE = re.compile(
    r"\b(?:nao(?! (?:so|apenas|somente)\b)|nunca|jamais|nem|ninguem|nenhu(?:m|ma|ns|mas)|"
    r"sem(?! duvida\b))\b"
)
UNASSERTED_SCOPE = re.compile(
    r"\b(?:se|caso|supondo|na hipotese|em tese|"
    r"(?:confirmar|verificar|checar|conferir|averiguar|descobrir|saber) (?:que|como|quando|por que))\b"
)
URGENT_PATTERNS = (IMMEDIATE_LOSS, IMMEDIATE_CONSEQUENCE, TOTAL_STOP, PAYMENT_HARM)
PRIORITY_EVIDENCE = {
    "routine": (ROUTINE, NORMAL_OR_RECOVERED),
    "localized_impact": (LOCALIZED,),
    "broad_impact": (BROAD,),
    "immediate_harm": URGENT_PATTERNS,
}


def any_match(patterns, text):
    return any(pattern.search(text) for pattern in patterns)


def asserted_matches(pattern, text, *, offset=0):
    """Só usa efeitos declarados. Negações internas podem afirmar uma falha."""
    if "?" in text or any(marker.search(text, offset) for marker in (UNCERTAINTY, UNASSERTED_SCOPE)):
        return ()
    # Para prazos em ordem inversa, o prazo pode vir antes de um negador.
    # A captura nomeada marca o início do efeito, e não o início do prazo.
    return tuple(match for match in pattern.finditer(text, offset)
                 if not NEGATING_SCOPE.search(text, offset, match.start(match.lastgroup or 0)))


def pending_consequences(clause):
    condition = PENDING_CONDITION.match(clause.text)
    # Só uma condição operacional reconhecida abre escopo para o consequente.
    offset = condition.end() if condition else 0
    if LATER_DEADLINE.search(clause.text, offset):
        return ()
    return asserted_matches(IMMEDIATE_CONSEQUENCE, clause.text, offset=offset)


def ambiguous_impact(text):
    """Uma afirmação possível numa pergunta mista já impede classificar rotina."""
    if "?" not in text:
        return False
    for pattern in URGENT_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            cut = POSSIBLE_QUESTION_BOUNDARY.search(text, match.end())
            if cut and asserted_matches(pattern, text[:cut.start()]):
                return True
    return False


def priority_reason(criterion, context):
    proof = PRIORITY_EVIDENCE[criterion]
    if not any(any_match(proof, clause.excerpt) for clause in context):
        return "insufficient_relation"

    active = [clause for clause in context if not excluded(clause)
              or (PENDING_CONDITION.match(clause.text) and pending_consequences(clause)
                  and not any_match((EXCLUDED_FOCUS, INCIDENTAL), clause.text))]
    recovery = max((i for i, clause in enumerate(active) if PAST_OR_RESTORED.search(clause.text)), default=-1)
    current = [clause for clause in active[recovery + 1:] if not FUTURE.search(clause.text)]
    # Orientação futura é suporte de rotina. Fatos futuros por si sós não são
    # prova de prejuízo atual. Um prazo futuro explícito pode ser imediato.
    pending = active[recovery + 1:]
    handled = max((i for i, clause in enumerate(pending) if asserted_matches(HANDLED_DEADLINE, clause.text)), default=-1)
    immediate = [(clause, match) for clause in pending[handled + 1:] for match in pending_consequences(clause)]
    no_impact = any(asserted_matches(NEGATED_IMPACT, clause.text) for clause in current)
    alternative = any(asserted_matches(ALTERNATIVE, clause.text) and not asserted_matches(NO_ALTERNATIVE, clause.text)
                      for clause in current)
    no_alternative = any(asserted_matches(NO_ALTERNATIVE, clause.text) for clause in current)
    total = [(clause, match) for clause in current for match in asserted_matches(TOTAL_STOP, clause.text)]
    total_without_alternative = total if no_alternative and not alternative else []
    payment_damage = False
    loss = [(clause, match) for clause in current for match in asserted_matches(IMMEDIATE_LOSS, clause.text)]
    for index, clause in enumerate(current):
        damage = asserted_matches(PAYMENT_HARM, clause.text)
        if not damage or asserted_matches(PAYMENT_HARM_RESOLVED, clause.text):
            continue
        payment_damage = True
        if (REPEATED_OR_CURRENT.search(clause.text)
                or any(asserted_matches(DAMAGE_CONTINUATION, c.text) for c in current[index + 1:index + 2])):
            loss.extend((clause, match) for match in damage)
    urgent = [] if no_impact else loss + immediate + total_without_alternative
    broad = [clause for clause in current if BROAD.search(clause.text) and not NEGATED_IMPACT.search(clause.text)]
    local = [clause for clause in current if LOCALIZED.search(clause.text) and not NEGATED_IMPACT.search(clause.text)]
    if urgent:
        cited = any(clause.quote_start <= match.start() and match.end() <= clause.quote_end
                    for clause, match in urgent)
        return "supported_relation" if criterion == "immediate_harm" and cited else "context_conflict"
    if (no_alternative and alternative and total) or (no_impact and (loss or immediate or total)):
        return "context_conflict"
    elif broad and not any(NOW.search(clause.text) for clause in broad):
        found, support = "broad_impact", broad
    elif local and alternative and not total and not broad and not no_alternative:
        found, support = "localized_impact", local
    elif not (local or total or broad or loss or immediate or payment_damage
              or any(CURRENT_PROBLEM.search(c.text) or asserted_matches(CURRENT_LOSS, c.text) for c in current)
              or any(ambiguous_impact(c.text) for c in context)):
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

    context = list(clauses(item["text"], data["start"], data["end"], priority=field == "priority"))
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
            # raw é a saída IPC após a política. A proposta do fornecedor
            # permanece em audit.fields e no conteúdo original.
            choices[field] = choice("abstained", c01.ABSTENTION, "policy")
        else:
            # O corpo bruto fica na auditoria. Um código válido não pode
            # ocupar raw quando o objeto privado que o carrega está inválido.
            choices[field] = choice(outcome, None, evidence["reason"])
    return choices
