"""Catálogo local por marca e controles de aplicabilidade da E01."""

from copy import deepcopy
from pathlib import Path
import re
import unicodedata

if __package__:
    from .e01_contracts import read_json_object, read_private_schema, validator
else:
    from e01_contracts import read_json_object, read_private_schema, validator


BRANDS = {
    "11111111-1111-4111-8111-111111111111": "aurora",
    "22222222-2222-4222-8222-222222222222": "horizonte",
}
HANDOFF_REASONS = {"human_requested", "no_guidance", "sensitive_operation"}
RESOLUTION_QUESTION = "O procedimento resolveu o problema?"
RESOLVE_TEXT = "Certo, vou encerrar este atendimento."
HANDOFF_TEXT = "Vou encaminhar seu atendimento para a equipe."

# O piloto reconhece pedidos de consulta e de encaminhamento em português.
_CONSULTATION = re.compile(
    r"^(?:(?:oi|ola|por favor) )*(?:(?:onde|como) (?:eu |posso |consigo )?"
    r"|(?:quero|preciso|gostaria de|nao consigo) )(?:consult|ver\b|vej|acess|encontr|ach|localiz|busc)"
)
_HUMAN_ROLE = r" (?:um |uma |o |a )?(?:pessoa|atendente|humano|humana|analista|time humano|equipe humana)\b"
_CALL_HUMAN = re.compile(r"(?:por favor )?chame" + _HUMAN_ROLE + r"(?: (?:agora|por favor))?")
_HUMAN_REQUEST = re.compile(
    r"\b(?:(?:quero|queria|preciso|posso|gostaria de) (?:falar|conversar) com"
    r"|(?:me (?:passe|transfira|encaminhe)|(?:pode )?(?:me )?(?:passar|transferir|encaminhar)) para"
    r"|quero|queria|preciso de|gostaria de)" + _HUMAN_ROLE
)
_SENSITIVE_REQUEST = re.compile(
    r"\b(?:estorne|reembolse|cancel(?:e|ar) (?:o |um )?pix)\b"
    r"|(?:^|\b(?:quero|queria|preciso|gostaria de|pode|para) )(?:estornar|reembolsar)\b"
    r"|\b(?:alter(?:e|ar)|troc(?:a|ar|que)) (?:os |meus |a |minha )?(?:dados bancarios|conta bancaria|chave pix)\b"
    r"|\btransfer(?:e|ir) (?:o |meu )?(?:saldo|dinheiro|valores)\b"
    r"|\b(?:faz(?:er|a)|solicitar|realiz(?:ar|e)|execut(?:ar|e)|process(?:ar|e)"
    r"|efetu(?:ar|e)|quero|preciso de) (?:um |uma |o |a |meu )?"
    r"(?:estorno|reembolso|pagamento|transferencia|cancelamento (?:do|de) pix)\b"
)
_QUOTED_SPEECH = re.compile(r'"[^"]*"|“[^”]*”|«[^»]*»|‘[^’]*’|\x27[^\x27]*\x27')
_CLAUSE_BOUNDARY = re.compile(r"[.!?;:,\n]+|\b(?:mas|porém|contudo|só que)\b", re.IGNORECASE)
_NEGATED_REQUEST = re.compile(
    r"\b(?:nao|nunca|nem|sem) (?:(?:quero|queria|preciso(?: de)?|gostaria de"
    r"|pretendo|vou|posso|pode(?:mos|m)?|consigo|consegue(?:m)?|conseguimos"
    r"|devo|deve(?:mos|m)?|para|pra|estou pedindo (?:para|pra)) )?(?:(?:mais|mesmo) )?$"
)
_NON_REQUEST_MARKERS = re.compile(r'["“”«»]|\b(?:ignore|fingir|suponha|hipoteticamente|apenas um exemplo)\b',
                                re.IGNORECASE)
_CONTRADICTION = re.compile(r"\b(?:mas nao|porem nao|nao quero|nao e sobre|nao era sobre|talvez|se por acaso)\b")


def _tokens(text):
    plain = "".join(character for character in unicodedata.normalize("NFKD", text.casefold())
                    if not unicodedata.combining(character))
    return " ".join(re.findall(r"[^\W_]+", plain))


def _index(rows):
    result = {row["id"]: row for row in rows}
    _require(len(result) == len(rows), "duplicate_knowledge_id")
    return result


def _require(predicate, code):
    if not predicate:
        raise ValueError(code)


def _author(row, kind):
    return row["author"]["type"] == kind


def latest_customer(history):
    return next(row for row in reversed(history) if _author(row, "customer"))


