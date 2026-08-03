"""Runtime configuration for the DeepAgents MCP orchestrator."""

from __future__ import annotations

import json
import logging
import os
import shlex
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_MODEL = "anthropic:claude-sonnet-4-6"
DEFAULT_MCP_SERVER_NAME = "default"
DEFAULT_MAX_TOOLS = 50
DEFAULT_SUBAGENT_COUNT = 10
DEFAULT_LOG_LEVEL = "INFO"


def _parse_mcp_args(raw_args: str) -> list[str]:
    """Parse MCP_ARGS as either a JSON string array or shell-style arguments."""
    if not raw_args.strip():
        return []

    stripped = raw_args.strip()
    if stripped.startswith("["):
        parsed = json.loads(stripped)
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise ValueError("MCP_ARGS JSON must be a list of strings.")
        return parsed

    return shlex.split(stripped)


def _parse_positive_int(raw_value: str | None, *, default: int, name: str) -> int:
    """Parse a positive integer environment variable with a default."""
    if raw_value is None or not raw_value.strip():
        return default

    value = int(raw_value)
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated application settings loaded from the process environment."""

    model: str
    mcp_server_name: str
    mcp_command: str
    mcp_args: list[str]
    max_tools: int
    subagent_count: int
    log_level: str


def get_settings() -> Settings:
    """Return validated runtime settings."""
    load_dotenv()

    mcp_command = os.getenv("MCP_COMMAND", "")
    if not mcp_command:
        raise RuntimeError("MCP_COMMAND is required. Set it in the environment or .env file.")

    return Settings(
        model=os.getenv("MODEL", DEFAULT_MODEL),
        mcp_server_name=os.getenv("MCP_SERVER_NAME", DEFAULT_MCP_SERVER_NAME),
        mcp_command=mcp_command,
        mcp_args=_parse_mcp_args(os.getenv("MCP_ARGS", "")),
        max_tools=_parse_positive_int(
            os.getenv("MAX_TOOLS"),
            default=DEFAULT_MAX_TOOLS,
            name="MAX_TOOLS",
        ),
        subagent_count=_parse_positive_int(
            os.getenv("SUBAGENT_COUNT"),
            default=DEFAULT_SUBAGENT_COUNT,
            name="SUBAGENT_COUNT",
        ),
        log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
    )


def configure_logging(level: str | None = None) -> None:
    """Configure process logging once for CLI execution."""
    if level is None:
        load_dotenv()
        level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()

    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
