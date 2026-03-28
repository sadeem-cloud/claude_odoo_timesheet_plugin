---
description: Test the Odoo connection and show available tasks in the configured project
---

Test the Odoo connection by running:
```bash
SCRIPTS=$(python3 -c "import json,pathlib; p=next((c/'.claude'/'odoo-timesheet'/'config.json' for c in [pathlib.Path.cwd(),*pathlib.Path.cwd().parents] if (c/'.claude'/'odoo-timesheet'/'config.json').exists()), pathlib.Path.home()/'.claude'/'plugins'/'data'/'odoo-timesheet'/'config.json'); print(json.loads(p.read_text())['scripts_path'])")
python3 "$SCRIPTS/test_connection.py"
```

Show the output to the user. If it succeeds, summarise:
- Connected user and employee ID
- Number of tasks found in the project
- First 10 task names

If it fails, help them troubleshoot the config using `/odoo-timesheet:setup`.
