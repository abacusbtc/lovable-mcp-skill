# Lovable MCP skill for Hermes Agent

Lets Hermes Agent drive [Lovable](https://lovable.dev) — create full-stack apps
from prompts, iterate by chat, inspect code, run SQL against the project's
Postgres, and deploy — over Lovable's official remote MCP server.

## What's in the box

```
lovable-mcp/
├── SKILL.md              # the playbook: setup, auth workaround, guardrails
├── references/tools.md   # digest of all 40 MCP tools
└── scripts/lovable_mcp.py  # standalone driver (works pre-restart, or from cron)
```

## Install (colleague)

Copy (or `git clone`) the `lovable-mcp/` folder into your Hermes skills
directory, then restart Hermes:

```bash
mkdir -p ~/.hermes/skills/devops
cp -r lovable-mcp ~/.hermes/skills/devops/
# restart Hermes / start a new session, then: load the skill and follow SKILL.md
```

Then follow **SKILL.md → "Procedure — Setup"** exactly. It is three commands and
one browser authorization:

1. `hermes mcp add lovable --url https://mcp.lovable.dev --auth oauth`
2. `hermes config set mcp_servers.lovable.oauth.cimd false` ← **required**:
   Lovable's OAuth server rejects Hermes' default client-identity style
   (`invalid_client`) despite advertising support; this forces the registration
   style Lovable does accept
3. `hermes mcp login lovable` — complete the browser sign-in (SKILL.md has the
   headless/remote variant where the login page is driven through the Hermes
   preview pane)
4. Restart Hermes → tools appear as `mcp_lovable_*` in every conversation

## Requirements

- Hermes Agent (any recent version; the `mcp` package ships with it)
- A Lovable account (any plan; Enterprise workspaces must enable Third-party
  MCP clients in Settings → Security)
- Lovable credits for builds/iterations (SQL, diffs, and file reads are free)

## Safety notes

- The OAuth grant is **account-wide**: the agent can read and edit every
  Lovable project the account can access. Revoke at Lovable → Settings →
  Build & deploy → MCP server → Manage access.
- There is **no delete_project** MCP tool — remove projects in the Lovable
  dashboard. The skill sets new projects to `private` immediately.
- `deploy_project` publishes to a public URL on Free/Pro plans.

## License

MIT
