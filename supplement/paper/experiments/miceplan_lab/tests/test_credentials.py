from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from miceplan_lab.credentials import resolve_api_key


class CredentialTests(unittest.TestCase):
    def test_environment_key_takes_precedence_without_keychain_lookup(self) -> None:
        with patch.dict(os.environ, {"MICEPLAN_TEST_API_KEY": "environment-secret"}, clear=False):
            with patch("miceplan_lab.credentials.subprocess.run") as run:
                self.assertEqual(
                    resolve_api_key(
                        "MICEPLAN_TEST_API_KEY",
                        keychain_service="MICEPLAN_TEST_API_KEY",
                    ),
                    "environment-secret",
                )
                run.assert_not_called()

    def test_keychain_secret_is_returned_without_logging(self) -> None:
        completed = type(
            "Completed",
            (),
            {"returncode": 0, "stdout": "keychain-secret\n", "stderr": ""},
        )()
        with patch.dict(os.environ, {}, clear=True):
            with patch("miceplan_lab.credentials.subprocess.run", return_value=completed) as run:
                self.assertEqual(
                    resolve_api_key(
                        "MICEPLAN_TEST_API_KEY",
                        keychain_service="MICEPLAN_TEST_API_KEY",
                    ),
                    "keychain-secret",
                )
                self.assertNotIn("keychain-secret", repr(run.call_args))

    def test_missing_credential_raises_without_secret_material(self) -> None:
        completed = type("Completed", (), {"returncode": 44, "stdout": "", "stderr": "missing"})()
        with patch.dict(os.environ, {}, clear=True):
            with patch("miceplan_lab.credentials.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(RuntimeError, "Missing API credential"):
                    resolve_api_key(
                        "MICEPLAN_TEST_API_KEY",
                        keychain_service="MICEPLAN_TEST_API_KEY",
                    )


if __name__ == "__main__":
    unittest.main()
