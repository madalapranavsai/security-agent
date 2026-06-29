"""Project MCP integration package.

The official MCP Python SDK is also named ``mcp``. This project keeps the
requested local ``mcp/`` package and extends its module search path so
``langchain-mcp-adapters`` can still resolve SDK imports such as
``from mcp import ClientSession``.
"""

from __future__ import annotations

import sys
from importlib.machinery import PathFinder
from pathlib import Path

_LOCAL_PACKAGE_DIR = Path(__file__).resolve().parent
_LOCAL_PARENT_DIR = _LOCAL_PACKAGE_DIR.parent


def _external_sdk_paths() -> list[str]:
    paths: list[str] = []
    for entry in sys.path:
        candidate = Path(entry or ".").resolve()
        if candidate == _LOCAL_PARENT_DIR or candidate == _LOCAL_PACKAGE_DIR:
            continue

        spec = PathFinder.find_spec(__name__, [str(candidate)])
        locations = spec.submodule_search_locations if spec and spec.submodule_search_locations else []
        for location in locations:
            resolved = Path(location).resolve()
            if resolved != _LOCAL_PACKAGE_DIR and str(resolved) not in paths:
                paths.append(str(resolved))
    return paths


for _sdk_path in _external_sdk_paths():
    if _sdk_path not in __path__:
        __path__.append(_sdk_path)

try:
    from .client.session import ClientSession
    from .client.stdio import StdioServerParameters
except ImportError:
    __all__: list[str] = []
else:
    __all__ = ["ClientSession", "StdioServerParameters"]
