"""Bounded context delivery and observed-read receipts, not proof of understanding."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from tool_policy import is_mutating_tool, is_shell_tool, paths_for_tool, tool_leaf

PAGE_CHARS = 4000
MAX_BYTES = 2 * 1024 * 1024


def document(path: str) -> tuple[str, str]:
    candidate = Path(path)
    if not candidate.is_absolute() or candidate.suffix.lower() != '.md':
        raise ValueError('context documents must be absolute Markdown paths')
    if candidate != candidate.resolve() or candidate.stat().st_size > MAX_BYTES:
        raise ValueError('context document is symlinked or too large')
    content = candidate.read_text(encoding='utf-8')
    return content, hashlib.sha256(content.encode('utf-8')).hexdigest()


def read_page(path: str, offset: int, epoch: str) -> dict[str, Any]:
    content, revision = document(path)
    if offset < 0 or offset > len(content):
        raise ValueError('offset is outside the document')
    end = min(offset + PAGE_CHARS, len(content))
    return {'type': 'workflow-context-page-v1', 'epoch': epoch, 'path': path,
            'revision': revision, 'start': offset, 'end': end, 'total': len(content),
            'text': content[offset:end]}


def unwrap(payload: dict[str, Any]) -> dict[str, Any]:
    """Support one literal tool call in functions.exec, without evaluating JS."""
    if tool_leaf(payload) != 'exec':
        return payload
    value = payload.get('tool_input')
    code = value.get('code') if isinstance(value, dict) else value
    if not isinstance(code, str):
        return payload
    match = re.fullmatch(
        r'\s*text\(await tools\.(exec_command|apply_patch)\((.*)\)\);?\s*', code, re.DOTALL)
    if not match:
        return payload
    try:
        arguments = json.loads(match[2])
    except (ValueError, TypeError):
        return payload
    if match[1] == 'exec_command' and not isinstance(arguments, dict):
        return payload
    if match[1] == 'apply_patch' and not isinstance(arguments, str):
        return payload
    return {**payload, 'tool_name': match[1], 'tool_input': arguments}


def observed_page(response: Any, depth: int = 0) -> dict[str, Any] | None:
    """Require a complete successful shell result, also inside MCP text wrappers."""
    if depth > 5:
        return None
    if isinstance(response, str):
        try:
            return observed_page(json.loads(response), depth + 1)
        except ValueError:
            return None
    if not isinstance(response, dict):
        return None
    if any(response.get(key) for key in ('isError', 'truncated', 'is_truncated', 'output_truncated')):
        return None
    if response.get('exit_code') == 0 and not response.get('session_id'):
        output = response.get('output', response.get('stdout'))
        if not isinstance(output, str):
            return None
        try:
            page = json.loads(output)
        except ValueError:
            return None
        return page if isinstance(page, dict) and page.get('type') == 'workflow-context-page-v1' else None
    content = response.get('content')
    if isinstance(content, list) and len(content) == 1 and isinstance(content[0], dict) and content[0].get('type') == 'text':
        return observed_page(content[0].get('text'), depth + 1)
    return None


def accept_page(restore: dict[str, Any], path: str, offset: int, response: Any) -> bool:
    page = observed_page(response)
    if page is None:
        return False
    try:
        expected = read_page(path, offset, restore['epoch'])
    except (OSError, ValueError, UnicodeError):
        return False
    prior = restore['reads'].get(path, {})
    next_offset = prior.get('offset', 0) if prior.get('revision') == expected['revision'] else 0
    if page != expected or offset != next_offset:
        return False
    restore['reads'][path] = {'revision': expected['revision'], 'offset': expected['end']}
    return True


def missing_reads(restore: dict[str, Any], paths: list[str]) -> list[dict[str, Any]]:
    missing = []
    for path in paths:
        try:
            content, revision = document(path)
        except (OSError, ValueError, UnicodeError) as error:
            missing.append({'path': path, 'offset': 0, 'error': str(error)})
            continue
        prior = restore['reads'].get(path)
        offset = prior['offset'] if prior and prior.get('revision') == revision else 0
        if not prior or prior.get('revision') != revision or offset != len(content):
            missing.append({'path': path, 'offset': offset})
    return missing


def safe_during_restore(payload: dict[str, Any], record: str) -> bool:
    """Reads, questions, interruption, and direct Markdown record repair remain usable."""
    leaf = tool_leaf(payload)
    if leaf in {'request_user_input', 'request_user_input_async', 'interrupt_agent',
                'list_agents', 'wait_agent', 'get_goal'}:
        return True
    if leaf == 'write_stdin':
        value = payload.get('tool_input')
        return isinstance(value, dict) and value.get('chars', '') in {'', '\x03'}
    paths = paths_for_tool(payload)
    if paths:
        root = Path(record).resolve()
        for path in paths:
            candidate = Path(path).expanduser()
            if not candidate.is_absolute():
                candidate = Path(str(payload.get('cwd', '.'))) / candidate
            if (candidate.suffix.lower() != '.md' or candidate.resolve().suffix.lower() != '.md'
                    or root not in candidate.resolve().parents):
                return False
        return True
    if is_shell_tool(payload):
        return not is_mutating_tool(payload)
    # Unknown/opaque tools and worker dispatch must not evade the restore gate.
    if leaf in {'exec', 'js', 'eval', 'evaluate', 'run_code', 'run_script',
                'spawn_agent', 'followup_task', 'send_message'} or is_mutating_tool(payload):
        return False
    return bool(re.match(r'^(?:read|get|list|search|find|fetch|inspect|view)(?:_|$)', leaf))
