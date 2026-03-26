"""
odoo_connector.py
Odoo client supporting both XML-RPC (for API keys) and JSON-RPC (for passwords).
XML-RPC is the standard Odoo external API — works with both passwords and API keys.
Compatible with Odoo 14-18.
"""

import json
import random
import re
import xmlrpc.client
import urllib.request
import urllib.error
from datetime import date


class OdooConnector:
    """
    Odoo connector using XML-RPC (stdlib xmlrpc.client).
    Supports password and API key authentication.
    """

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None

    # ----------------------------------------------------------------
    # Auth
    # ----------------------------------------------------------------

    def authenticate(self) -> int:
        common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        try:
            uid = common.authenticate(self.db, self.username, self.password, {})
        except Exception as e:
            raise ConnectionError(f"Cannot reach Odoo at {self.url}: {e}")
        if not uid:
            raise PermissionError("Authentication failed — check credentials, db name, or API key.")
        self.uid = uid
        return self.uid

    def _models(self):
        return xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

    def _execute(self, model: str, method: str, *args, **kwargs):
        try:
            return self._models().execute_kw(
                self.db, self.uid, self.password,
                model, method, list(args), kwargs
            )
        except xmlrpc.client.Fault as e:
            raise RuntimeError(f"Odoo error: {e.faultString}")
        except Exception as e:
            raise ConnectionError(f"Cannot reach Odoo at {self.url}: {e}")

    def get_employee_id(self) -> int | None:
        rows = self._execute(
            'hr.employee', 'search_read',
            [['user_id', '=', self.uid]],
            fields=['id', 'name'], limit=1
        )
        return rows[0]['id'] if rows else None

    # ----------------------------------------------------------------
    # Tasks
    # ----------------------------------------------------------------

    def get_project_tasks(self, project_id: int) -> list[dict]:
        rows = self._execute(
            'project.task', 'search_read',
            [['project_id', '=', project_id], ['active', '=', True]],
            fields=['id', 'name', 'description', 'stage_id'],
            order='name asc', limit=100
        )
        tasks = []
        for r in rows:
            desc = _strip_html(r.get('description') or '')
            tasks.append({
                'id': r['id'],
                'name': r['name'],
                'description': desc[:200],
                'stage': r['stage_id'][1] if r.get('stage_id') else '',
            })
        return tasks

    def create_task(self, project_id: int, name: str, description: str = '') -> int:
        return self._execute('project.task', 'create',
                             {'name': name, 'project_id': project_id,
                              'description': description})

    # ----------------------------------------------------------------
    # Timesheet  (account.analytic.line)
    # ----------------------------------------------------------------

    def create_timesheet(self, task_id: int, project_id: int, employee_id: int,
                         duration_minutes: float, summary: str,
                         tokens_used: int = 0, session_name: str = '') -> int:
        note_parts = [summary]
        if tokens_used:
            note_parts.append(f"[tokens: {tokens_used:,}]")
        if session_name:
            note_parts.append(f"[session: {session_name}]")

        return self._execute('account.analytic.line', 'create', {
            'task_id': task_id,
            'project_id': project_id,
            'employee_id': employee_id,
            'unit_amount': round(duration_minutes / 60, 4),
            'name': ' | '.join(filter(None, note_parts)),
            'date': date.today().isoformat(),
        })


def _strip_html(html: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html)
    for entity, char in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>')]:
        text = text.replace(entity, char)
    return re.sub(r'\s+', ' ', text).strip()
