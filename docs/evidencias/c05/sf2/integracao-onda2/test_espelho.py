"""Controles de recusa para o espelho de QA. Todos os arquivos da prova são temporários."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verificar as qa


class MirrorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(temp.cleanup)
        self.area = Path(temp.name)
        self.checkout = self.area/"checkout"
        self.fixture = self.area/"fixture"
        self.output = self.area/"output"
        self.source = self.checkout/"sources/member.txt"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("fonte de controle")
        self.marker = self.area/"marcador.txt"
        self.marker.write_text("controle")
        init = self.checkout/qa.SF2/"evaluation/__init__.py"
        init.parent.mkdir(parents=True)
        init.touch()
        self.enterContext(patch.object(qa, "EVALUATION_INIT_SHA256", qa.sha256(init)))
        self.schema = self.checkout/"schema.json"
        self.schema.write_text("{}")
        self.protocol = self.checkout/"protocol.json"
        self.protocol.write_text('{"sources":{}}')
        pkg = self.fixture/"package"
        pkg.mkdir(parents=True)
        roles = ["arguments", "training_freeze"]
        for field in qa.FIELDS:
            roles.extend(f"{field}.{role}" for role in ("manifest", *qa.package.COMPONENTS))
        manifest = {"files": dict.fromkeys(roles, "0"*64)}
        self.manifest = pkg/"manifest.json"
        self.manifest.write_text(json.dumps(manifest))
        model = qa.package.package_paths(pkg, manifest)
        for path in model.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

        generated = dict(train="train.jsonl", validation="validation.jsonl", annotations="annotations-public.jsonl",
                         review_receipt="review_receipt.json", token_lengths="token_lengths.json", training_code="code.json",
                         arguments="arguments.json", public_manifest="public.json", final_seal="seal.json")
        training = {k: self.fixture/v for k, v in generated.items()}
        for path in training.values():
            path.touch()
        training.update(protocol=self.protocol, contracts=self.schema)
        self.config = self.fixture/"config.json"
        self.cfg = qa.fixture_config(self.fixture, training, model)
        self.config.write_text(json.dumps(self.cfg))
        for k in ("adapter", "versions", "costs", "capture_policy", "capture_command", "final_command"):
            Path(self.cfg[k]).touch()
        self.index = self.fixture/"adapter-code.json"
        self.index.write_text(json.dumps({"files": {"sources/member.txt": qa.sha256(self.source)}}))
        self.historical = dict(package=qa.sha256(self.manifest), adapter=qa.sha256(self.index),
                               protocol=qa.sha256(self.protocol))
        self.enterContext(patch.object(qa, "ROOT", self.checkout))
        self.enterContext(patch.object(qa.workflow, "sources", return_value={"protocol": self.protocol, "schema": self.schema}))

    def assert_refused(self, reason):
        with patch.object(qa.shutil, "copyfile") as copy:
            with self.assertRaisesRegex(ValueError, reason):
                qa.prepare_mirror(self.output, self.config, self.historical)
            copy.assert_not_called()
        self.assertEqual(self.marker.read_text(), "controle")

    def test_indice_trocado(self):
        self.index.write_bytes(self.index.read_bytes() + b" ")
        self.assert_refused("SHA-256 não confere para adapter-code.json")

    def test_configuracao_com_caminho_trocado(self):
        self.config.write_text(json.dumps({**self.cfg, "versions": str(self.marker)}))
        self.assert_refused("configuração fora dos papéis e caminhos")

    def test_captura_com_argv_divergente(self):
        self.historical["argv"] = "a"*64
        reference = {**self.historical, "argv": "b"*64}
        with patch.object(qa.workflow, "capture_receipt", return_value=reference):
            self.assert_refused("entradas da coleta divergentes do histórico.*argv")

    def test_componente_de_subida_em_indice_de_controle(self):
        self.index.write_text(json.dumps({"files": {"sources/../schema.json": qa.sha256(self.schema)}}))
        self.historical["adapter"] = qa.sha256(self.index)
        self.assert_refused("caminho relativo não canônico")

    def test_origem_com_link_externo(self):
        self.source.unlink()
        self.source.symlink_to(self.marker)
        self.assert_refused("caminho redirecionado")

    def test_destino_resolve_fora_do_espelho(self):
        mirror = self.output/"mirror"
        mirror.mkdir(parents=True)
        (mirror/"sources").symlink_to(self.area, target_is_directory=True)
        self.assert_refused("caminho redirecionado")
        self.assertFalse((self.area/"member.txt").exists())


if __name__ == "__main__":
    unittest.main()
