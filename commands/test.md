---
description: Test the Odoo connection and show available tasks in the configured project
---

Test the Odoo connection by running:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/test_connection.py
```

Show the output to the user. If it succeeds, summarise:
- Connected user and employee ID
- Number of tasks found in the project
- First 10 task names

If it fails, help them troubleshoot the config using `/odoo-timesheet:setup`.
