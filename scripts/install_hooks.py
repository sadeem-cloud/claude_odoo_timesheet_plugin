#!/usr/bin/env python3
"""
install_hooks.py — registers the odoo-timesheet hooks into ~/.claude/settings.json.
Called automatically at the end of /odoo-timesheet:setup.
Safe to run multiple times (idempotent).
"""
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = os.environ.get('CLAUDE_PLUGIN_ROOT', str(Path(__file__).parent.parent))
SETTINGS_PATH = Path.home() / '.claude' / 'settings.json'

HOOKS_TO_ADD = {
    'UserPromptSubmit': {
        'type': 'command',
        'command': f'python3 {PLUGIN_ROOT}/scripts/session_start.py',
        'timeout': 5,
    },
    'Stop': {
        'type': 'command',
        'command': f'python3 {PLUGIN_ROOT}/scripts/session_stop.py',
        'timeout': 30,
    },
}


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text())
        except Exception:
            pass
    return {}


def save_settings(cfg: dict):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(cfg, indent=2) + '\n')


def hook_already_registered(hook_list: list, script_name: str) -> bool:
    """Check if a hook referencing this script file is already registered."""
    for group in hook_list:
        for h in group.get('hooks', []):
            if script_name in h.get('command', ''):
                return True
    return False


def main():
    settings = load_settings()
    hooks = settings.setdefault('hooks', {})
    added = []

    for event, hook_def in HOOKS_TO_ADD.items():
        event_hooks = hooks.setdefault(event, [])
        script_name = Path(hook_def['command'].split()[-1]).name  # e.g. "session_start.py"
        if hook_already_registered(event_hooks, script_name):
            print(f'  [odoo-timesheet] {event} hook already registered, skipping.')
            continue
        # Append to the first existing group, or create a new one
        if event_hooks:
            event_hooks[0].setdefault('hooks', []).append(hook_def)
        else:
            event_hooks.append({'hooks': [hook_def]})
        added.append(event)

    if added:
        save_settings(settings)
        for event in added:
            print(f'  [odoo-timesheet] ✓ Registered {event} hook in {SETTINGS_PATH}')
    else:
        print(f'  [odoo-timesheet] Hooks already registered — nothing to do.')


if __name__ == '__main__':
    main()
