---
description: Manually log current session as an Odoo timesheet entry
---

Log the current Claude Code session as a timesheet entry in Odoo.

First, resolve the scripts path from config:
```bash
SCRIPTS=$(python3 -c "import json,pathlib; p=next((c/'.claude'/'odoo-timesheet'/'config.json' for c in [pathlib.Path.cwd(),*pathlib.Path.cwd().parents] if (c/'.claude'/'odoo-timesheet'/'config.json').exists()), pathlib.Path.home()/'.claude'/'plugins'/'data'/'odoo-timesheet'/'config.json'); print(json.loads(p.read_text())['scripts_path'])")
```

Then run:
```bash
python3 "$SCRIPTS/session_stop.py"
```

**If the output says "Session too short or no active session"**, ask the user:
> "How many minutes did you work on this session?"

Then re-run with the duration they provide:
```bash
python3 "$SCRIPTS/session_stop.py" --duration <MINUTES>
```

This will:
1. Calculate how long this session has been running (or use the provided duration)
2. Fetch open tasks from your configured Odoo project
3. Ask you to confirm which task matches what you worked on
4. Log the timesheet with time, token count, and a summary

After I show you the task list and you confirm a match, I'll call:
```bash
echo '<JSON_RESPONSE>' | python3 "$SCRIPTS/odoo_log.py"
```
to finalise the entry.

**Important**: Never estimate or hardcode the duration — always use the actual session time or ask the user.
