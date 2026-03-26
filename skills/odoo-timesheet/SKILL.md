---
name: odoo-timesheet
description: >
  Use this skill when the user mentions Odoo timesheets, asks about logging time,
  wants to configure the timesheet plugin, or asks why a session wasn't logged.
  Also use when interpreting the task-matching JSON response from the Stop hook.
---

# Odoo Timesheet Plugin

This plugin automatically logs Claude Code sessions as Odoo timesheets.

## How it works

1. **Session starts** → `UserPromptSubmit` hook records the start time
2. **Session ends** → `Stop` hook calculates duration, fetches Odoo tasks, prints matching prompt
3. **Claude picks task** → responds with JSON `{"action": "match", "task_id": X}` or `{"action": "create", "task_name": "..."}`
4. **Timesheet logged** → `odoo_log.py` creates/finds the task and logs `account.analytic.line`

## Timesheet entry contains
- Duration in hours (converted from minutes)
- Summary of what was worked on
- Token count as a note
- Session ID timestamp

## Commands
- `/odoo-timesheet:setup` — configure Odoo connection
- `/odoo-timesheet:test` — verify connection and list tasks
- `/odoo-timesheet:log` — manually trigger logging for current session

## Config location
`~/.claude/plugins/data/odoo-timesheet/config.json`

## Config options

| Key | Description | Default |
|-----|-------------|---------|
| `odoo_url` | Odoo server URL | required |
| `odoo_db` | Database name | required |
| `odoo_user` | Login email | required |
| `odoo_password` | Password or API key | required |
| `project_id` | Odoo project ID | required |
| `employee_id` | Employee ID (null = auto) | null |
| `ai_matching` | `claude_code` or `keyword` | `claude_code` |
| `auto_create_task` | Create task if no match | true |
| `min_duration_seconds` | Minimum session to log | 30 |

## Troubleshooting

**Sessions not being logged:**
- Check config is complete: `/odoo-timesheet:test`
- Check session was longer than `min_duration_seconds`
- Verify hooks are enabled in Claude Code settings

**Employee not found:**
- Odoo admin needs to link your user to an `hr.employee` record
- Or set `employee_id` manually in config

**Authentication errors:**
- For Odoo Online: use API key (Settings → Users → [your user] → API Keys)
- For self-hosted: username + password works directly
