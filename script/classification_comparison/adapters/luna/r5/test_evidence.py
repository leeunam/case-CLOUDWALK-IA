"""Ensaios artificiais R5 com transporte local injetado. Nenhum lote é carregado."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from adapters.luna.r5.adapter import MODEL, R5Adapter, identity_for, replay_envelope, validate_envelope
from adapters.luna.r5.evidence import POLICY_SHA256, build_audit, project_choices
from adapters.qwen.adapter import Blocked
from common import c01, decide, decode, encode

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CATALOG = c01.read(ROOT / "script/f08/jev/catalog.json")
RUN_ID = "r5-a-sintetico"
POR_CAMPO = {"category": "terminal", "priority": "basic"}
ABSTAIN = {"code": "informacao_insuficiente", "criterion": "none", "quote": ""}


def item(text, *, case_id="sintetico-alfa", requested=("category",), received=None):
    if received is None:
        received = {field: value for field, value in POR_CAMPO.items() if field not in requested}
    return {"contract_version": "1.1.0", "id": case_id, "text": text, "brand": "marca-sintetica",
            "catalog": deepcopy(CATALOG), "received": received, "missing": list(requested)}


def prediction(code, criterion, quote):
    return {"code": code, "criterion": criterion, "quote": quote}


def response(payload, *, raw=None, model=MODEL, finish="stop", refusal=None, usage=None):
    message = {"content": encode(payload) if raw is None and payload is not None else raw}
    if refusal is not None:
        message["refusal"] = refusal
    return {"model": model, "choices": [{"message": message, "finish_reason": finish}], "usage": usage}


class Gateway:
    def __init__(self, output, *, status=200, failure=None, before_send=False, events=None):
        self.output = output
        self.status = status
        self.failure = failure
        self.before_send = before_send
        self.events = [] if events is None else events
        self.bodies = []
        self.closed = 0

    def __call__(self, body, deadline, dispatched):
        self.events.append("transport")
        if self.before_send:
            raise self.failure
        dispatched()
        self.bodies.append((body, deadline))
        self.events.append("post")
        if self.failure is not None:
            raise self.failure
        return self.status, encode(self.output).encode("utf-8")

    def close(self):
        self.closed += 1


class Budget:
    max_tokens = 384
    cost_unit = "USD"
    tariff = {"source": "tarifa artificial", "date": "2026-11-25", "unit": "USD/Mtoken",
              "input": "1", "output": "2", "cache_read": "1", "cache_write": "1"}

    def __init__(self, events, *, failure=None):
        self.events = events
        self.reservations = []
        self.usage = []
        self.failure = failure

    def reserve(self, case_id, body_size):
        self.events.append("reserve")
        self.reservations.append((case_id, body_size))
        if self.failure is not None:
            raise self.failure

    def observe(self, usage):
        self.events.append("usage")
        self.usage.append(usage.copy())


class EvidenceTests(unittest.TestCase):
    def classify(self, entry, output, *, gateway=None, **options):
        gateway = gateway or Gateway(response(output))
        adapter = R5Adapter(identity_for("fixture"), RUN_ID, "Instrução artificial.", gateway, **options)
        self.addCleanup(adapter.close)
        self.assertEqual(gateway.events, [])
        envelope = adapter.classify(entry)
        self.assertEqual(replay_envelope(entry, envelope, policy_sha256=POLICY_SHA256), envelope["audit"])
        return envelope, adapter, gateway

    def assert_field(self, entry, value, *, status, reason=None):
        field, = entry["missing"]
        envelope, _, gateway = self.classify(entry, {field: value})
        observation = envelope["observation"]
        evidence = envelope["audit"]["fields"][field]
        selected = observation["choices"][field]
        self.assertEqual(selected["status"], status)
        if reason:
            self.assertEqual(evidence["reason"], reason)
        self.assertEqual((observation["requests"], observation["questions"], len(gateway.bodies)), (1, 1, 1))
        return evidence

    def test_categorias_procuram_operacao_em_contexto(self):
        scenarios = {
            ("pix", "pix_operation"): (
                ("Fiz um Pix e não chegou ao comerciante.", "predicted"),
                ("Minha dúvida não é sobre fazer um Pix.", "abstained"),
                ("Talvez seja por tentar enviar um Pix.", "abstained"),
                ("Por sinal, consigo fazer um Pix quando preciso.", "abstained"),
                ("Vou fazer um Pix amanhã.", "abstained"),
                ("Como faço um Pix na próxima semana?", "predicted"),
                ("Gostaria de enviar um valor pela chave do destinatário.", "predicted"),
            ),
            ("payouts", "sales_settlement"): (
                ("O repasse das nossas vendas não entrou.", "predicted"),
                ("Minha dúvida não é sobre quando entra o valor das vendas.", "abstained"),
                ("Talvez o valor das vendas não tenha entrado na conta.", "abstained"),
                ("Por sinal, posso consultar o repasse das vendas.", "abstained"),
                ("Vou receber o valor das vendas na semana que vem.", "abstained"),
                ("Qual o prazo para receber o valor das vendas do próximo mês?", "predicted"),
                ("Quanto tempo leva para cair na conta o que vendi a débito?", "predicted"),
            ),
            ("terminal", "terminal_operation"): (
                ("A leitora de cartões deixou de imprimir os comprovantes.", "predicted"),
                ("O pedido não é sobre configurar a maquininha.", "abstained"),
                ("Talvez a leitora de cartões tenha deixado de imprimir os comprovantes.", "abstained"),
                ("Por sinal, ontem consegui ativar uma maquininha.", "abstained"),
                ("Vou instalar a maquininha amanhã.", "abstained"),
                ("Como instalar a leitora de cartões no próximo turno?", "predicted"),
            ),
        }
        for (code, criterion), cases in scenarios.items():
            for text, status in cases:
                with self.subTest(code=code, text=text):
                    self.assert_field(item(text), prediction(code, criterion, text), status=status)

    def test_termos_genericos_e_relacoes_em_oracoes_distintas_nao_bastam(self):
        for text, code, criterion in (
            ("O valor sumiu. Vi uma notificação no aparelho e no aplicativo.", "payouts", "sales_settlement"),
            ("Faço vendas no bairro. O depósito da minha tia não entrou.", "payouts", "sales_settlement"),
            ("Preciso transferir um valor. O aplicativo mostra um QR.", "pix", "pix_operation"),
            ("A leitora de cartões está na gaveta. A impressora de etiquetas não ligou.", "terminal", "terminal_operation"),
        ):
            with self.subTest(text=text):
                self.assert_field(item(text), prediction(code, criterion, text), status="abstained",
                                  reason="insufficient_relation")

    def test_venda_ausente_do_lote_creditado(self):
        sale = "A venda no débito de ontem não apareceu no depósito já creditado na nossa conta."
        other = "Uma venda no cartão não foi incluída no lote que entrou no saldo."
        cases = [
            (sale, sale, True),
            (other, other, True),
            (sale, "depósito já creditado na nossa conta", False),
            ("Por exemplo, " + sale, sale, False),
            ("Se isso ocorrer, " + sale, sale, False),
            ("Não é verdade: " + sale, sale, False),
            ("O cupom d" + sale.lower(), sale[2:], False),
            (sale + " Mas minha dúvida é como configurar a maquininha.", sale, False),
            ("Uma venda no cartão não entrou no lote de notas fiscais.", "venda no cartão não entrou", False),
            ("Uma venda no débito não entrou no lote que cair na minha conta.", "venda no débito não entrou", False),
        ]
        for text, quote, supported in cases:
            with self.subTest(text=text, quote=quote):
                self.assert_field(item(text), prediction("payouts", "sales_settlement", quote),
                                  status="predicted" if supported else "abstained")

    def test_paralisacao_de_pagadores_exige_ausencia_de_alternativa(self):
        stop = "Nenhum dos clientes pode fazer o pagamento"
        lack = "não temos outro meio de pagamento"
        cases = [
            (stop + " e " + lack + ".", stop, True),
            ("Ninguém consegue pagar agora. Não temos outra forma de receber.", "Ninguém consegue pagar agora", True),
            (stop + " e " + lack + ".", lack, False),
            (stop + " e " + lack + "?", stop, False),
            ("Não é verdade que " + stop.lower() + " e " + lack + ".", stop.lower(), False),
            ("Se " + stop.lower() + " e " + lack + ", peço ajuda.", stop.lower(), False),
            (stop + " e " + lack + ". Mas temos outro meio de cobrança.", stop, False),
            (stop + " e " + lack + ". Mas os clientes já conseguem pagar por Pix.", stop, False),
            (stop + " e " + lack + ", e seguimos vendendo pelo celular.", stop, False),
            (stop + ". Não temos outro meio e já recebemos por Pix.", stop, False),
            (stop + " e " + lack + ", e os clientes agora conseguem pagar por Pix.", stop, False),
            (stop + " e não temos outro meio de transporte.", stop, False),
            (stop + " da mensalidade. Não temos outra forma de receber.", stop, False),
            (stop + " por cartão. Não temos outra forma de receber.", stop, False),
        ]
        for text, quote, supported in cases:
            with self.subTest(text=text, quote=quote):
                self.assert_field(item(text, requested=("priority",)), prediction("urgent", "immediate_harm", quote),
                                  status="predicted" if supported else "abstained")

    def test_ajuste_antes_do_uso_vincula_pedido_e_terminal_e_conserva_impacto(self):
        device = "Compramos uma leitora de cartões. "
        setup = "Onde posso ajustar o brilho da tela antes de abrir a loja?"
        cases = [
            (device + setup, True, True),
            ("Recebi um novo terminal de pagamento. Como diminuir a fonte da tela antes de começar a atender?", True, True),
            ("Recebi um tablet. " + setup, False, False),
            ("Talvez eu tenha recebido uma maquininha. " + setup, False, False),
            ("Não comprei uma leitora de cartões. " + setup, False, False),
            ("Comprei uma etiqueta para a maquininha. " + setup, False, False),
            (device + setup.replace("da tela", "da tela do celular"), False, False),
            (device + "Não quero saber disso. " + setup, False, False),
            (device + setup + " Ninguém consegue pagar por cartão.", True, False),
            (device + setup + " Não é verdade que ninguém consegue pagar.", True, True),
            (device + setup + " Estamos perdendo clientes a cada minuto.", True, False),
        ]
        for text, terminal, routine in cases:
            with self.subTest(text=text):
                for field, code, criterion, accepted in (
                    ("category", "terminal", "terminal_operation", terminal),
                    ("priority", "basic", "routine", routine),
                ):
                    quote = text.split("?")[0] + "?"
                    self.assert_field(item(text, requested=(field,)), prediction(code, criterion, quote),
                                      status="predicted" if accepted else "abstained")
        for cid in ("preparo-sintetico", "outra-chave-sintetica"):
            entry = item(device + setup, case_id=cid, requested=("category", "priority"))
            predictions = {"category": prediction("terminal", "terminal_operation", device + setup),
                           "priority": prediction("basic", "routine", setup)}
            envelope, _, gateway = self.classify(entry, predictions)
            decision = decide(entry, envelope["observation"], CATALOG, RUN_ID)
            self.assertEqual(decision["outcome"], "complete")
            self.assertEqual(len(gateway.bodies), 1)
            self.assertEqual({f: outcome["applied"] for f, outcome in decision["fields"].items()},
                             {"category": "terminal", "priority": "basic"})
        self.assert_field(item(device + setup), prediction("terminal", "terminal_operation", setup), status="abstained")
        excerpt = "leitora de cartões. Onde posso ajustar o brilho da tela"
        self.assert_field(item(device + setup), prediction("terminal", "terminal_operation", excerpt), status="predicted")

    def test_falha_da_operacao_exige_o_sujeito_correto(self):
        for code, criterion, asserted, incidental in (
            ("pix", "pix_operation", "O Pix não chegou ao destinatário.",
             "O adesivo do Pix não chegou pelo correio."),
            ("terminal", "terminal_operation", "A maquininha não imprime os comprovantes.",
             "A etiqueta que veio com a maquininha não chegou aos atendentes."),
            ("payouts", "sales_settlement", "O repasse das vendas não creditou.",
             "Quando vendi a débito o cupom saiu ilegível."),
        ):
            with self.subTest(code=code):
                self.assert_field(item(asserted), prediction(code, criterion, asserted), status="predicted")
                text = incidental + " Quero uma segunda via."
                self.assert_field(item(text), prediction(code, criterion, incidental), status="abstained")
        # O recorte remove o verdadeiro sujeito de "não chegou".
        text = "O adesivo do Pix não chegou pelo correio. Quero outra via do adesivo."
        self.assert_field(item(text), prediction("pix", "pix_operation", "Pix não chegou"), status="abstained")
        text = "O adesivo do Pix não chegou, fiz um Pix esta manhã."
        self.assert_field(item(text), prediction("pix", "pix_operation", "Pix não chegou"), status="abstained")
        text = "O Pix não chegou ao destinatário."
        self.assert_field(item(text), prediction("pix", "pix_operation", "Pix não chegou"), status="predicted")

    def test_negacao_de_pedido_e_novo_objeto_fora_da_citacao(self):
        for code, criterion, action in (
            ("pix", "pix_operation", "fazer um Pix"),
            ("terminal", "terminal_operation", "configurar a maquininha"),
            ("payouts", "sales_settlement", "consultar o valor das vendas"),
        ):
            with self.subTest(code=code):
                for opening in ("Não quero ", "Não pretendo "):
                    text = opening + action + ". Preciso atualizar meu endereço."
                    self.assert_field(item(text), prediction(code, criterion, action), status="abstained")
                quote = "Como " + action + "?"
                self.assert_field(item(quote), prediction(code, criterion, quote), status="predicted")
                self.assert_field(item(quote + " Preciso atualizar meu endereço."),
                                  prediction(code, criterion, quote), status="abstained")
                self.assert_field(item(quote + " Como altero meu endereço?"),
                                  prediction(code, criterion, quote), status="abstained")
        quote = "Como substituir a bobina da leitora de cartões?"
        text = "Não estou perguntando sobre Pix. " + quote
        self.assert_field(item(text), prediction("terminal", "terminal_operation", quote), status="predicted")

    def test_trecho_e_contexto_mudam_veto_e_independem_do_id(self):
        quote = "O valor das vendas não entrou."
        value = prediction("payouts", "sales_settlement", quote)
        for case_id in ("sintetico-beta", "sintetico-gama"):
            self.assert_field(item(quote, case_id=case_id), value, status="predicted", reason="supported_relation")
            for suffix in (
                " Mas minha dúvida é como instalar a leitora de cartões.",
                " Minha dúvida não é sobre o recebimento das vendas.",
                " Minha solicitação é corrigir o endereço de contato.",
            ):
                self.assert_field(item(quote + suffix, case_id=case_id), value, status="abstained", reason="context_conflict")
        self.assert_field(item(quote), prediction("payouts", "sales_settlement", "valor das vendas"),
                          status="abstained", reason="insufficient_relation")
        background = "O repasse das vendas caiu normalmente. Como troco a bobina da maquininha?"
        self.assert_field(item(background), prediction("terminal", "terminal_operation", "Como troco a bobina da maquininha?"),
                          status="predicted")

    def test_prioridades_preservam_escopo_impacto_e_alternativa(self):
        routine = "Como posso instalar a leitora de cartões?"
        local = "Só uma loja não consegue vender."
        availability = " As outras lojas funcionam normalmente."
        broad = "Quatro lojas ficaram sem receber pagamentos."
        total = "Nenhuma venda passa."
        no_alternative = " Não temos outra forma de receber."
        loss = "Estamos perdendo vendas a cada minuto."
        scenarios = [
            ("basic", "routine", routine, routine, "predicted"),
            ("basic", "routine", "Preciso muito de ajuda logo.", "Preciso muito de ajuda logo.", "abstained"),
            ("basic", "routine", routine + " " + loss, routine, "abstained"),
            ("intermediate", "localized_impact", local + availability, local, "predicted"),
            ("intermediate", "localized_impact", local, local, "abstained"),
            ("intermediate", "localized_impact", local + availability + " " + broad, local, "abstained"),
            ("advanced", "broad_impact", broad + " Podemos receber pelo caixa central.", broad, "predicted"),
            ("advanced", "broad_impact", broad + " " + loss, broad, "abstained"),
            ("advanced", "broad_impact", "Precisamos reprocessar todos os pagamentos.", "reprocessar todos os pagamentos", "abstained"),
            ("advanced", "broad_impact", "Precisamos reprocessar todos os pagamentos.", "Precisamos reprocessar todos os pagamentos.", "predicted"),
            ("urgent", "immediate_harm", total + no_alternative, total, "predicted"),
            ("urgent", "immediate_harm", total + " Podemos cobrar pelo caixa central.", total, "abstained"),
            ("urgent", "immediate_harm", "Não conseguimos vender nada." + no_alternative, "Não conseguimos vender nada.", "predicted"),
            ("urgent", "immediate_harm", loss, loss, "predicted"),
            ("urgent", "immediate_harm", loss + " Tudo voltou ao normal.", loss, "abstained"),
            ("urgent", "immediate_harm", "Não estamos perdendo vendas agora.", "Não estamos perdendo vendas agora.", "abstained"),
            ("urgent", "immediate_harm", "Em quinze minutos vou perder o lote.", "Em quinze minutos vou perder o lote.", "predicted"),
            ("urgent", "immediate_harm", "Na semana que vem vou perder o lote.", "Na semana que vem vou perder o lote.", "abstained"),
        ]
        for code, criterion, text, quote, expected in scenarios:
            with self.subTest(code=code, text=text):
                self.assert_field(item(text, requested=("priority",)), prediction(code, criterion, quote), status=expected)

    def test_prazo_urgente_exige_consequencia_afirmada_e_pendente(self):
        total = "Nenhuma venda passa."
        deadline = "Se o pagamento não sair, receberei uma multa em quinze minutos."
        alternatives = (
            total + " Não temos outra forma de receber. Mas agora sigo vendendo pelo celular sem atraso.",
            total + " Não há outro terminal. Agora continuamos cobrando por transferência.",
            "Todos os terminais desligaram, mas sigo vendendo pelo celular sem atraso.",
        )
        for text, quote, status in (
            ("Não há multa hoje. Preciso de uma orientação.", "multa hoje", "abstained"),
            ("Consigo pagar a multa hoje com tranquilidade.", "pagar a multa hoje", "abstained"),
            ("Vence o prazo de pagamento hoje.", "Vence o prazo de pagamento hoje.", "abstained"),
            ("Receberei uma multa em quinze minutos.", "Receberei uma multa em quinze minutos.", "predicted"),
            ("Vou receber uma multa hoje.", "Vou receber uma multa hoje.", "predicted"),
            ("Receberei uma multa hoje. A multa já foi cancelada.", "Receberei uma multa hoje.", "abstained"),
            (deadline, "receberei uma multa em quinze minutos", "predicted"),
            (total + " Não temos outra forma de receber.", total, "predicted"),
            (alternatives[0], total, "abstained"),
            (alternatives[1], total, "abstained"),
            (alternatives[2], "Todos os terminais desligaram", "abstained"),
        ):
            with self.subTest(text=text):
                self.assert_field(item(text, requested=("priority",)), prediction("urgent", "immediate_harm", quote),
                                  status=status)

    def test_debito_repetido_em_curso_nunca_libera_rotina(self):
        quote = "Como posso configurar a maquininha?"
        for damage in (
            "Todos os clientes são debitados duas vezes a cada tentativa agora.",
            "O sistema está cobrando em duplicidade neste momento.",
        ):
            with self.subTest(damage=damage):
                entry = item(quote + " " + damage, requested=("priority",))
                values = {"priority": prediction("basic", "routine", quote)}
                envelope, _, _ = self.classify(entry, values)
                decision = decide(entry, envelope["observation"], CATALOG, RUN_ID)
                self.assertEqual(decision["outcome"], "review")
                self.assertIsNone(decision["fields"]["priority"]["applied"])
                self.assert_field(entry, prediction("urgent", "immediate_harm", damage), status="predicted")
        for denied_damage in ("A operação segue sem prejuízo ou cobranças duplicadas.",
                              "Não é verdade que nossos clientes são debitados duas vezes agora."):
            normal = quote + " " + denied_damage
            self.assert_field(item(normal, requested=("priority",)), prediction("basic", "routine", quote),
                              status="predicted")
            self.assert_field(item(normal, requested=("priority",)),
                              prediction("urgent", "immediate_harm", denied_damage), status="abstained")
        past = "O sistema cobrou duas vezes. Agora quero apenas entender o recibo."
        self.assert_field(item(past, requested=("priority",)), prediction("urgent", "immediate_harm", "cobrou duas vezes"),
                          status="abstained")
        repeated = "A cada nova tentativa todos os clientes são debitados duas vezes;"
        text = repeated + " isso continua agora e não temos outra forma de receber."
        self.assert_field(item(text, requested=("priority",)), prediction("urgent", "immediate_harm", repeated),
                          status="predicted")

    def test_urgencia_exige_afirmacao_do_efeito_em_cada_ramo(self):
        cases = (
            ("Serei multado hoje.", True),
            ("Não serei multado hoje.", False),
            ("Hoje não serei multado.", False),
            ("Jamais receberemos uma multa hoje.", False),
            ("Não terei multa hoje.", False),
            ("Quero saber se serei multado hoje.", False),
            ("Serei multado hoje se o envio falhar.", False),
            ("Caso o envio falhe, receberemos uma multa hoje.", False),
            ("Estamos perdendo vendas a cada minuto.", True),
            ("Nunca estamos perdendo vendas a cada minuto.", False),
            ("Estamos perdendo vendas a cada minuto?", False),
            ("Débitos não autorizados continuam.", True),
            ("Nenhuma venda passa. Não temos alternativa.", True),
            ("Não conseguimos vender nada. Não temos alternativa.", True),
            ("Não é verdade que nenhuma venda passa. Não temos alternativa.", False),
            ("Nenhuma venda passa. Será que não temos alternativa?", False),
            ("Hoje não poderemos pagar.", True),
            ("Vou confirmar se hoje não poderemos pagar.", False),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                status = "predicted" if expected else "abstained"
                self.assert_field(item(text, requested=("priority",)),
                                  prediction("urgent", "immediate_harm", text), status=status)

    def test_duvida_ou_negacao_de_debito_nao_afirma_dano(self):
        routine = "Como posso configurar a maquininha?"
        cases = (
            ("Os clientes estão sendo debitados duas vezes agora.", True),
            ("Nenhum cliente está sendo cobrado duas vezes agora.", False),
            ("Nenhuma das vendas foi cobrada em dobro agora.", False),
            ("Como posso confirmar se os clientes estão sendo debitados duas vezes agora?", False),
            ("Quero verificar se os compradores estão sendo cobrados em duplicidade neste momento.", False),
            ("Os clientes estão sendo debitados duas vezes agora?", False),
            ("Se der erro, os clientes são debitados duas vezes a cada tentativa.", False),
            ("Nunca estamos perdendo vendas a cada minuto.", False),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                entry = item(routine + " " + text, requested=("priority",))
                self.assert_field(entry, prediction("urgent", "immediate_harm", text),
                                  status="predicted" if expected else "abstained")
                self.assert_field(entry, prediction("basic", "routine", routine),
                                  status="abstained" if expected else "predicted")
        fault = "Como consultar o Pix que não chegou ao comerciante?"
        self.assert_field(item(fault, requested=("priority",)), prediction("basic", "routine", fault),
                          status="abstained")

    def test_citacao_de_consequencia_negada_nao_herda_outra_perda_afirmada(self):
        loss = "Estamos perdendo vendas a cada minuto"
        denied = "não serei multado hoje"
        text = loss + " e " + denied + "."
        entry = item(text, requested=("priority",))
        self.assert_field(entry, prediction("urgent", "immediate_harm", loss), status="predicted")
        self.assert_field(entry, prediction("urgent", "immediate_harm", denied), status="abstained")

    def test_pergunta_de_orientacao_preserva_dano_afirmado_entre_pontuacoes(self):
        effects = ("Estamos perdendo vendas a cada minuto",
                   "Todos os clientes estão sendo debitados duas vezes agora",
                   "Serei multado hoje")
        questions = ("como posso configurar a maquininha?", "como resolvo isso?")
        for effect in effects:
            alone = item(effect + ".", requested=("priority",))
            self.assert_field(alone, prediction("urgent", "immediate_harm", effect), status="predicted")
            self.assert_field(alone, prediction("basic", "routine", effect), status="abstained")
            for punctuation in (".", ":", ",", ";"):
                for question in questions:
                    with self.subTest(effect=effect, punctuation=punctuation, question=question):
                        entry = item(effect + punctuation + " " + question, requested=("priority",))
                        self.assert_field(entry, prediction("urgent", "immediate_harm", effect), status="predicted")
                        self.assert_field(entry, prediction("basic", "routine", question), status="abstained")

    def test_pergunta_de_orientacao_com_negacao_consulta_e_fronteira_incerta(self):
        routine = "como posso configurar a maquininha?"
        effects = ("Não estamos perdendo vendas a cada minuto",
                   "Nenhuma cliente está sendo debitada duas vezes agora",
                   "Quero confirmar se os clientes estão sendo debitados duas vezes agora",
                   "Se der erro, os clientes são debitados duas vezes a cada tentativa")
        for effect in effects:
            for punctuation in (".", ":", ",", ";"):
                with self.subTest(effect=effect, punctuation=punctuation):
                    entry = item(effect + punctuation + " " + routine, requested=("priority",))
                    self.assert_field(entry, prediction("urgent", "immediate_harm", effect), status="abstained")
                    self.assert_field(entry, prediction("basic", "routine", routine), status="predicted")

        uncertainty = "Estamos perdendo vendas a cada minuto, é essa a situação?"
        entry = item(routine + " " + uncertainty, requested=("priority",))
        self.assert_field(entry, prediction("urgent", "immediate_harm", uncertainty), status="abstained")
        self.assert_field(entry, prediction("basic", "routine", routine), status="abstained")
        effect = "Estamos perdendo vendas a cada minuto"
        unpunctuated = item(effect + " " + routine, requested=("priority",))
        self.assert_field(unpunctuated, prediction("urgent", "immediate_harm", effect), status="abstained")
        self.assert_field(unpunctuated, prediction("basic", "routine", routine), status="abstained")

        normal = item(routine, requested=("priority",))
        self.assert_field(normal, prediction("urgent", "immediate_harm", routine), status="abstained")
        self.assert_field(normal, prediction("basic", "routine", routine), status="predicted")

    def test_familias_localizadas_e_retrabalho_abrangente(self):
        local = "Só uma das três leitoras parou;"
        broad = "As divergências de todos os caixas exigem refazer o fechamento inteiro há dias;"
        for code, criterion, quote, consequence in (
            ("intermediate", "localized_impact", local, " os clientes continuam pagando nas outras duas."),
            ("advanced", "broad_impact", broad, " ainda consigo vender e o prazo termina na próxima semana."),
        ):
            with self.subTest(code=code):
                self.assert_field(item(quote + consequence, requested=("priority",)),
                                  prediction(code, criterion, quote), status="predicted")

    def test_quote_literal_unicode_repeticao_e_aspas(self):
        quote = 'Como posso "enviar um valor" pela chave do destinatário?'
        text = "🧾 O atendimento está aberto. " + quote
        key = "pix", "pix_operation"
        evidence = self.assert_field(item(text), prediction(*key, quote), status="predicted")
        self.assertEqual(evidence["start"], 29)
        self.assertEqual(text[evidence["start"]:evidence["end"]], quote)
        self.assert_field(item(text), prediction(*key, quote.replace("á", "a")),
                          status="abstained", reason="no_literal_span")
        self.assert_field(item(text + " " + quote), prediction(*key, quote),
                          status="abstained", reason="ambiguous_span")
        value = prediction(*key, "enviar um valor")
        self.assert_field(item(text), value, status="abstained", reason="insufficient_relation")

    def test_catalogo_ampliado_e_definicao_alterada(self):
        text = "Como consultar um Pix?"
        entry = item(text, received={"priority": "planejamento"})
        entry["catalog"]["priority"]["planejamento"] = "Orientação para obras"
        entry["catalog"]["category"]["infra"] = "Equipamento de rede"
        self.assert_field(entry, prediction("infra", "terminal_operation", text),
                          status="abstained", reason="unsupported_code")
        envelope, _, _ = self.classify(entry, {"category": prediction("pix", "pix_operation", text)})
        decision = decide(entry, envelope["observation"], entry["catalog"], RUN_ID)
        self.assertEqual(decision["fields"]["priority"], {"status": "provided", "applied": "planejamento"})
        entry["catalog"]["category"]["pix"] = "Repasses por cartão"
        self.assert_field(entry, prediction("pix", "pix_operation", text), status="abstained", reason="unsupported_code")

    def test_saida_malformada_encerra_sessao_antes_da_semantica(self):
        text = "Como consultar um Pix?"
        valid = prediction("pix", "pix_operation", text)
        cases = [
            ({}, "missing_output"),
            ({"category": "pix"}, "invalid_output"),
            ({"category": dict(valid, quote=42)}, "invalid_output"),
            ({"category": dict(valid, quote="")}, "invalid_output"),
            ({"category": dict(valid, quote="a" * 161)}, "invalid_output"),
            ({"category": dict(valid, code="fora-do-catalogo")}, "invalid_output"),
            ({"category": dict(valid, criterion="desconhecido")}, "invalid_output"),
            ({"category": dict(valid, criterion="none")}, "invalid_output"),
            ({"category": dict(ABSTAIN, quote=text)}, "invalid_output"),
            ({"category": {"code": "pix", "quote": text}}, "missing_output"),
            ({"category": dict(valid, explanation="extra")}, "invalid_output"),
            ({"category": valid, "priority": ABSTAIN}, "invalid_output"),
        ]
        for payload, reason in cases:
            with self.subTest(payload=payload):
                envelope, adapter, gateway = self.classify(item(text), payload)
                self.assertEqual(envelope["observation"]["choices"]["category"]["reason"], reason)
                self.assertEqual(envelope["audit"]["raw_content"], encode(payload))
                self.assertEqual(gateway.closed, 1)
                with self.assertRaises(ConnectionError):
                    adapter.classify(item(text))
                self.assertEqual(len(gateway.bodies), 1)

    def test_json_invalido_e_conteudo_truncado(self):
        text = "Como consultar um Pix?"
        payload = {"category": prediction("pix", "pix_operation", text)}
        outputs = (
            response(None, raw='{"category":'),
            response(None, raw='{"category": {}, "category": {}}'),
            response(payload, finish="length"),
        )
        for output in outputs:
            with self.subTest(output=output):
                gateway = Gateway(output)
                envelope, _, _ = self.classify(item(text), None, gateway=gateway)
                self.assertEqual(envelope["observation"]["choices"]["category"]["reason"], "invalid_output")
                self.assertEqual(gateway.closed, 1)
        self.assertEqual(envelope["audit"]["fields"]["category"]["quote"], text)

    def test_criterio_incompativel_e_recusa_preservam_lote(self):
        text = "Como consultar um Pix?"
        entry = item(text)
        envelope, adapter, gateway = self.classify(entry, {"category": prediction("pix", "terminal_operation", text)})
        self.assertEqual(envelope["audit"]["fields"]["category"]["reason"], "criterion_mismatch")
        self.assertEqual(envelope["audit"]["fields"]["category"]["start"], 0)
        self.assertEqual(gateway.closed, 0)
        gateway.output = response(None, refusal="Recusa artificial")
        recused = adapter.classify(dict(entry, id="sintetico-delta"))
        self.assertIsNone(recused["audit"]["raw_content"])
        self.assertEqual(recused["audit"]["refusal"], "Recusa artificial")
        self.assertEqual(recused["audit"]["fields"]["category"]["reason"], "provider_refusal")
        replay_envelope(dict(entry, id="sintetico-delta"), recused)
        gateway.output = response(None, finish="content_filter")
        filtered = adapter.classify(dict(entry, id="sintetico-episilon"))
        self.assertEqual(filtered["observation"]["choices"]["category"]["reason"], "policy")
        gateway.output = response({"category": ABSTAIN})
        explicit = adapter.classify(dict(entry, id="sintetico-zeta"))
        self.assertEqual(explicit["observation"]["choices"]["category"]["reason"], "explicit")
        self.assertEqual((gateway.closed, len(gateway.bodies)), (0, 4))

    def test_veto_projeta_abstencao_e_audita_proposta_do_fornecedor(self):
        text = "Vi o dinheiro no aplicativo do aparelho."
        entry = item(text)
        output = {"category": prediction("payouts", "sales_settlement", text)}
        envelope, _, _ = self.classify(entry, output)
        evidence = envelope["audit"]["fields"]["category"]
        observation = envelope["observation"]
        self.assertEqual(observation["choices"]["category"],
                         {"status": "abstained", "raw": "informacao_insuficiente", "reason": "policy", "score": None})
        self.assertEqual((evidence["value"], evidence["quote"], evidence["reason"]),
                         ("payouts", text, "insufficient_relation"))
        self.assertEqual(decode(envelope["audit"]["raw_content"]), output)
        decision = decide(entry, observation, CATALOG, RUN_ID)
        self.assertEqual(decision["outcome"], "review")
        self.assertEqual(decision["fields"]["priority"], {"status": "provided", "applied": "basic"})

    def test_um_campo_e_dois_em_um_post_sem_aplicacao_parcial(self):
        text = "Como configurar a leitora de cartões?"
        entry = item(text, requested=("category", "priority"))
        choices = {"category": prediction("terminal", "terminal_operation", text),
                   "priority": prediction("urgent", "immediate_harm", text)}
        envelope, _, gateway = self.classify(entry, choices)
        observation = envelope["observation"]
        self.assertEqual((observation["requests"], observation["questions"], len(gateway.bodies)), (1, 2, 1))
        self.assertEqual(observation["choices"]["category"]["raw"], "terminal")
        self.assertEqual(observation["choices"]["priority"]["reason"], "policy")
        decision = decide(entry, observation, CATALOG, RUN_ID)
        self.assertEqual(decision["outcome"], "review")
        self.assertEqual(decision["fields"]["category"], {"status": "predicted", "applied": None})
        self.assertEqual(envelope["audit"]["fields"]["category"]["verdict"], "accepted")
        self.assertEqual(envelope["audit"]["fields"]["priority"]["verdict"], "veto")
        body = decode(gateway.bodies[0][0])
        context = decode(body["messages"][1]["content"])
        self.assertEqual(set(context), {"text", "brand", "catalog", "missing", "received"})
        self.assertEqual(context["missing"], ["category", "priority"])
        self.assertEqual(context["received"], {})
        self.assertNotIn("temperature", body)
        self.assertEqual((body["stream"], body["reasoning_effort"], body["max_completion_tokens"]), (False, "none", 384))
        schema = body["response_format"]["json_schema"]
        self.assertTrue(schema["strict"])
        self.assertEqual(schema["schema"]["required"], ["category", "priority"])
        self.assertEqual(set(schema["schema"]["properties"]["category"]["properties"]), {"code", "criterion", "quote"})
        self.assertEqual(schema["schema"]["properties"]["category"]["properties"]["quote"]["maxLength"], 160)
        one = item(text, received={"priority": "advanced", "category": " "})
        single, _, gateway = self.classify(one, {"category": choices["category"]})
        body = decode(gateway.bodies[0][0])
        self.assertEqual(decode(body["messages"][1]["content"])["received"], {"priority": "advanced"})
        self.assertEqual(body["response_format"]["json_schema"]["schema"]["required"], ["category"])
        decision = decide(one, single["observation"], CATALOG, RUN_ID)
        self.assertEqual(decision["fields"]["priority"], {"status": "provided", "applied": "advanced"})
        self.assertEqual(set(single["audit"]["fields"]), {"category"})

    def test_entrada_completa_invalida_e_mascara_falsa_nao_iniciam_transporte(self):
        for entry in (
            item("Atendimento.", requested=()),
            item("Atendimento.", received={"priority": "inexistente"}),
            item("Atendimento.", received={"priority": "basic", "category": "pix"}),
        ):
            gateway = Gateway({})
            adapter = R5Adapter(identity_for("fixture"), RUN_ID, "Artefato artificial", gateway)
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                adapter.classify(entry)
            adapter.close()
            self.assertEqual((gateway.events, gateway.bodies, gateway.closed), ([], [], 1))

    def test_orcamento_reserva_antes_do_transporte_e_concilia_429(self):
        events = []
        text = "Como consultar um Pix?"
        entry = item(text)
        gateway = Gateway(response(None, model=None, usage={
            "prompt_tokens": 109, "completion_tokens": 4, "cost": "0.000125"
        }), status=429, events=events)
        budget = Budget(events)
        envelope, adapter, _ = self.classify(entry, None, gateway=gateway, budget=budget)
        self.assertEqual(events, ["reserve", "transport", "post", "usage"])
        self.assertEqual(budget.reservations, [(entry["id"], len(gateway.bodies[0][0]))])
        usage, = envelope["observation"]["request_usage"]
        self.assertEqual((usage["input_tokens"], usage["output_tokens"], usage["observed_api_usd"]), (109, 4, 0.000125))
        self.assertEqual(budget.usage, [usage])
        self.assertEqual(envelope["observation"]["choices"]["category"]["reason"], "transport")
        adapter.close()
        self.assertEqual((len(gateway.bodies), gateway.closed), (1, 1))

    def test_falha_antes_do_post_e_reserva_recusada(self):
        for from_budget in (True, False):
            events = []
            gateway = Gateway({}, failure=OSError("sem conexão"), before_send=True, events=events)
            budget = Budget(events, failure=Blocked("sem reserva") if from_budget else None)
            envelope, _, _ = self.classify(item("Como consultar um Pix?"), None, gateway=gateway, budget=budget)
            self.assertEqual(events, ["reserve"] if from_budget else ["reserve", "transport"])
            self.assertEqual(envelope["observation"]["choices"]["category"]["reason"],
                             "adapter_error" if from_budget else "transport")
            self.assertEqual((envelope["observation"]["requests"], gateway.bodies, budget.usage), (0, [], []))

    def test_timeout_apos_post_conserva_custo_desconhecido_e_encerra(self):
        events = []
        gateway = Gateway({}, failure=TimeoutError(), events=events)
        budget = Budget(events)
        envelope, adapter, _ = self.classify(item("Como consultar um Pix?"), None, gateway=gateway, budget=budget)
        self.assertEqual(envelope["observation"]["choices"]["category"]["reason"], "timeout")
        self.assertEqual((envelope["observation"]["requests"], len(budget.reservations), len(budget.usage)), (1, 1, 1))
        self.assertTrue(all(value is None for value in budget.usage[0].values()))
        self.assertEqual(events, ["reserve", "transport", "post", "usage"])
        with self.assertRaises(ConnectionError):
            adapter.classify(item("Como consultar um Pix?"))
        self.assertEqual((len(gateway.bodies), gateway.closed), (1, 1))

    def test_prazo_terminado_ao_conferir_auditoria_preserva_resposta_e_uso(self):
        text = "Como consultar um Pix?"
        events = []
        gateway = Gateway(response({"category": prediction("pix", "pix_operation", text)},
                                   usage={"prompt_tokens": 109, "completion_tokens": 5, "cost": "0.000119"}),
                          events=events)
        budget = Budget(events)
        moments = iter((10.0, 10.0, 10.0, 10.0, 10.96))
        envelope, _, _ = self.classify(item(text), None, gateway=gateway, budget=budget, timeout_ms=1000,
                                       clock=lambda: next(moments))
        explanation = envelope["audit"]["fields"]["category"]
        self.assertEqual((explanation["verdict"], explanation["reason"], explanation["quote"]), ("error", "timeout", text))
        self.assertEqual(budget.usage[0]["observed_api_usd"], 0.000119)
        self.assertEqual(gateway.bodies[0][1], 10.95)
        self.assertEqual((len(gateway.bodies), gateway.closed), (1, 1))

    def test_modelo_ausente_e_divergente_preservam_evidencia_sem_aplicar(self):
        text = "Como consultar um Pix?"
        for model, reason in ((None, "adapter_error"), ("outro/modelo", "version_mismatch")):
            gateway = Gateway(response({"category": prediction("pix", "pix_operation", text)}, model=model))
            envelope, _, _ = self.classify(item(text), None, gateway=gateway)
            observation = envelope["observation"]
            self.assertEqual(observation["returned_model"], model)
            self.assertEqual(observation["choices"]["category"]["reason"], reason)
            self.assertEqual(observation["choices"]["category"]["status"], "error")
            self.assertEqual(envelope["audit"]["fields"]["category"]["quote"], text)
            self.assertEqual(gateway.closed, 1)
        gateway = Gateway({})
        with self.assertRaisesRegex(ValueError, "exige orçamento"):
            R5Adapter(identity_for("real"), RUN_ID, "Artefato artificial", gateway)
        with self.assertRaisesRegex(ValueError, "identidade incompatível"):
            R5Adapter(dict(identity_for("fixture"), policy_version="1.1.0"), RUN_ID, "Artefato artificial", gateway)
        self.assertEqual(gateway.events, [])

    def test_replay_rejeita_adulteracao_de_evidencia_e_escolha(self):
        text = "Como consultar um Pix?"
        entry = item(text)
        source, _, _ = self.classify(entry, {"category": prediction("pix", "pix_operation", text)})
        expected_hash = sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(source["audit"]["input_sha256"], expected_hash)
        for field, value in (
            ("quote", "Qual o prazo de um Pix?"),
            ("start", 1),
            ("criterion", "terminal_operation"),
            ("value", "terminal"),
            ("reason", "context_conflict"),
        ):
            changed = deepcopy(source)
            changed["audit"]["fields"]["category"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                replay_envelope(entry, changed)
        contradicted = deepcopy(source)
        contradicted["observation"]["choices"]["category"]["raw"] = "payouts"
        with self.assertRaisesRegex(ValueError, "incompatível com o replay"):
            replay_envelope(entry, contradicted)
        with self.assertRaises(ValueError):
            replay_envelope(dict(entry, text="Como consultar outro Pix?"), source)
        with self.assertRaises(ValueError):
            replay_envelope(entry, source, policy_sha256="0" * 64)
        off_schema = deepcopy(source)
        off_schema["audit"]["notes"] = "propriedade inesperada"
        with self.assertRaises(ValueError):
            validate_envelope(off_schema)

    def test_replay_rejeita_resposta_de_fornecedor_sem_despacho(self):
        text = "Como consultar um Pix?"
        entry = item(text)
        source, _, _ = self.classify(entry, {"category": prediction("pix", "pix_operation", text)})
        pre_dispatch, _, _ = self.classify(entry, None, gateway=Gateway({}, failure=TimeoutError(), before_send=True))
        self.assertEqual(pre_dispatch["observation"]["requests"], 0)
        self.assertEqual(pre_dispatch["observation"]["choices"]["category"]["reason"], "timeout")
        self.assertIsNone(pre_dispatch["audit"]["raw_content"])
        # Uma adulteração pode remontar as escolhas e a auditoria sem mudar o
        # vínculo impossível entre requests e os metadados do provedor.
        content = source["audit"]["raw_content"]
        for raw, finish, refusal in ((content, None, None), (None, "stop", None), (None, None, "recusa")):
            with self.subTest(raw=raw, finish=finish, refusal=refusal):
                changed = deepcopy(pre_dispatch)
                changed["audit"] = build_audit(entry, raw, finish, refusal=refusal, error="timeout")
                changed["observation"]["choices"] = project_choices(changed["audit"])
                with self.assertRaises(ValueError):
                    replay_envelope(entry, changed)
        for key in ("returned_model", "weights_revision"):
            with self.subTest(key=key):
                changed = deepcopy(pre_dispatch)
                changed["observation"][key] = MODEL
                with self.assertRaises(ValueError):
                    replay_envelope(entry, changed)


if __name__ == "__main__":
    unittest.main()
