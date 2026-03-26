---
description: Configure Odoo connection for the timesheet plugin (URL, DB, credentials, project ID)
---

Help the user configure the odoo-timesheet plugin by collecting the following information interactively:

1. Ask for each missing config value one by one:
   - `odoo_url` — Odoo server URL (e.g. https://mycompany.odoo.com)
   - `odoo_db` — Database name
   - `odoo_user` — Login email
   - `odoo_password` — Password or API key (Settings → Users → API Keys)
   - `project_id` — Project ID (found in the URL when viewing the project: /odoo/project/NUMBER)

2. Once you have all values, save them by running (replace the placeholder values with what the user provided):
```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/odoo_log.py" --setup \
  --url "<URL>" --db "<DB>" --user "<USER>" --password "<PASSWORD>" --project-id <PROJECT_ID>
```

If that script doesn't support --setup flags, save directly:
```bash
python3 - <<EOF
import sys, os, json
sys.path.insert(0, os.environ['CLAUDE_PLUGIN_ROOT'] + '/scripts')
from utils import load_config, save_config, CONFIG_PATH

cfg = load_config()
cfg['odoo_url'] = '<URL>'
cfg['odoo_db'] = '<DB>'
cfg['odoo_user'] = '<USER>'
cfg['odoo_password'] = '<PASSWORD>'
cfg['project_id'] = <PROJECT_ID>
save_config(cfg)
print(f"Config saved to: {CONFIG_PATH}")
EOF
```

3. Then test the connection:
```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/test_connection.py"
```

4. Confirm to the user what was saved and whether the connection test passed.

**Config options:**
- `ai_matching`: `"claude_code"` (default, uses AI to match tasks) or `"keyword"` (fast offline matching)
- `auto_create_task`: `true` (create task if no match) or `false` (skip if no match)
- `min_duration_seconds`: minimum session length to log (default: 30)
- `employee_id`: auto-detected from your Odoo user, or set manually