def _confirmed(history, question, answers, *, suffix=False):
    if len(history) < 2:
        return False
    previous, current = history[-2:]
    if not (_author(previous, "ai") and _author(current, "customer")):
        return False
    asked = previous["text"].endswith(question) if suffix else previous["text"] == question
    answer = current["text"].strip().casefold()
    if answer.endswith((".", "!")):
        answer = answer[:-1]
    return asked and answer in answers


def _handoff_reason(text):
    direct_speech = _QUOTED_SPEECH.sub(" ", text)
    clauses = [_tokens(clause) for clause in _CLAUSE_BOUNDARY.split(direct_speech)]
    for reason, pattern in (("sensitive_operation", _SENSITIVE_REQUEST), ("human_requested", _HUMAN_REQUEST)):
        for clause in clauses:
            if reason == "human_requested" and _NON_REQUEST_MARKERS.search(clause):
                continue
            if any(not _NEGATED_REQUEST.search(clause[:match.start()]) for match in pattern.finditer(clause)):
                return reason
    # Uma condição ou citação introdutória pode estar separada por vírgula ou dois-pontos.
    if any(_CALL_HUMAN.fullmatch(_tokens(sentence)) for sentence in re.split(r"[.!?;\n]+", direct_speech)):
        return "human_requested"
    return None


