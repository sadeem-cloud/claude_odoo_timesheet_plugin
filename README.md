# odoo-timesheet — Claude Code Plugin

Auto-log your Claude Code sessions as Odoo timesheets. Tracks time spent, token usage, and uses AI to match your work to existing project tasks.

## Install

```bash
/plugin install odoo-timesheet@sadeem-marketplace
```

Then run setup to configure your Odoo connection and register the tracking hooks:

```bash
/odoo-timesheet:setup
```

## Quick Start

```bash
# 1. Configure connection + register hooks
/odoo-timesheet:setup

# 2. Test connection
/odoo-timesheet:test

# 3. Work normally — timesheets log automatically when sessions end
```

## How It Works

1. **Session starts** — `UserPromptSubmit` hook records the start time on your first message
2. **Session ends** — `Stop` hook calculates duration, fetches your Odoo tasks, and asks Claude to match the work to a task
3. **Claude picks a task** — responds with `{"action": "match", "task_id": X}` or `{"action": "create", "task_name": "..."}`
4. **Timesheet logged** — entry created on `account.analytic.line` with duration, tokens, and summary

## Configuration

Config is **project-scoped** — each project has its own `config.json`.

Resolution order:
1. `$CLAUDE_PROJECT_DIR/.claude/odoo-timesheet/config.json`
2. Auto-detect: walks up from cwd to find a dir with `.git` or `.claude`
3. Global fallback: `~/.claude/plugins/data/odoo-timesheet/config.json`

| Key | Description | Default |
|-----|-------------|---------|
| `odoo_url` | Odoo server URL | required |
| `odoo_db` | Database name | required |
| `odoo_user` | Login email | required |
| `odoo_password` | Password or API key | required |
| `project_id` | Odoo project ID (from URL: `/odoo/project/NUMBER`) | required |
| `employee_id` | Employee ID — auto-detected if not set | null |
| `ai_matching` | `"claude_code"` (AI) or `"keyword"` (offline) | `"claude_code"` |
| `auto_create_task` | Create a new task if nothing matches | true |
| `min_duration_seconds` | Minimum session length to log | 30 |

## Commands

| Command | Description |
|---------|-------------|
| `/odoo-timesheet:setup` | Configure Odoo connection and register hooks |
| `/odoo-timesheet:test` | Verify connection and list project tasks |
| `/odoo-timesheet:log` | Manually trigger logging for the current session |

## What Gets Logged

Each entry on `account.analytic.line` contains:
- **Date**: today
- **Hours**: actual session duration
- **Task**: matched from your project or newly created
- **Employee**: auto-detected from your Odoo user
- **Note**: `[task summary] | [tokens: X,XXX] | [session: YYYYMMDD_HHMMSS]`

## Plugin Structure

```
odoo-timesheet/
├── .claude-plugin/
│   └── plugin.json              ← manifest
├── commands/
│   ├── setup.md                 ← /odoo-timesheet:setup
│   ├── log.md                   ← /odoo-timesheet:log
│   └── test.md                  ← /odoo-timesheet:test
├── hooks/
│   └── hooks.json               ← UserPromptSubmit + Stop hook definitions
├── scripts/
│   ├── odoo_connector.py        ← Odoo XML-RPC client (zero deps)
│   ├── utils.py                 ← config, session, and state helpers
│   ├── session_start.py         ← records session start time
│   ├── session_stop.py          ← calculates duration, fetches tasks
│   ├── odoo_log.py              ← finalises timesheet after task match
│   ├── install_hooks.py         ← registers hooks into ~/.claude/settings.json
│   └── test_connection.py       ← connection test
├── skills/
│   └── odoo-timesheet/
│       └── SKILL.md             ← context-aware guidance for Claude
└── README.md
```

## Requirements

- Python 3.10+ (stdlib only — no pip installs needed)
- Odoo 14–18 with Project + Timesheets modules enabled
- For Odoo Online: API key required (Settings → Users → your user → API Keys tab)
- An `hr.employee` record linked to your Odoo user (for the employee field on timesheets)

## Troubleshooting

**Sessions not being logged**
- Run `/odoo-timesheet:test` to verify the connection
- Check the session was longer than `min_duration_seconds` (default 30s)
- Run `/odoo-timesheet:setup` again to ensure hooks are registered in `~/.claude/settings.json`

**Authentication errors (403 / Access Denied)**
- Odoo Online requires an API key, not your login password
- Generate one at: Settings → Users & Companies → Users → your user → API Keys tab
- Self-hosted Odoo accepts username + password directly

**Employee not found**
- Ask your Odoo admin to link your user to an `hr.employee` record
- Or set `employee_id` manually in the config file
