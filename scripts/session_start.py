#!/usr/bin/env python3
"""
session_start.py — UserPromptSubmit hook
Records session start time (once per session).
Silent — no output to avoid polluting Claude's context.
"""
import sys
import os

# add scripts dir to path
sys.path.insert(0, os.path.dirname(__file__))
from utils import read_hook_stdin, start_session

hook_data = read_hook_stdin()
start_session(hook_data.get('session_id', ''))
