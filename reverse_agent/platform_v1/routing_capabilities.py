"""Versioned, exact-id routing fallback and provider-free calibration ingestion.

Unknown models have no demonstrated capability. Owner entries are exact family/
version ids (provider namespace may be omitted), never substring matches.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

VERSION = 1
KINDS = frozenset({'code', 'analysis', 'writing', 'research_design', 'review'})
# These are conservative context estimates, not capability claims.
PRIOR_MODELS = {
    'gpt-6.1-sol': {'context_window': 200_000},
    'gpt-6-sol': {'context_window': 200_000},
    'claude-sonnet-4-6': {'context_window': 200_000},
    'gemini-flash': {'context_window': 1_000_000},
}


class CapabilityTable(dict):
    """Owner tiers keyed by model id, plus adopted benchmark priors (issue 1264)."""
    benchmarks: Any = None


def read_capability_table(state_path: Path | None) -> dict[str, Any]:
    if state_path is None:
        return {}
    from .capability_benchmarks import read_benchmark_priors
    table = CapabilityTable()
    table.benchmarks = read_benchmark_priors(state_path)
    try:
        data = json.loads(Path(state_path).with_name('model_capabilities.json').read_text(encoding='utf-8'))
    except FileNotFoundError:
        return table
    except (OSError, ValueError) as exc:
        raise ValueError('invalid_model_capabilities') from exc
    if not isinstance(data, dict) or type(data.get('version')) is not int or data.get('version') != VERSION or not isinstance(data.get('models'), dict):
        raise ValueError('invalid_model_capabilities')
    for entry in data['models'].values():
        if (not isinstance(entry, dict) or not isinstance(entry.get('tiers', {}), dict)
                or 'notes' in entry and not isinstance(entry['notes'], str)):
            raise ValueError('invalid_model_capabilities')
        if any(k not in KINDS or type(v) is not int or not 1 <= v <= 5 for k, v in entry.get('tiers', {}).items()):
            raise ValueError('invalid_model_capabilities')
    table.update(data['models'])
    return table


def calibration_profiles(results: Sequence[Mapping[str, Any]], *, version: int = VERSION) -> dict[str, Any]:
    """Convert independently checked calibration outcomes to real-run bucket shape.

    The fixed v1 suite covers code fix + tests, data analysis, summary, experiment
    design and review, at declared difficulty 1..5. A runner is a follow-up; this
    function neither invokes models nor promotes self-reported CLI success.
    Each record must carry a host-validated success boolean and suite version.
    """
    if type(version) is not int or version != VERSION:
        raise ValueError('unsupported_calibration_version')
    profiles: dict[str, Any] = {}
    for row in results:
        if (not isinstance(row, Mapping) or type(row.get('suite_version')) is not int or row.get('suite_version') != version or row.get('kind') not in KINDS
                or type(row.get('difficulty')) is not int or not 1 <= row['difficulty'] <= 5
                or type(row.get('success')) is not bool or not isinstance(row.get('binding_id'), str)
                or not row['binding_id']):
            raise ValueError('invalid_calibration_result')
        if ('refused' in row and type(row['refused']) is not bool
                or 'tokens' in row and (type(row['tokens']) is not int or row['tokens'] < 0)
                or row.get('seconds') is not None and (type(row['seconds']) not in (int, float)
                    or not math.isfinite(row['seconds']) or row['seconds'] < 0)):
            raise ValueError('invalid_calibration_result')
        profile = profiles.setdefault(row['binding_id'], {'task_buckets': {}, 'calibration_version': version,
            'attempts': 0, 'ok': 0, 'failed': 0, 'observed_tokens': 0, 'tool_errors': 0, 'content_attempts': {}})
        content = row.get('content_class', row['kind'])
        if content not in KINDS | {'security_simulation'}:
            raise ValueError('invalid_calibration_result')
        evidence = profile['content_attempts'].setdefault(content, {'attempts': 0, 'refusals': 0})
        evidence['attempts'] += 1
        evidence['refusals'] += int(row.get('refused') is True)
        profile['observed_tokens'] += row.get('tokens', 0)
        bucket = profile['task_buckets'].setdefault(f"{row['kind']}:{row['difficulty']}",
            {'attempts': 0, 'ok': 0, 'timeouts': 0, '_seconds': []})
        # Willingness is separate evidence; never a capability failure.
        if row.get('refused'):
            continue
        profile['attempts'] += 1
        profile['ok'] += int(row['success'])
        profile['failed'] += int(not row['success'])
        profile['tool_errors'] += int(row.get('tool_error') is True)
        bucket['attempts'] += 1
        bucket['ok'] += int(row['success'])
        bucket['timeouts'] += int(row.get('timeout') is True)
        if type(row.get('seconds')) in (int, float) and row['seconds'] >= 0 and row['success']:
            bucket['_seconds'].append(row['seconds'])
    for profile in profiles.values():
        profile['success_rate'] = profile['ok'] / profile['attempts'] if profile['attempts'] else None
        profile['tool_reliability'] = 1 - profile['tool_errors'] / max(1, profile['attempts'])
        profile['refusal_rates'] = {content: row['refusals'] / row['attempts']
                                    for content, row in profile['content_attempts'].items()}
        for bucket in profile['task_buckets'].values():
            bucket['success_rate'] = bucket['ok'] / bucket['attempts'] if bucket['attempts'] else None
            seconds = bucket.pop('_seconds')
            bucket['median_ok_seconds'] = median(seconds) if seconds else None
    return profiles


def tier_evidence(model: str, profile: Mapping[str, Any], kind: str, difficulty: int,
                  table: Mapping[str, Any] | None = None,
                  override: Mapping[str, Any] | None = None) -> tuple[int, bool, str]:
    detail = tier_detail(model, profile, kind, difficulty, table, override)
    return detail['tier'], detail['unproven'], detail['source']


def tier_detail(model: str, profile: Mapping[str, Any], kind: str, difficulty: int,
                table: Mapping[str, Any] | None = None,
                override: Mapping[str, Any] | None = None, benchmarks: Any = None) -> dict[str, Any]:
    """Resolve binding Owner tiers > measured buckets > Owner table > benchmark prior > fallback.

    A benchmark prior also enters measured buckets as pseudo-observations, so a
    few real runs refine it and about ``MEASURED_DOMINATES`` attempts outweigh it.
    """
    from .capability_benchmarks import (DEMONSTRATED, MEASURED_DOMINATES, PRIOR_GAP, PRIOR_GAP_MIN_ATTEMPTS,
                                        blend, expected_success, pseudo_count)
    tier = (override or {}).get("tiers", {}).get(kind)
    if tier is not None:
        return {'tier': tier, 'unproven': False, 'source': 'owner_override'}
    benchmarks = benchmarks if benchmarks is not None else getattr(table, 'benchmarks', None)
    prior = benchmarks.lookup(model, kind) if benchmarks is not None else None
    measured: list[tuple[int, int, float, int, float]] = []
    gaps, attempts_seen = [], 0
    for level in range(1, 6):
        bucket = profile.get('task_buckets', {}).get(f'{kind}:{level}', {})
        attempts = bucket.get('attempts', 0)
        if attempts >= 3:
            rate = bucket.get('success_rate') or 0
            if prior is not None:
                expected = expected_success(prior['tier'], level)
                posterior = blend(expected, pseudo_count(prior['confidence']), bucket.get('ok', round(rate * attempts)), attempts)
                if attempts >= PRIOR_GAP_MIN_ATTEMPTS and abs(rate - expected) >= PRIOR_GAP:
                    gaps.append(f'{kind}:{level}')
            else:
                posterior = rate
            good = posterior >= DEMONSTRATED and bucket.get('timeouts', 0) / attempts <= .2
            measured.append((level, max(1, level if good else level - 1), posterior, attempts, rate))
            attempts_seen = max(attempts_seen, attempts)
    detail: dict[str, Any] = {}
    if prior is not None:
        detail['benchmark'] = {key: prior[key] for key in ('family', 'tier', 'percentile', 'confidence', 'snapshot_id', 'sources')}
        if gaps:
            detail['prior_gap'] = gaps
    if measured:
        exact = next((tier for level, tier, _, _, _ in measured if level == difficulty), None)
        highest_measured = max(tier for _, tier, _, _, _ in measured)
        # Fallback to prior (owner table or benchmark) is only allowed when:
        # 1. ALL measured levels are strictly below the target difficulty
        #    (missing target is treated as missing info, not evidence), AND
        # 2. No measured bucket has a conclusive failure against the prior
        #    (many attempts below DEMONSTRATED + significant gap), AND
        # 3. No measured bucket at or above the target difficulty actually
        #    succeeded at raw measured rate — positive evidence at >= difficulty
        #    must count even on few attempts (raw rate, not blended posterior
        #    which dilutes high successes with prior pseudo-observations).
        all_below_target = all(level < difficulty for level, _, _, _, _ in measured)
        conclusive_failure = any(att >= MEASURED_DOMINATES and posterior < DEMONSTRATED
                                 for _, _, posterior, att, _ in measured)
        high_success = any(level >= difficulty and raw_rate >= DEMONSTRATED
                           for level, _, _, _, raw_rate in measured)
        if (prior is not None and all_below_target and not gaps
                and not conclusive_failure and not high_success):
            detail['measured_off_target'] = [level for level, _, _, _, _ in measured]
            entry = (table or {}).get(model, (table or {}).get(model.rsplit('/', 1)[-1], {}))
            tier = entry.get('tiers', {}).get(kind)
            if tier is not None:
                return {**detail, 'tier': tier, 'unproven': False, 'source': 'owner_table'}
            return {**detail, 'tier': prior['tier'], 'unproven': prior['confidence'] != 'high', 'source': 'benchmark'}
        source = 'measured' if prior is None or attempts_seen >= MEASURED_DOMINATES else 'measured_with_prior'
        if exact is not None:
            return {**detail, 'tier': exact, 'unproven': False, 'source': source}
        return {**detail, 'tier': highest_measured, 'unproven': False, 'source': source}
    entry = (table or {}).get(model, (table or {}).get(model.rsplit('/', 1)[-1], {}))
    tier = entry.get('tiers', {}).get(kind)
    if tier is not None:
        return {**detail, 'tier': tier, 'unproven': False, 'source': 'owner_table'}
    if prior is not None:
        # One source, or conflicting sources, still needs calibration before hard work.
        return {**detail, 'tier': prior['tier'], 'unproven': prior['confidence'] != 'high', 'source': 'benchmark'}
    # No name heuristic can establish competence; the prior remains unproven.
    return {'tier': 2, 'unproven': True, 'source': 'prior'}
