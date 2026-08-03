from __future__ import annotations

import importlib
import sys
import unittest

sys.modules.pop("prompts", None)
prompts = importlib.import_module("prompts")


class PromptTests(unittest.TestCase):
    def test_supervisor_prompt_uses_dynamic_subagent_api(self) -> None:
        prompt = prompts.build_supervisor_prompt(["worker_01", "worker_02"])

        self.assertIn("subagentType", prompt)
        self.assertNotIn("subagent_type", prompt)
        self.assertIn("Promise.all", prompt)


if __name__ == "__main__":
    unittest.main()
