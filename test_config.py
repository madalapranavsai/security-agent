from __future__ import annotations

import importlib
import os
import sys
import unittest
from unittest.mock import patch

sys.modules.pop("config", None)
config = importlib.import_module("config")


class ConfigTests(unittest.TestCase):
    def test_get_settings_parses_runtime_environment(self) -> None:
        env = {
            "MCP_COMMAND": "python3",
            "MCP_ARGS": '["server.py", "--port", "8000"]',
            "MAX_TOOLS": "25",
            "SUBAGENT_COUNT": "10",
            "LOG_LEVEL": "debug",
        }

        with patch.dict(os.environ, env, clear=True):
            settings = config.get_settings()

        self.assertEqual(settings.mcp_command, "python3")
        self.assertEqual(settings.mcp_args, ["server.py", "--port", "8000"])
        self.assertEqual(settings.max_tools, 25)
        self.assertEqual(settings.subagent_count, 10)
        self.assertEqual(settings.log_level, "DEBUG")

    def test_get_settings_rejects_invalid_subagent_count(self) -> None:
        env = {
            "MCP_COMMAND": "python3",
            "SUBAGENT_COUNT": "0",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "SUBAGENT_COUNT"):
                config.get_settings()


if __name__ == "__main__":
    unittest.main()
