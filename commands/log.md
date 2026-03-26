---
description: Manually log current session as an Odoo timesheet entry
---

Log the current Claude Code session as a timesheet entry in Odoo.

Run:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_stop.py
```

This will:
1. Calculate how long this session has been running
2. Fetch open tasks from your configured Odoo project
3. Ask you to confirm which task matches what you worked on
4. Log the timesheet with time, token count, and a summary

After I show you the task list and you confirm a match, I'll call:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/odoo_log.py
```
to finalise the entry.