class Knowledge:
    @classmethod
    def load(cls, root: Path):
        root = Path(root)
        schema = read_private_schema("knowledge")
        ontology = read_json_object((root / "ontology.json").read_bytes())
        _require(validator(schema, "ontology").is_valid(ontology), "invalid_ontology")
        brand_validator = validator(schema, "brand")
        brands = {}
        for identifier, slug in BRANDS.items():
            brand_file = root / "brands" / f"{slug}.json"
            brand = read_json_object(brand_file.read_bytes())
            _require(brand_validator.is_valid(brand), "invalid_brand_knowledge")
            _require((brand["brand_id"], brand["slug"]) == (identifier, slug), "brand_origin")
            brands[identifier] = brand
        return cls(ontology, brands, validator(read_private_schema("decision")))

    def __init__(self, ontology, brands, decision_validator):
        self._version = ontology["version"]
        self._subjects = _index(ontology["subjects"])
        self._intents = _index(ontology["intents"])
        self._conditions = _index(ontology["conditions"])
        self._validate_references(brands)
        self._brands = brands
        self._decision = decision_validator
        self._synonyms = {key: tuple(" " + _tokens(term) + " " for term in intent["synonyms"])
                          for key, intent in self._intents.items()}

    def _validate_references(self, brands):
        for intent in self._intents.values():
            _require(intent["subject_id"] in self._subjects, "subject_ref")
            _require(all(_tokens(term) for term in intent["synonyms"]), "empty_normalized_synonym")
        questions = {condition["question"] for condition in self._conditions.values()}
        _require(len(questions) == len(self._conditions), "duplicate_condition_question")
        for brand in brands.values():
            _require(brand["ontology_version"] == self._version, "ontology_version")
            sources = _index(brand["sources"])
            procedures = _index(brand["procedures"])
            rules = _index(brand["handoff_rules"])
            prefix = brand["slug"] + "."
            _require(all(key.startswith(prefix) for key in (*sources, *procedures, *rules)), "foreign_brand_id")
            _require({rule["reason"] for rule in rules.values()} == HANDOFF_REASONS and len(rules) == len(HANDOFF_REASONS),
                     "invalid_handoff_rules")
            for item in (*procedures.values(), *rules.values()):
                _require(item["source_id"] in sources, "source_ref")
            for item in procedures.values():
                _require(item["intent_id"] in self._intents, "intent_ref")
                _require(set(item["requires"]) <= self._conditions.keys(), "condition_ref")
                _require(len(self._procedure_text(item)) <= 1000, "procedure_text_too_long")

    def _match(self, text):
        normalized = " " + _tokens(text) + " "
        return {key for key, synonyms in self._synonyms.items() if any(term in normalized for term in synonyms)}

    def _category(self, procedure):
        return self._subjects[self._intents[procedure["intent_id"]]["subject_id"]]["category"]

    @staticmethod
    def _procedure_text(procedure):
        return " ".join([*procedure["steps"], RESOLUTION_QUESTION])

    def select(self, request: dict) -> dict:
        brand = self._brands.get(request["brand_id"])
        _require(brand is not None, "unknown_knowledge_brand")
        payload = request["payload"]
        customers = [row for row in payload["history"] if _author(row, "customer")]
        _require(bool(customers), "missing_customer_history")
        matched = set().union(*(self._match(row["text"]) for row in customers))
        procedures = [row for row in brand["procedures"] if row["intent_id"] in matched]
        current = self._match(customers[-1]["text"])
        category = payload["classification"]["category"]
        procedures.sort(key=lambda row: (self._category(row) != category, row["intent_id"] not in current, row["id"]))
        sources = {row["source_id"] for row in (*procedures, *brand["handoff_rules"])}
        conditions = {condition for row in procedures for condition in row["requires"]}
        return deepcopy({
            "brand_id": brand["brand_id"],
            "ontology_version": self._version,
            "knowledge_version": brand["version"],
            "procedures": procedures,
            "sources": [row for row in brand["sources"] if row["id"] in sources],
            "handoff_rules": brand["handoff_rules"],
            "conditions": [row for key, row in self._conditions.items() if key in conditions],
        })

    def _reply_options(self, history, procedures):
        latest = history[-1]
        if not _author(latest, "customer") or _NON_REQUEST_MARKERS.search(latest["text"]):
            return {}
        normalized = _tokens(latest["text"])
        if _CONTRADICTION.search(normalized):
            return {}
        latest_intents = self._match(latest["text"])
        previous_customer = next((row for row in reversed(history[:-2]) if _author(row, "customer")), None)
        previous_intents = self._match(previous_customer["text"]) if previous_customer else set()
        options = {}
        for procedure in procedures:
            intent = procedure["intent_id"]
            if not procedure["requires"]:
                if latest_intents == {intent} and _CONSULTATION.match(normalized):
                    options[procedure["id"]] = ("procedure", self._procedure_text(procedure))
                continue
            question = self._conditions[procedure["requires"][0]]["question"]
            if previous_intents == {intent} and _confirmed(history, question, {"sim", "sim, confirmo"}):
                options[procedure["id"]] = ("procedure", self._procedure_text(procedure))
            elif latest_intents == {intent} and not any(
                _author(row, "ai") and row["text"] == question for row in history[:-1]
            ):
                options[procedure["id"]] = ("clarify", question)
        return options

    def applicable_options(self, request: dict, candidates: dict) -> list:
        history = request["payload"]["history"]
        reason = _handoff_reason(latest_customer(history)["text"])
        sources = _index(candidates["sources"])

        def source_refs(item):
            source = sources[item["source_id"]]
            return [{"id": source["id"], "version": source["version"]}]

        if reason is None:
            if _confirmed(history, RESOLUTION_QUESTION, {"sim, resolveu", "o problema foi resolvido"}, suffix=True):
                return [{"action": "resolve", "text": RESOLVE_TEXT, "source_refs": []}]
            replies = self._reply_options(history, candidates["procedures"])
            if replies:
                procedures = _index(candidates["procedures"])
                return [{"action": "reply", "kind": kind, "procedure_id": identifier, "text": text,
                         "source_refs": source_refs(procedures[identifier])}
                        for identifier, (kind, text) in replies.items()]
            reason = "no_guidance"
        return [{"action": "handoff", "rule_id": rule["id"], "text": HANDOFF_TEXT, "source_refs": source_refs(rule)}
                for rule in candidates["handoff_rules"] if rule["reason"] == reason]

    def validate_decision(self, request: dict, candidates: dict, decision: dict) -> None:
        _require(self._decision.is_valid(decision), "invalid_decision_schema")
        _require(candidates == self.select(request), "invalid_candidate_snapshot")
        history = request["payload"]["history"]
        _require(latest_customer(history)["id"] in decision["message_ids"], "latest_customer_origin")
        _require(set(decision["message_ids"]) <= {row["id"] for row in history}, "message_origin")
        options = self.applicable_options(request, candidates)
        action = decision["action"]
        if action == "resolve":
            _require(any(row["action"] == action and row["text"] == decision["text"] for row in options),
                     "resolution_evidence")
            return

        if action == "reply":
            id_field, candidates_field, evidence = "procedure_id", "procedures", "reply_evidence"
        else:
            id_field, candidates_field, evidence = "rule_id", "handoff_rules", "handoff_evidence"
        identifier = decision[id_field]
        _require(identifier in _index(candidates[candidates_field]), "candidate_origin")
        option = next((row for row in options if row.get(id_field) == identifier), None)
        _require(option is not None and option["text"] == decision["text"] and option.get("kind") == decision.get("kind"),
                 evidence)
        _require(option["source_refs"] == decision["source_refs"], "source_origin")
