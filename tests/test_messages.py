# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
"""Verify stable error codes and localization without accessing hardware."""
import ast
import os
from pathlib import Path
import runpy
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import messages


class MessageTests(unittest.TestCase):
    def test_catalog_has_all_four_nonempty_translations(self):
        for code, values in messages.MESSAGES.items():
            with self.subTest(code=code):
                self.assertEqual(len(values), 4)
                self.assertTrue(all(isinstance(value, str) and value for value in values))
                for language, expected in zip(('en', 'pl', 'de', 'cs'), values):
                    self.assertEqual(messages.message(code, language), expected)

    def test_locale_normalization_and_precedence(self):
        for value, expected in [('pl_PL.UTF-8', 'pl'), ('de-DE', 'de'), ('cs_CZ', 'cs'),
                                ('en_US', 'en'), ('unknown', 'en'), ('', 'en')]:
            self.assertEqual(messages.normalize_language(value), expected)
        with patch.dict(os.environ, {'DAVEKVM_LANG': 'cs', 'LANG': 'pl_PL.UTF-8'}):
            self.assertEqual(messages.configured_language(), 'cs')
        self.assertEqual(messages.message('MISSING', 'pl'), 'Nieoczekiwany błąd')

    def test_every_keyboard_error_code_is_known_to_python_and_panel(self):
        javascript = (ROOT / 'i18n.js').read_text(encoding='utf-8')
        found = set()
        for name in ('keyboard.py', 'server.py'):
            tree = ast.parse((ROOT / name).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == 'KeyboardError' and node.args
                        and isinstance(node.args[0], ast.Constant)):
                    found.add(node.args[0].value)
        self.assertTrue(found)
        for code in found:
            with self.subTest(code=code):
                self.assertIn(code, messages.MESSAGES)
                self.assertIn(code + ':', javascript)

    def test_cli_validation_retains_a_stable_code_across_languages(self):
        control = runpy.run_path(str(ROOT / 'davekvm-control'), run_name='davekvm_test')
        for language in ('en', 'pl', 'de', 'cs'):
            with self.subTest(language=language), patch.dict(os.environ, {'DAVEKVM_LANG': language}):
                with self.assertRaises(messages.UserError) as caught:
                    control['execute'](None, {'action': 'type', 'text': '\u2603'})
                self.assertEqual(caught.exception.code, 'UNSUPPORTED_TEXT')
                self.assertEqual(str(caught.exception), messages.message('UNSUPPORTED_TEXT', language))

    def test_missing_password_is_localized_without_traceback(self):
        for language in ('en', 'pl', 'de', 'cs'):
            env = dict(os.environ, DAVEKVM_LANG=language, DAVEKVM_PASSWORD_FILE='/nonexistent-davekvm-test-password')
            result = subprocess.run([sys.executable, str(ROOT / 'davekvm-control')], env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1)
            self.assertIn(messages.message('PASSWORD_FILE_ERROR', language), result.stderr)
            self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
