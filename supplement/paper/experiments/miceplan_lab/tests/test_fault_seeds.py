from __future__ import annotations

import unittest

from miceplan_lab.generate_fault_seeds import audit, generate


class FaultSeedTests(unittest.TestCase):
    def test_generated_seeds_are_deterministic_isolated_and_intent_preserving(self) -> None:
        first = generate()
        second = generate()
        self.assertEqual(first, second)
        self.assertTrue(first)
        counts = audit(first)
        self.assertGreater(counts["development"]["total"], 0)
        self.assertGreater(counts["test"]["total"], 0)
        self.assertTrue(all(row["intent_signature_preserved"] for row in first))


if __name__ == "__main__":
    unittest.main()
