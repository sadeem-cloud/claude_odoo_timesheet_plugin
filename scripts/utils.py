"""
utils.py — shared helpers for all scripts
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime

# ----------------------------------------------------------------
# Paths
#
# Config is project-scoped:
#   $CLAUDE_PROJECT_DIR/.claude/odoo-timesheet/config.json
# falling back to the global data dir when no project dir is set.
#
# Runtime state (session, pending) always lives in the global dir
# so it survives across working directories within one session.
# ----------------------------------------------------------------

_global_data_dir = Path(os.environ.get('CLAUDE_PLUGIN_DATA',
                                       Path.home() / '.claude' / 'plugins' / 'data' / 'odoo-timesheet'))
_global_data_dir.mkdir(parents=True, exist_ok=True)

# Project-scoped config dir: use cwd's .claude/odoo-timesheet/ if it
# looks like a project root (has a .git or .claude dir), otherwise fall
# back to the global dir.
def _resolve_config_dir() -> Path:
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '')
    if project_dir:
        d = Path(project_dir) / '.claude' / 'odoo-timesheet'
        d.mkdir(parents=True, exist_ok=True)
        return d
    # Auto-detect: walk up from cwd looking for .git or .claude
    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / '.git').exists() or (candidate / '.claude').exists():
            d = candidate / '.claude' / 'odoo-timesheet'
            d.mkdir(parents=True, exist_ok=True)
            return d
    return _global_data_dir


_config_dir  = _resolve_config_dir()
CONFIG_PATH  = _config_dir / 'config.json'

# Runtime state stays global (shared across all projects in a session)
SESSION_FILE = _global_data_dir / '.session.json'
PENDING_FILE = _global_data_dir / '.pending.json'

# ----------------------------------------------------------------
# Config
# ----------------------------------------------------------------

DEFAULTS = {
    "odoo_url": "",
    "odoo_db": "",
    "odoo_user": "",
    "odoo_password": "",
    "project_id": None,
    "employee_id": None,
    "ai_matching": "claude_code",   # "claude_code" | "keyword"
    "auto_create_task": True,
    "min_duration_seconds": 30,
    "scripts_path": str(Path(__file__).parent),  # path to plugin scripts dir
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULTS, indent=2))
    cfg = json.loads(CONFIG_PATH.read_text())
    for k, v in DEFAULTS.items():
        cfg.setdefault(k, v)
    return cfg


def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def is_config_valid(cfg: dict) -> tuple[bool, list]:
    missing = [k for k in ['odoo_url', 'odoo_db', 'odoo_user', 'odoo_password', 'project_id']
               if not cfg.get(k)]
    return (len(missing) == 0, missing)

# ----------------------------------------------------------------
# Session tracking
# ----------------------------------------------------------------

def start_session(session_id: str = ''):
    if SESSION_FILE.exists():
        return  # already running
    SESSION_FILE.write_text(json.dumps({
        'start_time': time.time(),
        'session_id': session_id or datetime.now().strftime('%Y%m%d_%H%M%S'),
    }))


def load_session() -> dict | None:
    if not SESSION_FILE.exists():
        return None
    try:
        return json.loads(SESSION_FILE.read_text())
    except Exception:
        return None


def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()

# ----------------------------------------------------------------
# Pending state (between Stop hook and AI match response)
# ----------------------------------------------------------------

def write_pending(data: dict):
    PENDING_FILE.write_text(json.dumps(data))


def load_pending() -> dict | None:
    if not PENDING_FILE.exists():
        return None
    try:
        return json.loads(PENDING_FILE.read_text())
    except Exception:
        return None


def clear_pending():
    if PENDING_FILE.exists():
        PENDING_FILE.unlink()

# ----------------------------------------------------------------
# Hook stdin parsing
# ----------------------------------------------------------------

def read_hook_stdin() -> dict:
    import sys
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def extract_last_user_message(hook_data: dict) -> str:
    for msg in reversed(hook_data.get('messages', [])):
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            if isinstance(content, list):
                return ' '.join(b.get('text', '') for b in content
                                if b.get('type') == 'text')[:500]
            return str(content)[:500]
    return 'Development task'


def extract_tokens(hook_data: dict) -> int:
    u = hook_data.get('usage', {})
    return u.get('input_tokens', 0) + u.get('output_tokens', 0)
