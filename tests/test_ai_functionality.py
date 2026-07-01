"""
AI Functionality Tests for KCompareAgent

Integration tests that exercise src.AICorrector exactly like the real
application does: every real GGUF model found under models/ (discovered via
modelSelector.list_available_models, the same function AIPanel uses to
populate its model dropdown) is loaded via load_model() and driven through
real inference via AICorrection() - nothing about llama_cpp is mocked.
"""

import os
import sys
import unittest

# Add the project root to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import AICorrector
from src.modelSelector import list_available_models
from llama_cpp import Llama


class TestAIFunctionality(unittest.TestCase):
    """Test cases specifically for AI correction functionality"""

    @classmethod
    def setUpClass(cls):
        """Discover every real model under models/ the same way AIPanel does"""
        cls.available_models = list_available_models(AICorrector.MODELS_DIR)
        if not cls.available_models:
            raise unittest.SkipTest(
                f"Nessun modello .gguf trovato in {AICorrector.MODELS_DIR} "
                "(i file .gguf non sono versionati in git)"
            )

    def test_ai_corrector_exists(self):
        """Test that the AICorrector module exposes its expected public API"""
        self.assertTrue(hasattr(AICorrector, "load_model"))
        self.assertTrue(hasattr(AICorrector, "AICorrection"))
        self.assertTrue(hasattr(AICorrector, "get_current_model_path"))

    def test_load_model_sets_real_llama_instance(self):
        """load_model should leave a real, usable Llama instance loaded, for every model in models/"""
        for model in self.available_models:
            with self.subTest(model=model["filename"]):
                AICorrector.load_model(model["path"])
                self.assertIsInstance(AICorrector.llm, Llama)
                self.assertEqual(AICorrector.get_current_model_path(), model["path"])

    def test_ai_correction_method_exists(self):
        """Test that AICorrection raises a clear error when no model is loaded"""
        original_llm = AICorrector.llm
        try:
            AICorrector.llm = None
            with self.assertRaises(RuntimeError):
                AICorrector.AICorrection("auto text", "human comment")
        finally:
            AICorrector.llm = original_llm

    def test_ai_correction_with_sample_text(self):
        """Test correction with sample text input, running real inference on every model in models/"""
        for model in self.available_models:
            with self.subTest(model=model["filename"]):
                AICorrector.load_model(model["path"])
                result = AICorrector.AICorrection(
                    "- Aggiunta variabile VarTest\n- Rimossa variabile VarOld",
                    "aggiunta variabile di test e rimossa quella vecchia"
                )
                self.assertIsInstance(result, str)
                self.assertTrue(result.strip())
                self.assertNotIn("<think>", result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
