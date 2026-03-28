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

2. Once you have all values, save them directly:
```bash
python3 - <<EOF
import sys, json, pathlib

# Find config path
cwd = pathlib.Path.cwd()
config_path = next(
    (c / '.claude' / 'odoo-timesheet' / 'config.json'
     for c in [cwd, *cwd.parents]
     if (c / '.claude' / 'odoo-timesheet' / 'config.json').exists()),
    pathlib.Path.home() / '.claude' / 'plugins' / 'data' / 'odoo-timesheet' / 'config.json'
)
sys.path.insert(0, str(config_path.parent.parent.parent / 'scripts') if 'plugins/data' not in str(config_path) else str(config_path.parent))
from utils import load_config, save_config, CONFIG_PATH

cfg = load_config()
cfg['odoo_url'] = '<URL>'
cfg['odoo_db'] = '<DB>'
cfg['odoo_user'] = '<USER>'
cfg['odoo_password'] = '<PASSWORD>'
cfg['project_id'] = <PROJECT_ID>
save_config(cfg)
print(f"Config saved to: {CONFIG_PATH}")
print(f"scripts_path: {cfg.get('scripts_path', 'not set')}")
EOF
```

3. Register the hooks into ~/.claude/settings.json (so sessions are tracked automatically):
```bash
SCRIPTS=$(python3 -c "import json,pathlib; p=next((c/'.claude'/'odoo-timesheet'/'config.json' for c in [pathlib.Path.cwd(),*pathlib.Path.cwd().parents] if (c/'.claude'/'odoo-timesheet'/'config.json').exists()), pathlib.Path.home()/'.claude'/'plugins'/'data'/'odoo-timesheet'/'config.json'); print(json.loads(p.read_text())['scripts_path'])")
python3 "$SCRIPTS/install_hooks.py"
```

4. Then test the connection:
```bash
python3 "$SCRIPTS/test_connection.py"
```

5. Confirm to the user what was saved, whether hooks were registered, and whether the connection test passed.

**Config options:**
- `ai_matching`: `"claude_code"` (default, uses AI to match tasks) or `"keyword"` (fast offline matching)
- `auto_create_task`: `true` (create task if no match) or `false` (skip if no match)
- `min_duration_seconds`: minimum session length to log (default: 30)
- `employee_id`: auto-detected from your Odoo user, or set manually
