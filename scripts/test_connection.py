#!/usr/bin/env python3
"""
test_connection.py — verifies Odoo config and connection.
Called by /odoo-timesheet:test command.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from utils import load_config, is_config_valid, CONFIG_PATH
from odoo_connector import OdooConnector


def main():
    cfg = load_config()
    valid, missing = is_config_valid(cfg)

    print(f"Config path: {CONFIG_PATH}")

    if not valid:
        print(f"✗ Config incomplete — missing fields: {missing}")
        print("  Run /odoo-timesheet:setup to configure.")
        sys.exit(1)

    print(f"Connecting to: {cfg['odoo_url']} (db: {cfg['odoo_db']}) ...")
    try:
        odoo = OdooConnector(cfg['odoo_url'], cfg['odoo_db'],
                             cfg['odoo_user'], cfg['odoo_password'])
        uid = odoo.authenticate()
        emp_id = odoo.get_employee_id()
        tasks = odoo.get_project_tasks(cfg['project_id'])

        print(f"✓ Connected | uid={uid} | employee_id={emp_id or 'not found'}")
        print(f"✓ Project {cfg['project_id']}: {len(tasks)} open tasks")
        for t in tasks[:10]:
            print(f"  [{t['id']}] {t['name']}")
        if len(tasks) > 10:
            print(f"  ... and {len(tasks) - 10} more")

        if not emp_id:
            print("\n⚠ No hr.employee linked to your user.")
            print("  Timesheets will still be created, but without an employee.")
            print("  Ask your Odoo admin to link your user to an Employee record.")

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
