"""Asynchronous MCP tool loading for the DeepAgents orchestrator."""

from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING

try:
    from langchain_core.tools import BaseTool
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_mcp_adapters.tools import load_mcp_tools
except ImportError as exc:
    raise RuntimeError(
        "Missing MCP dependencies. Install them with `pip install -r requirements.txt`."
    ) from exc

if TYPE_CHECKING:
    from collections.abc import Sequence

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class MCPToolLoader:
    """Connect to one MCP server and expose a bounded set of LangChain tools."""

    def __init__(
        self,
        *,
        command: str,
        args: Sequence[str],
        max_tools: int,
        server_name: str = "default",
    ) -> None:
        if not command:
            raise ValueError("command is required.")
        if max_tools <= 0:
            raise ValueError("max_tools must be greater than zero.")

        self.command = command
        self.args = list(args)
        self.max_tools = max_tools
        self.server_name = server_name
        self._client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] = []
        self._exit_stack: AsyncExitStack | None = None

    async def connect(self) -> tuple[MultiServerMCPClient, list[BaseTool]]:
        """Open the MCP session and return the connected client plus filtered tools."""

        if self._client is not None:
            return self._client, list(self._tools)

        logger.info("Connecting to MCP server '%s'...", self.server_name)
        logger.info("Command : %s", self.command)
        logger.info("Args    : %s", self.args)

        client = MultiServerMCPClient(
            {
                self.server_name: {
                    "transport": "stdio",
                    "command": self.command,
                    "args": self.args,
                }
            }
        )

        exit_stack = AsyncExitStack()

        try:
            session = await exit_stack.enter_async_context(
                client.session(self.server_name)
            )

            logger.info("Connected successfully.")

            all_tools = await load_mcp_tools(
                session=session,
                server_name=self.server_name,
            )

            filtered_tools = list(all_tools[: self.max_tools])

            logger.info(
                "Registering %d/%d tools.",
                len(filtered_tools),
                len(all_tools),
            )
            logger.debug(
                "Available MCP tools: %s",
                ", ".join(tool.name for tool in all_tools),
            )

        except Exception as e:
            await exit_stack.aclose()
            logger.exception("Failed to connect to MCP server.")
            raise e

        self._client = client
        self._tools = filtered_tools
        self._exit_stack = exit_stack

        return client, list(filtered_tools)

    async def aclose(self) -> None:
        """Close the MCP session and release the server process."""

        if self._exit_stack is not None:
            await self._exit_stack.aclose()
            logger.info("Closed MCP server connection '%s'.", self.server_name)

        self._exit_stack = None
        self._client = None
        self._tools = []
