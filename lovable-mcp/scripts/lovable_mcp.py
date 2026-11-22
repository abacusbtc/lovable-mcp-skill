#!/usr/bin/env python3
"""Standalone driver for the Lovable MCP server (https://mcp.lovable.dev).

Uses the OAuth tokens Hermes stores at $HERMES_HOME/mcp-tokens/lovable.json
(completed via `hermes mcp login lovable`). Works without restarting Hermes —
useful before MCP tools are loaded into a session, or from scripts/cron.

Run with the Hermes venv python (it has the `mcp` package). Its location depends
on the install: ~/.hermes/hermes-agent/venv (default installer) or
/usr/local/lib/hermes-agent/venv (system-wide install).
    ~/.hermes/hermes-agent/venv/bin/python lovable_mcp.py tools
    ~/.hermes/hermes-agent/venv/bin/python lovable_mcp.py call list_workspaces
    ~/.hermes/hermes-agent/venv/bin/python lovable_mcp.py call create_project \
        --data '{"initial_message": "Build a todo app", "wait": true}'

If a call returns 401 Unauthorized, the access token expired: re-run
`hermes mcp login lovable` (this script does not refresh tokens).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

SERVER_URL = "https://mcp.lovable.dev"
DEFAULT_SERVER_NAME = "lovable"


def token_path(server: str) -> Path:
    home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    return home / "mcp-tokens" / f"{server}.json"


def load_token(server: str) -> str:
    path = token_path(server)
    if not path.exists():
        sys.exit(
            f"No token file at {path}\n"
            f"Run `hermes mcp login {server}` first (see SKILL.md)."
        )
    data = json.loads(path.read_text())
    tok = data.get("access_token")
    if not tok:
        sys.exit(f"No access_token inside {path}")
    exp = data.get("expires_at")
    if exp and exp < time.time():
        print(
            f"WARNING: token expired {int(time.time() - exp)}s ago — "
            f"re-run `hermes mcp login {server}`.", file=sys.stderr)
    return tok


async def open_session(server: str):
    """Yield (context, session, http_client) using Hermes' stored token."""
    tok = load_token(server)
    headers = {"Authorization": f"Bearer {tok}"}
    try:  # streamable_http_client exists in late mcp 1.x (e.g. 1.30, yields 3-tuple) and 2.x
        from mcp.client.streamable_http import (
            create_mcp_http_client,
            streamable_http_client as http_client_ctx,
        )
        http_client = create_mcp_http_client(headers=headers, timeout=None)
        ctx = http_client_ctx(SERVER_URL, http_client=http_client)
        read, write, *_ = await ctx.__aenter__()
    except ImportError:  # mcp 1.x
        from mcp.client.streamable_http import streamablehttp_client
        http_client = None
        ctx = streamablehttp_client(SERVER_URL, headers=headers, timeout=60)
        read, write, _ = await ctx.__aenter__()

    from mcp import ClientSession
    session = ClientSession(read, write)
    await session.__aenter__()
    await session.initialize()
    return ctx, session, http_client


def result_to_text(result) -> str:
    parts = []
    for c in getattr(result, "content", []) or []:
        if hasattr(c, "text"):
            parts.append(c.text)
        else:
            parts.append(str(c))
    text = "\n".join(parts)
    if getattr(result, "isError", False):
        text = f"[tool error]\n{text}"
    return text


def maybe_json(text: str):
    """Pretty-print if the server returned a JSON document."""
    stripped = text.strip()
    if stripped.startswith(("{", "[")):
        try:
            return json.dumps(json.loads(stripped), indent=2)
        except json.JSONDecodeError:
            pass
    return text


async def cmd_tools(server: str) -> None:
    ctx, session, http_client = await open_session(server)
    try:
        tools = await session.list_tools()
        print(f"{len(tools.tools)} tools:")
        for t in tools.tools:
            desc = (t.description or "").strip().splitlines()[0]
            print(f"  {t.name:32s} {desc[:90]}")
    finally:
        await session.__aexit__(None, None, None)
        await ctx.__aexit__(None, None, None)
        if http_client:
            await http_client.aclose()


async def cmd_call(server: str, tool: str, data: dict | None) -> None:
    ctx, session, http_client = await open_session(server)
    try:
        result = await session.call_tool(tool, data or {})
        print(maybe_json(result_to_text(result)))
    finally:
        await session.__aexit__(None, None, None)
        await ctx.__aexit__(None, None, None)
        if http_client:
            await http_client.aclose()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--server", default=DEFAULT_SERVER_NAME,
                    help="Hermes MCP token name (default: lovable)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tools", help="list available tools")
    call = sub.add_parser("call", help="call a tool by name")
    call.add_argument("tool")
    call.add_argument("--data", default=None,
                      help="arguments as a JSON object string")
    args = ap.parse_args()

    data = json.loads(args.data) if getattr(args, "data", None) else None
    import asyncio
    if args.cmd == "tools":
        asyncio.run(cmd_tools(args.server))
    else:
        asyncio.run(cmd_call(args.server, args.tool, data))


if __name__ == "__main__":
    main()
