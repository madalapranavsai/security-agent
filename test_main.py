from __future__ import annotations

import importlib
import io
import sys
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


def _install_import_stubs() -> None:
    deepagents = types.ModuleType("deepagents")
    deepagents.GeneralPurposeSubagentProfile = lambda **_: object()
    deepagents.HarnessProfile = lambda **_: object()
    deepagents.SubAgent = dict
    deepagents.create_deep_agent = lambda **_: object()
    deepagents.register_harness_profile = lambda *_: None
    sys.modules["deepagents"] = deepagents

    langchain_core = types.ModuleType("langchain_core")
    langchain_core_tools = types.ModuleType("langchain_core.tools")
    langchain_core_tools.BaseTool = object
    sys.modules["langchain_core"] = langchain_core
    sys.modules["langchain_core.tools"] = langchain_core_tools

    langchain = types.ModuleType("langchain")
    langchain_chat_models = types.ModuleType("langchain.chat_models")
    langchain_chat_models.init_chat_model = lambda **_: object()
    sys.modules["langchain"] = langchain
    sys.modules["langchain.chat_models"] = langchain_chat_models

    langchain_quickjs = types.ModuleType("langchain_quickjs")
    langchain_quickjs.CodeInterpreterMiddleware = lambda: object()
    sys.modules["langchain_quickjs"] = langchain_quickjs

    config = types.ModuleType("config")
    config.Settings = object
    config.configure_logging = lambda: None
    config.get_settings = lambda: object()
    sys.modules["config"] = config

    mcp = types.ModuleType("mcp")
    mcp_connect = types.ModuleType("mcp.connect")
    mcp_connect.MCPToolLoader = object
    sys.modules["mcp"] = mcp
    sys.modules["mcp.connect"] = mcp_connect

    prompts = types.ModuleType("prompts")
    prompts.build_supervisor_prompt = lambda worker_names: f"supervisor:{','.join(worker_names)}"
    prompts.WORKER_PROMPT = "worker"
    sys.modules["prompts"] = prompts


_install_import_stubs()
main = importlib.import_module("main")


class MainCliTests(unittest.TestCase):
    def test_build_worker_subagents_creates_configured_pool(self) -> None:
        workers = main.build_worker_subagents(10, ["tool"])

        self.assertEqual(len(workers), 10)
        self.assertEqual(workers[0]["name"], "worker_01")
        self.assertEqual(workers[-1]["name"], "worker_10")
        self.assertTrue(all(worker["tools"] == ["tool"] for worker in workers))

    def test_parse_user_request_from_args(self) -> None:
        self.assertEqual(
            main._parse_user_request(["run", "security", "assessment"]),
            "run security assessment",
        )

    def test_parse_user_request_from_stdin(self) -> None:
        with patch.object(main.sys, "stdin", io.StringIO("scan example.com\n")):
            self.assertEqual(main._parse_user_request([]), "scan example.com")

    def test_main_runs_agent_with_cli_request(self) -> None:
        seen: dict[str, str] = {}

        async def fake_run_agent(user_request: str, settings: object) -> str:
            seen["request"] = user_request
            return "done"

        with patch.object(main, "configure_logging", lambda: None), patch.object(
            main, "get_settings", lambda: object()
        ), patch.object(main, "run_agent", fake_run_agent):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main.main(["scan", "example.com"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(seen["request"], "scan example.com")
        self.assertEqual(stdout.getvalue(), "done\n")
        self.assertNotIn("axiomio.com", seen["request"])


if __name__ == "__main__":
    unittest.main()
