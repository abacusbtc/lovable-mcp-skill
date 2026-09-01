# Lovable MCP Server — Tool Reference (40 tools)

Machine-readable source of truth: `https://mcp.lovable.dev/skill.md` (maintained
by Lovable alongside the server; always matches what the server exposes). This
file is a working digest. All tool calls run with the connected account's
permissions on real projects; builds and chat messages spend Lovable credits.

## Identity & discovery

| Tool | Notes |
|---|---|
| `get_me` | Profile + workspaces; proves auth end-to-end |
| `list_workspaces` | Call first — yields `workspace_id` for everything else |
| `get_workspace` | Plan, credit balance, member count, settings |

## Projects

| Tool | Notes |
|---|---|
| `create_project` | `initial_message` becomes the first builder prompt; `wait: true` (default) blocks until the first build finishes; `template_project_id` starts from a template; `design_systems` from `list_design_systems`. Returns `projectId`, `message_id`, `preview_url`, `editor_url` |
| `get_project` | Details + screenshot of current state |
| `list_projects` | Search/filter by visibility, publish status, folder |
| `remix_project` | Fork into a workspace (optionally with history/knowledge) |
| `set_project_visibility` | `draft` / `private` / `public` — set `private` right after creating |
| `move_projects_to_folder` | Up to 30 projects |
| `set_folder_visibility` | `personal` / `workspace` |
| `deploy_project` | Publish to `lovable.app`; returns the live URL |
| `render_project_widget` | MCP-App-UI hosts only; project status widget |

## Agent interaction

| Tool | Notes |
|---|---|
| `send_message` | Iterate on a project; `plan_mode: true` = discuss architecture without writing code; `wait: true` blocks (minutes); message ≤ 100k chars; `files` accepts upload `file_id`s |
| `get_message` | Poll after `wait: false` or a timeout |
| `list_messages` | Newest-first; discover `message_id`s |

## Code inspection

| Tool | Notes |
|---|---|
| `get_diff` | Unified diff per `message_id`, or between commit `sha`s |
| `list_files` / `read_file` | File tree / single file at a git `ref` |
| `list_edits` | Edit history with commit SHAs |

## Knowledge (persistent instructions)

| Tool | Notes |
|---|---|
| `get_/set_workspace_knowledge` | Applies to all projects in the workspace (max 10k chars; read before writing — it replaces) |
| `get_/set_project_knowledge` | Per-project version |

Useful knowledge examples: brand colors, "use Supabase auth everywhere", error-
handling conventions, React Query for server state.

## Database (PostgreSQL via Supabase)

| Tool | Notes |
|---|---|
| `get_database_status` | Is a DB provisioned? |
| `enable_database` | Provision (30–60 s, one-time) |
| `query_database` | Raw SQL — SELECT/INSERT/UPDATE/DELETE/DDL. Runs with your full DB permissions; no dry-run |

## Files, connectors, analytics

| Tool | Notes |
|---|---|
| `get_file_upload_url` | Presigned upload → PUT bytes → pass `file_id` into `create_project`/`send_message` (mockups, screenshots, CSVs) |
| `list_connectors` / `list_custom_connectors` | Catalog + status; 50+ integrations (Gmail, Notion, Linear, Slack, Stripe, Supabase, n8n, …) |
| `add_connector` | Returns a dashboard URL only — connector setup is manual in the Lovable UI |
| `get_project_analytics` / `get_project_analytics_trend` | Visitor metrics for published projects (historical / last 30 min) |

## Skills (workspace) & templates

| Tool | Notes |
|---|---|
| `list_template_projects` | Cloneable starting points |
| `list_design_systems` | Reusable design tokens/components for new projects |
| `list_workspace_skills`, `get/create/update/delete_workspace_skill` | Reusable agent skill packs (CRUD fully programmatic, unlike connectors) |

## Retry deduplication

`create_project` and `send_message` detect identical retries (same caller +
arguments within ~2 min, extended while a `wait` is in flight) and return the
original result with `deduplicated: true` instead of double-spending credits.
If the original call is still in flight, the retry errors with instructions to
poll (`list_projects` / `list_messages` + `get_message`).
