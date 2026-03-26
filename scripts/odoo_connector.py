"""
odoo_connector.py
Odoo JSON-RPC client — stdlib only (urllib + json), no pip installs needed.
Compatible with Odoo 14-18.
"""

import json
import random
import urllib.request
import urllib.error
import re
from datetime import date


class OdooConnector:
    """
    Stateful Odoo JSON-RPC connector using session cookies.
    Same approach as browser-based JSON-RPC (web/session/authenticate).
    """

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.cookies = ''
        self.user_context = {}

    # ----------------------------------------------------------------
    # Transport
    # ----------------------------------------------------------------

    def _rpc(self, endpoint: str, params: dict):
        payload = json.dumps({
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": random.randint(1000, 9999),
        }).encode('utf-8')

        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        if self.cookies:
            headers['Cookie'] = self.cookies

        req = urllib.request.Request(
            self.url + endpoint, data=payload, headers=headers, method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                cookie = resp.getheader('Set-Cookie', '')
                if cookie:
                    self.cookies = cookie.split(';')[0]
                body = json.loads(resp.read().decode('utf-8'))
        except urllib.error.URLError as e:
            raise ConnectionError(f"Cannot reach Odoo at {self.url}: {e}")

        if body.get('error'):
            msg = (body['error'].get('data', {}).get('message')
                   or body['error'].get('message', str(body['error'])))
            raise RuntimeError(f"Odoo error: {msg}")

        return body.get('result', {})

    def _kw(self, model: str, method: str, args: list, kwargs: dict = None):
        return self._rpc('/web/dataset/call_kw', {
            "model": model,
            "method": method,
            "args": args,
            "kwargs": kwargs or {},
            "context": self.user_context,
        })

    # ----------------------------------------------------------------
    # Auth
    # ----------------------------------------------------------------

    def authenticate(self) -> int:
        result = self._rpc('/web/session/authenticate', {
            "db": self.db,
            "login": self.username,
            "password": self.password,
            "context": {},
        })
        if not result or not result.get('uid'):
            raise PermissionError("Authentication failed — check Odoo credentials/db.")
        self.uid = result['uid']
        self.user_context = result.get('user_context', {})
        return self.uid

    def get_employee_id(self) -> int | None:
        rows = self._kw('hr.employee', 'search_read',
                        [[['user_id', '=', self.uid]]],
                        {'fields': ['id', 'name'], 'limit': 1})
        return rows[0]['id'] if rows else None

    # ----------------------------------------------------------------
    # Tasks
    # ----------------------------------------------------------------

    def get_project_tasks(self, project_id: int) -> list[dict]:
        rows = self._kw(
            'project.task', 'search_read',
            [[['project_id', '=', project_id], ['active', '=', True]]],
            {'fields': ['id', 'name', 'description', 'stage_id'],
             'order': 'name asc', 'limit': 100},
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
        return self._kw('project.task', 'create',
                        [{'name': name, 'project_id': project_id,
                          'description': description}])

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

        return self._kw('account.analytic.line', 'create', [{
            'task_id': task_id,
            'project_id': project_id,
            'employee_id': employee_id,
            'unit_amount': round(duration_minutes / 60, 4),
            'name': ' | '.join(filter(None, note_parts)),
            'date': date.today().isoformat(),
        }])


def _strip_html(html: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html)
    for entity, char in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>')]:
        text = text.replace(entity, char)
    return re.sub(r'\s+', ' ', text).strip()
