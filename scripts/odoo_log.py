#!/usr/bin/env python3
"""
odoo_log.py — finalises timesheet after Claude picks the task.
Called from the /odoo-timesheet:log command or a PostResponse hook.

Reads pending state + Claude's JSON response from stdin.
"""
import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(__file__))
from utils import (load_config, is_config_valid, load_pending, clear_pending,
                   read_hook_stdin, make_task_name)
from odoo_connector import OdooConnector


def main():
    cfg = load_config()
    valid, missing = is_config_valid(cfg)
    if not valid:
        print(f"[odoo-timesheet] Config missing: {missing}")
        return

    pending = load_pending()
    if not pending:
        # Nothing to log
        return

    # Claude's response comes via stdin (hook provides it as text)
    raw = sys.stdin.read().strip()
    task_id = None
    task_name_new = None

    try:
        m = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if m:
            resp = json.loads(m.group())
            if resp.get('action') == 'match' and resp.get('task_id'):
                task_id = int(resp['task_id'])
            else:
                task_name_new = resp.get('task_name', pending['task_description'][:80])
        else:
            raise ValueError("No JSON in response")
    except Exception as e:
        print(f"[odoo-timesheet] Could not parse response ({e}), will auto-create task.")
        if cfg.get('auto_create_task'):
            task_name_new = pending['task_description'][:80]
        else:
            clear_pending()
            return

    try:
        odoo = OdooConnector(cfg['odoo_url'], cfg['odoo_db'],
                             cfg['odoo_user'], cfg['odoo_password'])
        odoo.authenticate()
    except Exception as e:
        print(f"[odoo-timesheet] ✗ Odoo connection failed: {e}")
        clear_pending()
        return

    try:
        if not task_id:
            name = make_task_name(cfg, task_name_new or pending['task_description'][:80])
            task_id = odoo.create_task(pending['project_id'], name)
            print(f"[odoo-timesheet] ✓ Created task [{task_id}] {name}")

        ts_id = odoo.create_timesheet(
            task_id=task_id,
            project_id=pending['project_id'],
            employee_id=pending['employee_id'],
            duration_minutes=pending['duration_minutes'],
            summary=pending['task_description'],
            tokens_used=pending['tokens_used'],
            session_name=pending['session_id'],
        )
        mins = round(pending['duration_minutes'], 1)
        print(f"[odoo-timesheet] ✓ Timesheet logged — task={task_id} | {mins}min | {pending['tokens_used']:,} tokens | entry={ts_id}")
    except Exception as e:
        print(f"[odoo-timesheet] ✗ Failed: {e}")

    clear_pending()


if __name__ == '__main__':
    main()
