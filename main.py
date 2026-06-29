"""CLI entrypoint for the Dynamic DeepAgents + MCP orchestrator."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Any, Sequence

from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    SubAgent,
    create_deep_agent,
    register_harness_profile,
)
from langchain_core.tools import BaseTool
from langchain_quickjs import CodeInterpreterMiddleware

from config import Settings, configure_logging, get_settings
from mcp.connect import MCPToolLoader
from prompts import SUPERVISOR_PROMPT, WORKER_PROMPT

logger = logging.getLogger(__name__)


def _disable_default_subagent(model: str) -> None:
    """Ensure DeepAgents registers only the configured worker subagent."""
    register_harness_profile(
        model,
        HarnessProfile(general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False)),
    )


def build_agent(settings: Settings, tools: Sequence[BaseTool]) -> Any:
    """Create the DeepAgent with QuickJS workflow execution and one worker."""
    _disable_default_subagent(settings.model)

    worker: SubAgent = {
        "name": "worker",
        "description": "Generic task execution agent.",
        "system_prompt": WORKER_PROMPT,
        "tools": list(tools),
    }
    logger.info("Registering worker subagent with %s shared MCP tools.", len(tools))

    return create_deep_agent(
        model=settings.model,
        tools=list(tools),
        system_prompt=SUPERVISOR_PROMPT,
        middleware=[CodeInterpreterMiddleware()],
        subagents=[worker],
        name="dynamic-deepagents-mcp-orchestrator",
    )


def _content_to_text(content: Any) -> str:
    """Convert LangChain message content into printable text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return str(content)


def format_final_result(result: Any) -> str:
    """Extract the final assistant message from an agent result."""
    if isinstance(result, dict):
        messages = result.get("messages")
        if isinstance(messages, list) and messages:
            final_message = messages[-1]
            if isinstance(final_message, dict):
                return _content_to_text(final_message.get("content"))
            return _content_to_text(getattr(final_message, "content", final_message))
    return str(result)


async def run_agent(user_request: str, settings: Settings) -> str:
    """Load MCP tools, run the agent, and return the final response text."""
    loader = MCPToolLoader(
        command=settings.mcp_command,
        args=settings.mcp_args,
        max_tools=settings.max_tools,
        server_name=settings.mcp_server_name,
    )

    try:
        _, tools = await loader.connect()
        logger.info("Creating DeepAgent with %s MCP tools.", len(tools))
        agent = build_agent(settings, tools)
        result = await agent.ainvoke({"messages": [{"role": "user", "content": user_request}]})
        return format_final_result(result)
    finally:
        await loader.aclose()


def _parse_user_request(argv: Sequence[str]) -> str:
    parser = argparse.ArgumentParser(description="Run a Dynamic DeepAgents + MCP workflow.")
    parser.add_argument("request", nargs="*", help="User request. If omitted, stdin is read.")
    args = parser.parse_args(argv)

    request = " ".join(args.request).strip()
    if request:
        return request

    if not sys.stdin.isatty():
        request = sys.stdin.read().strip()
        if request:
            return request

    parser.error("provide a request argument or pipe one on stdin.")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestrator CLI."""
    configure_logging()
    try:
        settings = get_settings()
        user_request = _parse_user_request(sys.argv[1:] if argv is None else argv)
        final_text = asyncio.run(run_agent(user_request, settings))
    except KeyboardInterrupt:
        logger.warning("Interrupted.")
        return 130
    except Exception:
        logger.exception("Agent execution failed.")
        return 1

    print(final_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
