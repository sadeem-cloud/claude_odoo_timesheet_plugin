# odoo-timesheet — Claude Code Plugin

Auto-log your Claude Code sessions as Odoo timesheets. Tracks time spent, token usage, and uses AI to match your work to existing project tasks.

## Install

```bash
# From GitHub (once published)
/plugin marketplace add https://github.com/sadeem-cloud/claude_odoo_timesheet_plugin.git
/plugin install odoo-timesheet

# Local install (for development)
claude --plugin-dir ./odoo-timesheet
```

## Quick Start

```bash
# 1. Configure
/odoo-timesheet:setup

# 2. Test connection
/odoo-timesheet:test

# 3. Work normally — timesheets log automatically
```

## Plugin Structure

```
odoo-timesheet/
├── .claude-plugin/
│   └── plugin.json          ← manifest
├── commands/
│   ├── setup.md             ← /odoo-timesheet:setup
│   ├── log.md               ← /odoo-timesheet:log
│   └── test.md              ← /odoo-timesheet:test
├── hooks/
│   └── hooks.json           ← UserPromptSubmit + Stop hooks
├── scripts/
│   ├── odoo_connector.py    ← Odoo JSON-RPC client (zero deps)
│   ├── utils.py             ← shared config/session helpers
│   ├── session_start.py     ← records start time
│   ├── session_stop.py      ← calculates duration, fetches tasks
│   ├── odoo_log.py          ← logs timesheet after task match
│   └── test_connection.py   ← connection test
├── skills/
│   └── odoo-timesheet/
│       └── SKILL.md         ← context-aware guidance
└── README.md
```

## What Gets Logged

Each timesheet entry on `account.analytic.line` contains:
- **Date**: today
- **Hours**: actual session duration
- **Note**: `[task summary] | [tokens: X,XXX] | [session: YYYYMMDD_HHMMSS]`
- **Task**: matched or newly created
- **Employee**: auto-detected from your Odoo user

## Requirements

- Python 3.10+ (stdlib only — no pip installs)
- Odoo 14–18 with Project + Timesheets modules
- For Odoo Online: API key required (Settings → Users → API Keys)
- `hr.employee` record linked to your Odoo user (for employee field)
