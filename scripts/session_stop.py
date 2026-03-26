#!/usr/bin/env python3
"""
session_stop.py — Stop hook
Collects session data, fetches Odoo tasks, prints matching prompt for Claude.
Claude picks the task, then odoo_log.py finalises the timesheet.
"""
import sys
import os
import time
import difflib

sys.path.insert(0, os.path.dirname(__file__))
from utils import (load_config, save_config, is_config_valid,
                   load_session, clear_session, write_pending,
                   read_hook_stdin, extract_last_user_message, extract_tokens)
from odoo_connector import OdooConnector

PLUGIN_ROOT = os.environ.get('CLAUDE_PLUGIN_ROOT', os.path.dirname(os.path.dirname(__file__)))


def main():
    cfg = load_config()
    valid, missing = is_config_valid(cfg)
    if not valid:
        print(f"[odoo-timesheet] ⚠ Config incomplete — missing: {missing}")
        print(f"[odoo-timesheet] Run: /odoo-timesheet:setup")
        clear_session()
        return

    hook_data = read_hook_stdin()
    session = load_session()

    # --- Duration ---
    if session:
        duration_seconds = time.time() - session['start_time']
        session_id = session.get('session_id', '')
    else:
        duration_seconds = 0
        session_id = hook_data.get('session_id', '')

    if duration_seconds < cfg['min_duration_seconds']:
        clear_session()
        return   # too short, skip silently

    duration_minutes = duration_seconds / 60
    tokens_used = extract_tokens(hook_data)
    task_description = extract_last_user_message(hook_data)

    # --- Odoo connection ---
    try:
        odoo = OdooConnector(cfg['odoo_url'], cfg['odoo_db'],
                             cfg['odoo_user'], cfg['odoo_password'])
        odoo.authenticate()
    except Exception as e:
        print(f"[odoo-timesheet] ✗ Odoo connection failed: {e}")
        clear_session()
        return

    # --- Auto-detect employee ---
    employee_id = cfg.get('employee_id')
    if not employee_id:
        employee_id = odoo.get_employee_id()
        if employee_id:
            cfg['employee_id'] = employee_id
            save_config(cfg)

    # --- Fetch tasks ---
    try:
        tasks = odoo.get_project_tasks(cfg['project_id'])
    except Exception as e:
        print(f"[odoo-timesheet] ✗ Failed to fetch tasks: {e}")
        clear_session()
        return

    # --- Save pending state for odoo_log.py ---
    write_pending({
        'duration_minutes': duration_minutes,
        'tokens_used': tokens_used,
        'session_id': session_id,
        'task_description': task_description,
        'employee_id': employee_id,
        'project_id': cfg['project_id'],
    })
    clear_session()

    # --- AI matching OR keyword matching ---
    if cfg['ai_matching'] == 'keyword':
        _keyword_match_and_log(odoo, tasks, cfg, task_description,
                               duration_minutes, tokens_used, session_id, employee_id)
    else:
        # claude_code mode: print prompt, Claude responds, odoo_log.py runs next
        _print_matching_prompt(task_description, tasks)


def _print_matching_prompt(task_description: str, tasks: list[dict]):
    """Print JSON block that Claude Code reads and responds to."""
    tasks_list = '\n'.join(
        f'  [{t["id"]}] {t["name"]}'
        + (f' — {t["description"][:80]}' if t['description'] else '')
        for t in tasks
    )
    print(f"""
=== ODOO TIMESHEET: TASK MATCHING ===
I just finished working on:
"{task_description}"

Available tasks in this Odoo project:
{tasks_list if tasks_list else '  (no open tasks found)'}

Please respond with ONLY this JSON — no explanation:
{{
  "action": "match",
  "task_id": <number from list above>
}}
OR if nothing matches:
{{
  "action": "create",
  "task_name": "<short name for new task>"
}}
=== END TIMESHEET REQUEST ===
""")


def _keyword_match_and_log(odoo, tasks, cfg, description,
                           duration_minutes, tokens_used, session_id, employee_id):
    """Offline fallback: keyword matching then direct log."""
    from utils import clear_pending
    task_id = None
    task_name_new = None

    if tasks:
        names = [t['name'].lower() for t in tasks]
        matches = difflib.get_close_matches(description.lower(), names, n=1, cutoff=0.35)
        if matches:
            task_id = tasks[names.index(matches[0])]['id']

    if not task_id:
        if cfg.get('auto_create_task'):
            task_name_new = description[:80]
        else:
            print("[odoo-timesheet] No match, auto_create_task=false. Skipping.")
            clear_pending()
            return

    _do_log(odoo, cfg['project_id'], task_id, task_name_new,
            employee_id, duration_minutes, description, tokens_used, session_id)
    clear_pending()


def _do_log(odoo, project_id, task_id, task_name_new,
            employee_id, duration_minutes, summary, tokens_used, session_id):
    try:
        if not task_id:
            task_id = odoo.create_task(project_id, task_name_new or summary[:80])
            print(f"[odoo-timesheet] ✓ Created task [{task_id}] {task_name_new}")

        ts_id = odoo.create_timesheet(
            task_id=task_id, project_id=project_id, employee_id=employee_id,
            duration_minutes=duration_minutes, summary=summary,
            tokens_used=tokens_used, session_name=session_id,
        )
        mins = round(duration_minutes, 1)
        print(f"[odoo-timesheet] ✓ Timesheet logged — task={task_id} | {mins}min | {tokens_used:,} tokens | entry={ts_id}")
    except Exception as e:
        print(f"[odoo-timesheet] ✗ Failed to log timesheet: {e}")


if __name__ == '__main__':
    main()
