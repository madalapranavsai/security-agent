"""Runtime configuration for the DeepAgents MCP orchestrator."""

from __future__ import annotations

import json
import logging
import os
import shlex
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


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


def _parse_positive_int(raw_value: str | None, *, default: int) -> int:
    """Parse a positive integer environment variable with a default."""
    if raw_value is None or not raw_value.strip():
        return default

    value = int(raw_value)
    if value <= 0:
        raise ValueError("MAX_TOOLS must be greater than zero.")
    return value


MODEL: str = os.getenv("MODEL", "anthropic:claude-sonnet-4-6")
MCP_SERVER_NAME: str = os.getenv("MCP_SERVER_NAME", "default")
MCP_COMMAND: str = os.getenv("MCP_COMMAND", "")
MCP_ARGS: list[str] = _parse_mcp_args(os.getenv("MCP_ARGS", ""))
MAX_TOOLS: int = _parse_positive_int(os.getenv("MAX_TOOLS"), default=50)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated application settings loaded from the process environment."""

    model: str
    mcp_server_name: str
    mcp_command: str
    mcp_args: list[str]
    max_tools: int
    log_level: str


def get_settings() -> Settings:
    """Return validated runtime settings."""
    if not MCP_COMMAND:
        raise RuntimeError("MCP_COMMAND is required. Set it in the environment or .env file.")

    return Settings(
        model=MODEL,
        mcp_server_name=MCP_SERVER_NAME,
        mcp_command=MCP_COMMAND,
        mcp_args=MCP_ARGS,
        max_tools=MAX_TOOLS,
        log_level=LOG_LEVEL,
    )


def configure_logging(level: str = LOG_LEVEL) -> None:
    """Configure process logging once for CLI execution."""
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
