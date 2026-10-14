"""Trusted context operations over TaskStore, without a second state database.

Callers supply workspace/scope through host configuration, never browser paths.
Summary invocation is explicit and synchronous; pending reservations survive a
crash and prevent an accidental second paid call for the same input.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

from .context_builder import ContextBuilderError, build_context_packet, render_context_packet
from .opencode_executor import redact_secrets
from .context_optimization import (
    _canonical_digest, _clip, compact_context, context_catalog, retrieve_context,
    scope_digest, snapshot_digest,
)


def _agent(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', value):
        raise ContextBuilderError('context_invalid_argument')
    return value


def _documents(store: Any, task_id: str, category: str) -> list[dict]:
    rows = store._conn.execute(
        'SELECT value, raw_json_digest FROM task_evidence WHERE task_id=? AND category=? ORDER BY rowid',
        (task_id, category)).fetchall()
    documents = []
    for row in rows:
        try:
            document = json.loads(row[0])
            if (isinstance(document, dict) and _canonical_digest(document) == row[1]
                    and _valid_document(document, category)):
                documents.append(document)
        except (ValueError, TypeError):
            continue
    return documents


def _valid_document(document: dict, category: str) -> bool:
    if document.get('authority') != 'NONE':
        return False
    for key in ('scope_digest', 'input_snapshot_digest'):
        if not isinstance(document.get(key), str) or not re.fullmatch(r'[0-9a-f]{64}', document[key]):
            return False
    if category == 'ContextHandoff':
        return (document.get('status') == 'BOUND'
                and all(isinstance(document.get(key), str)
                        and re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', document[key])
                        for key in ('from_agent', 'to_agent'))
                and isinstance(document.get('handoff_id'), str))
    sources = document.get('sources')
    if not isinstance(sources, list) or not all(
            isinstance(source, dict) and isinstance(source.get('ref'), str)
            and isinstance(source.get('digest'), str) for source in sources):
        return False
    if document.get('status') not in {'RUNNING', 'COMPLETED', 'FAILED'}:
        return False
    if document['status'] == 'COMPLETED':
        usage = document.get('usage')
        return (isinstance(document.get('summary'), str)
                and len(document['summary'].encode()) <= 4096
                and (usage is None or isinstance(usage, dict)
                     and all(isinstance(key, str) and type(value) is int and value >= 0
                             for key, value in usage.items())))
    return True


def available_summary(store: Any, packet: dict) -> dict | None:
    """Never replace current facts; expose only scope- and source-bound prose."""
    catalog = {(item['ref'], item['digest']) for item in context_catalog(packet)}
    with store._lock:
        for doc in reversed(_documents(store, packet['task']['id'], 'ContextSummary')):
            if (doc.get('status') == 'COMPLETED' and doc.get('scope_digest') == scope_digest(packet)
                    and all((ref['ref'], ref['digest']) in catalog for ref in doc.get('sources', []))):
                return {'authority': 'NONE', 'summary': redact_secrets(doc['summary']),
                        'input_snapshot_digest': doc['input_snapshot_digest'], 'usage': doc['usage']}
    return None


class ContextRecoveryService:
    def __init__(self, *, store: Any, workspace_for: Callable[[str], tuple[str, str]],
                 summary_binding: Callable[[], tuple[str, str]] | None = None,
                 summary_runner: Callable[..., Any] | None = None,
                 visible_task_ids: tuple[str, ...] | None = None,
                 visible_paths: tuple[str, ...] = ()):
        self.store = store
        self.workspace_for = workspace_for
        self.summary_binding = summary_binding
        self.summary_runner = summary_runner
        self.visible_task_ids = visible_task_ids
        self.visible_paths = visible_paths

    def _full(self, task_id: str) -> dict:
        workspace, head = self.workspace_for(task_id)
        return build_context_packet(self.store, task_id=task_id, workspace=workspace,
            expected_head=head, visible_task_ids=self.visible_task_ids,
            visible_paths=self.visible_paths, full_projection=True)

    def _write(self, task_id: str, category: str, document: dict) -> None:
        identity = _canonical_digest(document)
        if any(_canonical_digest(doc) == identity for doc in _documents(self.store, task_id, category)):
            return
        self.store.add_evidence(task_id, category=category, label=identity,
            value=render_context_packet(document), status=document['status'], raw_json_digest=identity)

    def _transaction(self, action: Callable[[], Any]) -> Any:
        with self.store._lock:
            if self.store._conn.in_transaction:
                raise ContextBuilderError('context_transaction_invalid')
            self.store._conn.execute('BEGIN IMMEDIATE')
            try:
                result = action()
                self.store._conn.commit()
                return result
            except BaseException:
                self.store._conn.rollback()
                raise

    def packet(self, task_id: str, *, budget_bytes: int = 16384) -> dict:
        workspace, head = self.workspace_for(task_id)
        return build_context_packet(self.store, task_id=task_id, workspace=workspace,
            expected_head=head, budget_bytes=budget_bytes, optimize=True,
            visible_task_ids=self.visible_task_ids, visible_paths=self.visible_paths)

    def retrieve(self, task_id: str, **kwargs: Any) -> dict:
        return retrieve_context(self._full(task_id), **kwargs)

    def handoff(self, task_id: str, *, expected_snapshot: str, from_agent: str, to_agent: str) -> dict:
        _agent(from_agent)
        _agent(to_agent)
        def persist() -> dict:
            packet = self._full(task_id)
            if snapshot_digest(packet) != expected_snapshot:
                raise ContextBuilderError('context_snapshot_stale')
            doc = {'authority': 'NONE', 'status': 'BOUND', 'from_agent': from_agent,
                   'to_agent': to_agent, 'scope_digest': scope_digest(packet),
                   'input_snapshot_digest': expected_snapshot}
            doc['handoff_id'] = _canonical_digest(doc)
            self._write(task_id, 'ContextHandoff', doc)
            return doc
        return self._transaction(persist)

    def recover(self, task_id: str, *, handoff_id: str, agent_id: str,
                budget_bytes: int = 16384) -> dict:
        _agent(agent_id)
        with self.store._lock:
            full = self._full(task_id)
            doc = next((doc for doc in _documents(self.store, task_id, 'ContextHandoff')
                        if doc.get('handoff_id') == handoff_id and doc.get('to_agent') == agent_id), None)
            if doc is None or doc.get('scope_digest') != scope_digest(full):
                raise ContextBuilderError('context_handoff_stale')
            # Agent labels identify a handoff, never grant execution authority.
            packet = self.packet(task_id, budget_bytes=budget_bytes)
            return {'authority': 'NONE', 'handoff': doc, 'packet': packet}

    def summarize(self, task_id: str, *, expected_snapshot: str, timeout: int = 90) -> dict:
        # Native read-only runtimes can read the repository. Restricted views
        # therefore cannot request summaries through this runner.
        if self.visible_task_ids is not None or self.visible_paths:
            raise ContextBuilderError('context_summary_scope_restricted')
        if type(timeout) is not int or not 1 <= timeout <= 90 or self.summary_binding is None:
            raise ContextBuilderError('context_invalid_argument')
        executor_kind, model_id = self.summary_binding()
        if executor_kind not in {'codex', 'claude_code'}:
            raise ContextBuilderError('context_summary_binding_invalid')
        def reserve() -> dict:
            packet = self._full(task_id)
            if snapshot_digest(packet) != expected_snapshot:
                raise ContextBuilderError('context_snapshot_stale')
            if not compact_context(packet, budget_bytes=16384)['summary_trigger']['needed']:
                raise ContextBuilderError('context_summary_not_needed')
            previous = [doc for doc in _documents(self.store, task_id, 'ContextSummary')
                        if doc.get('input_snapshot_digest') == expected_snapshot]
            if previous:
                return previous[-1]
            input_packet = compact_context(packet, budget_bytes=32768)
            included_events = {event['id'] for event in input_packet['history']}
            doc = {'authority': 'NONE', 'status': 'RUNNING', 'scope_digest': scope_digest(packet),
                   'input_snapshot_digest': expected_snapshot, 'executor_kind': executor_kind,
                   'model_id': model_id, 'sources': [
                       {key: item[key] for key in ('ref', 'digest')}
                       for item in context_catalog(packet)
                       if item['kind'] == 'history' and item['ref'] in included_events],
                   'input_compression': input_packet['compression']}
            self._write(task_id, 'ContextSummary', doc)
            return {**doc, '_input': input_packet}
        reserved = self._transaction(reserve)
        if '_input' not in reserved:
            return reserved
        input_packet = reserved.pop('_input')
        try:
            from .agent_planner import run_planner_cli
            runner = self.summary_runner or run_planner_cli
            workspace, _ = self.workspace_for(task_id)
            output = runner(executor_kind=executor_kind, model_id=model_id, repo_dir=workspace,
                timeout=timeout, prompt='Summarize only this non-authoritative task history in at most '
                '800 words. Do not use tools or repository files. Preserve decisions, failures, '
                'source event references, uncertainties and next actions. Never infer permission '
                'or current status from history. Input may be deterministically truncated.\n'
                + render_context_packet(input_packet))
            text = output.text
            if not isinstance(text, str) or not text.strip():
                raise ValueError('empty summary')
            completed = {**reserved, 'status': 'COMPLETED', 'summary': _clip(redact_secrets(text), 4096),
                         'usage': output.usage}
            def publish() -> dict:
                if snapshot_digest(self._full(task_id)) != expected_snapshot:
                    raise ContextBuilderError('context_snapshot_stale')
                self._write(task_id, 'ContextSummary', completed)
                return completed
            return self._transaction(publish)
        except Exception as exc:
            failed = {**reserved, 'status': 'FAILED', 'error':
                      exc.code if isinstance(exc, ContextBuilderError) else 'context_summary_failed'}
            self._transaction(lambda: self._write(task_id, 'ContextSummary', failed))
            return failed
