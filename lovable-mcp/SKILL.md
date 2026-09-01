---
name: lovable-mcp
description: Drive Lovable app-building from Hermes via remote MCP.
version: 0.1.0
author: Christopher Manie (abacusbtc), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [lovable, mcp, app-building, oauth, deployment]
    related_skills: [mcp-server-connectivity]
---

# Lovable MCP Skill

Connect Hermes Agent to Lovable's remote MCP server (`https://mcp.lovable.dev`) so
the agent can create full-stack apps (React + Tailwind + shadcn/ui + Supabase),
iterate on them by chat, query their Postgres database, and deploy to production —
without opening the Lovable editor. This skill documents the exact working setup
(including two non-obvious workarounds), the operational guardrails, and a
standalone driver script that works even before MCP tools load into a session.

## When to Use

- "Build me a Lovable app / landing page / dashboard / internal tool"
- "Deploy my Lovable project" / "show me what changed in my Lovable project"
- "Run SQL against my Lovable project's database"
- Setting up a new machine or Hermes profile to use Lovable (the setup below is
  the proven path — don't improvise, Lovable's OAuth rejects naive attempts)
- Don't use for: Lovable's *chat connectors* (those let Lovable call YOUR tools —
  this is the reverse), or non-Lovable MCP servers (use `mcp-server-connectivity`).

## Prerequisites

- Lovable account, any plan. Third-party MCP client access must be enabled for
  the workspace (default ON for Free/Pro/Business; Enterprise admins must enable
  it in Settings → Security → Privacy & security → Third-party MCP clients).
- The `mcp` Python package in the Hermes venv (Hermes installs it; check with
  `terminal`: `~/.hermes/hermes-agent/venv/bin/python -c "import mcp"`).
- MCP tool calls spend **real Lovable credits** (builds, chat iterations). SQL
  queries, file reads, and diffs are free.

## Procedure — Setup (first time per machine)

Perform steps in this exact order via the `terminal` tool. Steps 2–3 are the
critical workaround: Lovable's OAuth server rejects Hermes' default client-identity
style (CIMD) with `invalid_client`, despite advertising support for it. Forcing
dynamic client registration fixes it.

1. Add the server. Answer `Y` to "continue without authentication" and `y` to
   "save config anyway" (it cannot authenticate yet — that's expected):
   ```
   hermes mcp add lovable --url https://mcp.lovable.dev --auth oauth
   ```
   Completion check: `hermes mcp ls` shows `lovable` (status `disabled` is fine).
2. Force dynamic client registration. The value must be a real boolean:
   ```
   hermes config set mcp_servers.lovable.oauth.cimd false
   ```
   Completion check: `hermes config get mcp_servers.lovable` shows `cimd: false`.
3. Authenticate. If a desktop browser is available on this machine, just run
   `hermes mcp login lovable` and complete the browser flow. On a headless or
   remote machine (agent host ≠ your screen), run it in a background PTY and
   drive the flow through a page the user can see:
   - Start: `terminal(command="hermes mcp login lovable", background=true, pty=true)`
   - `process(action="log", ...)` → copy the printed
     `https://lovable.dev/oauth/authorize?...` URL
   - Open it where the user can see it (e.g. Hermes desktop preview pane);
     user logs in to Lovable and clicks **Authorize**
   - The browser lands on `http://127.0.0.1:<port>/callback?code=...` and shows a
     connection error — that is the success path; the code is in the address bar
   - Paste that full URL into the still-running login process:
     `process(action="submit", data="<callback URL>")`
   - The PKCE code is **single-use** and the login process must still be alive
     when you paste — if it exited, restart from the `login` step
   Completion check: output shows `✓ Authenticated — N tool(s) available` and
   `$HERMES_HOME/mcp-tokens/lovable.json` exists.
4. Verify: `hermes mcp test lovable` connects and lists ~40 tools.
5. Restart the Hermes session (or spawn a new one) — MCP tools load at startup
   as `mcp_lovable_<tool>` and are available in every conversation on every
   platform. The current session will NOT see them (loader initializes at
   session start; that's expected, not a bug).

## How to Run

Prefer the injected `mcp_lovable_*` tools in normal conversation. For scripts,
cron jobs, or before a restart, use the bundled driver (run with the Hermes venv
python, which has the `mcp` package):

```
~/.hermes/hermes-agent/venv/bin/python scripts/lovable_mcp.py tools
~/.hermes/hermes-agent/venv/bin/python scripts/lovable_mcp.py call list_workspaces
~/.hermes/hermes-agent/venv/bin/python scripts/lovable_mcp.py call create_project \
    --data '{"workspace_id": "<id>", "initial_message": "Build a todo app", "wait": true}'
```

`--server` overrides the token name (default `lovable`). Token path resolves via
`$HERMES_HOME` (default `~/.hermes`). The driver does NOT refresh tokens — if a
call returns 401, re-run `hermes mcp login lovable`.

## Quick Reference — workflow

1. `list_workspaces` → workspace id (call first; `create_project` needs it when
   the account has more than one workspace)
2. `create_project(workspace_id, initial_message, wait=true)` → full build;
   returns `projectId`, `message_id`, `preview_url`
3. `set_project_visibility(project_id, "private")` immediately — see Pitfalls
4. `get_diff(project_id, message_id)` → review what the agent changed
5. `send_message(project_id, msg, plan_mode=true)` to discuss architecture
   before code; `wait=true` (default) blocks until the build finishes
6. `enable_database` → `query_database` (live SQL incl. DDL and writes)
7. `deploy_project(project_id)` → live URL on `lovable.app`

Full tool reference: `references/tools.md`.

## Pitfalls

- **`invalid_client` on the authorize page** = CIMD rejected. Fix is step 2 of
  setup (`oauth.cimd: false`). Verify it survived: config values must be real
  YAML booleans, not the string `"false"`.
- **No `delete_project` tool exists.** Remove projects only in the Lovable
  dashboard. Keep test junk private.
- **`set_project_visibility` first.** `deploy_project` on Free/Pro publishes to
  a URL anyone with the link can reach; previews of draft projects are
  semi-public by default until set private.
- **Scope is the whole account.** One OAuth grant = the client can read and edit
  every Lovable project the account can access. Revoke via Lovable Settings →
  Build & deploy → MCP server → Manage access (or Third-party MCP clients).
- **Credits.** `create_project` and `send_message` consume Lovable credits.
  Retries within ~2 minutes are deduplicated by the server (a retry returns
  `deduplicated: true` with the original IDs — treat it as the earlier call's
  result, don't build twice).
- **`send_message` is slow.** Builds take minutes; keep tool-call timeouts high
  (pass `wait=false` + poll with `get_message` for long builds).
- **401 on every call** = refresh token dead or tokens wiped. Re-run
  `hermes mcp login lovable` (the dynamic-registered client persists in
  `$HERMES_HOME/mcp-tokens/lovable.client.json`; login reuses it).
- **Connectors cannot be added programmatically** — `add_connector` only returns
  a dashboard URL; the human adds the connector in the Lovable UI.

## Verification

- `hermes mcp test lovable` → connects, lists ~40 tools.
- `list_workspaces` returns the account's workspace(s) — proves auth end-to-end.
- Smoke test (spends one credit, disclose first): `create_project` with a
  minimal one-page prompt, check `status: completed`, `get_diff` returns a real
  diff, preview URL renders. Keep it private; delete in the dashboard after.
