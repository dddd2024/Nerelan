"""Benchmark-seeded capability priors, refined by real use (issue 1264).

A versioned snapshot ``capability_benchmarks.json`` lives beside the model setup
state. It names model families (exact ids plus provider aliases) and per-benchmark
scores, each tied to a named, dated source page. From it this module derives a
per-kind tier prior with a confidence, and blends that prior with measured runs
as pseudo-observations. Nothing here guesses from model-name fragments, and
nothing runs on import: the importer fetches only on an explicit command, and
every snapshot change is shown as a diff that the Owner must confirm by digest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import urlsplit
from urllib.request import Request

VERSION = 1
SNAPSHOT_FILE = 'capability_benchmarks.json'
CANDIDATE_FILE = 'capability_benchmarks.candidate.json'
KINDS = frozenset({'code', 'analysis', 'writing', 'research_design', 'review'})
_REASONING = ('analysis', 'research_design', 'review')
# Review is code plus reasoning; writing is human-preference text only.
BENCHMARK_KINDS: dict[str, tuple[str, ...]] = {
    'swe_bench_verified': ('code', 'review'),
    'swe_bench_pro': ('code', 'review'),
    'deepswe': ('code', 'review'),
    'aider_polyglot': ('code', 'review'),
    'livecodebench': ('code', 'review'),
    'terminal_bench': ('code', 'review'),
    'gpqa_diamond': _REASONING,
    'hle': _REASONING,
    'aime': ('analysis', 'research_design'),
    'math': ('analysis', 'research_design'),
    'arena_text': ('writing',),
}
AGREEMENT_BAND = .2       # max percentile spread across sources for high confidence
PSEUDO_COUNT = 3          # prior weight, in observations, at high confidence
LOW_CONFIDENCE_PSEUDO_COUNT = 1
MEASURED_DOMINATES = 10   # real attempts after which the record says "measured"
DEMONSTRATED = .8
PRIOR_GAP = .4            # |prior - measured| success gap that flags the entry
PRIOR_GAP_MIN_ATTEMPTS = 5
MAX_FETCH_BYTES = 2_000_000
_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')

# Families the snapshot must cover (issue 1264 item 6). Scores are compiled from
# linked public pages and reviewed as a PR; an empty list means needs_benchmark.
SEED_FAMILIES: dict[str, list[str]] = {
    'deepseek-v4.1-flash': ['deepseek-v4.1-flash', 'deepseek-v4.1-flash-free', 'deepseek-v4.1-flash-sg', 'auto-deepseek-v4-1-flash', 'sn-deepseek-v4-1-flash'],
    'deepseek-v4-pro': ['deepseek-v4-pro', 'workbuddy/deepseek-v4-pro', 'trae-cn/deepseek-v4-pro-official'],
    'glm-5.3': ['glm-5.3', 'workbuddy/glm-5.3', 'auto-glm-5-3', 'sn-glm-5-3', 'glm-5.3-max'],
    'glm-5.2': ['glm-5.2', 'workbuddy/glm-5.2', 'workbuddy-ai/glm-5.2', 'z-ai/glm-5.2', 'auto-glm-5-2', 'glm-5.2-max'],
    'kimi-k3': ['kimi-k3', 'auto-kimi-k3', 'sn-kimi-k3'],
    'kimi-k2.7-code': ['kimi-k2.7-code'],
    'minimax-m3': ['minimax-m3', 'auto-minimax-m3'],
    'doubao-seed-code': ['doubao-seed-code'],
    'gpt-6.1-sol': ['gpt-6.1-sol', 'auto-gpt-6-1-sol'],
    'gpt-5.6-luna': ['gpt-5.6-luna'],
    'gpt-4.1': ['gpt-4.1', 'copilot/gpt-4.1'],
    'claude-opus': ['claude-opus'],
    'claude-sonnet': ['claude-sonnet'],
    'mistral-medium-3.5': ['mistral-medium-3.5'],
    'codestral': ['codestral'],
    'agnes-3.0': ['agnes-3.0'],
}


def seed_snapshot(snapshot_id: str = 'seed') -> dict[str, Any]:
    return {'version': VERSION, 'snapshot_id': snapshot_id,
            'families': {family: {'aliases': list(aliases), 'scores': []}
                         for family, aliases in SEED_FAMILIES.items()}}


def _identity(model: str) -> str:
    return model.strip().lower()


def validate_snapshot(data: Any) -> dict[str, Any]:
    """Return the snapshot unchanged, or raise ``invalid_capability_benchmarks``."""
    def bad() -> ValueError:
        return ValueError('invalid_capability_benchmarks')
    if (not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != VERSION
            or not isinstance(data.get('snapshot_id'), str) or not data['snapshot_id']
            or not isinstance(data.get('families'), dict)):
        raise bad()
    owners: dict[str, str] = {}
    for family, entry in data['families'].items():
        if (not isinstance(family, str) or family != _identity(family) or not family
                or not isinstance(entry, dict) or not isinstance(entry.get('aliases'), list)
                or not isinstance(entry.get('scores'), list)):
            raise bad()
        if not all(isinstance(alias, str) for alias in entry['aliases']):
            raise bad()
        for alias in {family, *entry['aliases']}:
            if alias != _identity(alias) or not alias:
                raise bad()
            # One provider id must never resolve to two families.
            if owners.setdefault(alias, family) != family:
                raise bad()
        for row in entry['scores']:
            if (not isinstance(row, dict) or row.get('benchmark') not in BENCHMARK_KINDS
                    or type(row.get('score')) not in (int, float) or not math.isfinite(row['score'])
                    or not all(isinstance(row.get(key), str) and row[key] for key in ('source', 'url', 'retrieved_at'))
                    or not isinstance(row.get('variant', ''), str)
                    or urlsplit(row['url']).scheme != 'https' or not _DATE.fullmatch(row['retrieved_at'])):
                raise bad()
            try:
                date.fromisoformat(row['retrieved_at'])
            except ValueError as exc:
                raise bad() from exc
    return data


def read_snapshot(path: Path) -> dict[str, Any] | None:
    try:
        text = Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ValueError('invalid_capability_benchmarks') from exc
    try:
        return validate_snapshot(json.loads(text))
    except ValueError as exc:
        raise ValueError('invalid_capability_benchmarks') from exc


def alias_index(snapshot: Mapping[str, Any]) -> dict[str, str]:
    return {alias: family for family, entry in snapshot['families'].items()
            for alias in (family, *entry['aliases'])}


def resolve_family(model: str, index: Mapping[str, str]) -> str | None:
    """Exact id, then the id without its provider namespace. Never a substring."""
    model = _identity(model)
    return index.get(model) or index.get(model.rsplit('/', 1)[-1])


def _percentile(value: float, values: Sequence[float]) -> float:
    less = sum(v < value for v in values)
    equal = sum(v == value for v in values)
    return (less + (equal - 1) / 2) / (len(values) - 1)


def tier_for(percentile: float) -> int:
    return min(5, 1 + int(percentile * 5))


def compute_priors(snapshot: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Per family and kind: tier 1..5, percentile, confidence and cited sources.

    Each (benchmark, source) column is ranked across the families it covers; a
    column covering one family carries no comparison and is ignored. A source's
    kind score is the mean of its column percentiles, and the kind percentile is
    the median across sources. Confidence is high only when two or more sources
    agree within ``AGREEMENT_BAND``.
    """
    columns: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = {}
    for family, entry in snapshot['families'].items():
        for row in entry['scores']:
            columns.setdefault((row['benchmark'], row['source']), {}).setdefault(family, []).append(row)
    per_source: dict[str, dict[str, dict[str, list[Any]]]] = {}
    for (benchmark, source), families in columns.items():
        if len(families) < 2:
            continue
        values = {family: median(r['score'] for r in rows) for family, rows in families.items()}
        for family, value in values.items():
            pct = _percentile(value, list(values.values()))
            for kind in BENCHMARK_KINDS[benchmark]:
                cell = per_source.setdefault(family, {}).setdefault(kind, {}).setdefault(source, [[], []])
                cell[0].append(pct)
                cell[1].extend(families[family])
    priors: dict[str, dict[str, Any]] = {}
    for family, kinds in per_source.items():
        for kind, sources in kinds.items():
            scores = {source: sum(cell[0]) / len(cell[0]) for source, cell in sources.items()}
            pct = median(scores.values())
            agree = len(scores) >= 2 and max(scores.values()) - min(scores.values()) <= AGREEMENT_BAND
            priors.setdefault(family, {})[kind] = {
                'tier': tier_for(pct), 'percentile': round(pct, 4),
                'confidence': 'high' if agree else 'low',
                'snapshot_id': snapshot['snapshot_id'],
                'sources': sorted(({'source': source, 'percentile': round(scores[source], 4),
                                    'evidence': sorted({(r['benchmark'], r['url'], r['retrieved_at'], r.get('variant', ''))
                                                        for r in sources[source][1]})}
                                   for source in scores), key=lambda s: s['source'])}
    for prior in priors.values():
        for kind in prior.values():
            for source in kind['sources']:
                source['evidence'] = [dict(zip(('benchmark', 'url', 'retrieved_at', 'variant'), row))
                                      for row in source['evidence']]
    return priors


class BenchmarkPriors:
    """Resolved priors keyed by model id through the alias map."""

    def __init__(self, snapshot: Mapping[str, Any]):
        self.snapshot_id = snapshot['snapshot_id']
        self._index = alias_index(snapshot)
        self._priors = compute_priors(snapshot)

    def lookup(self, model: str, kind: str) -> dict[str, Any] | None:
        family = resolve_family(model, self._index)
        prior = self._priors.get(family or '', {}).get(kind)
        return None if prior is None else {'family': family, **prior}

    def family(self, model: str) -> str | None:
        return resolve_family(model, self._index)


def read_benchmark_priors(state_path: Path | None) -> BenchmarkPriors | None:
    if state_path is None:
        return None
    snapshot = read_snapshot(Path(state_path).with_name(SNAPSHOT_FILE))
    return None if snapshot is None else BenchmarkPriors(snapshot)


def expected_success(tier: int, difficulty: int) -> float:
    """Success rate a tier prior predicts at a difficulty."""
    return .85 if tier >= difficulty else max(.1, .85 - .25 * (difficulty - tier))


def pseudo_count(confidence: str) -> int:
    return PSEUDO_COUNT if confidence == 'high' else LOW_CONFIDENCE_PSEUDO_COUNT


def blend(prior_rate: float, k: float, ok: int, attempts: int) -> float:
    """Beta-style posterior: the prior counts as ``k`` observations of ``prior_rate``."""
    return (k * prior_rate + ok) / (k + attempts) if k + attempts else prior_rate


def needs_benchmark(model_ids: Iterable[str], snapshot: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Catalog models with no family or no scored family: unproven until covered."""
    index = alias_index(snapshot) if snapshot else {}
    out = []
    for model in sorted({_identity(m) for m in model_ids if isinstance(m, str) and m.strip()}):
        family = resolve_family(model, index)
        if family is None or not snapshot['families'][family]['scores']:
            out.append({'model_id': model, 'family': family, 'status': 'needs_benchmark', 'unproven': True})
    return out


# --- importer -----------------------------------------------------------------

def _validate_spec(spec: Mapping[str, Any]) -> None:
    url = urlsplit(spec.get('url', '')) if isinstance(spec.get('url'), str) else None
    if (url is None or url.scheme != 'https' or not url.hostname or url.username is not None
            or url.password is not None or spec.get('format') not in {'json_rows', 'csv'}
            or not isinstance(spec.get('source'), str) or not spec['source']
            or not isinstance(spec.get('model_field'), str)
            or not isinstance(spec.get('score_fields'), dict) or not spec['score_fields']
            or any(not isinstance(k, str) or v not in BENCHMARK_KINDS for k, v in spec['score_fields'].items())
            or not isinstance(spec.get('variant_field', ''), str)
            or not isinstance(spec.get('rows_field', 'rows'), str)
            or 'headers' in spec):
        raise ValueError('invalid_benchmark_source')


def parse_source(payload: bytes | str, spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Parse a machine-readable leaderboard (recorded fixture or fetched bytes)."""
    _validate_spec(spec)
    text = payload.decode('utf-8') if isinstance(payload, bytes) else payload
    if spec['format'] == 'json_rows':
        data = json.loads(text)
        rows = data.get(spec.get('rows_field', 'rows')) if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise ValueError('invalid_benchmark_payload')
    else:
        rows = list(csv.DictReader(io.StringIO(text)))
    out = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(spec['model_field']), str):
            continue
        for field, benchmark in spec['score_fields'].items():
            raw = row.get(field)
            try:
                score = float(raw) if isinstance(raw, (int, float, str)) and not isinstance(raw, bool) else None
            except ValueError:
                score = None
            if score is None or not math.isfinite(score):
                continue
            variant = row.get(spec['variant_field']) if spec.get('variant_field') else ''
            out.append({'model': row[spec['model_field']].strip(), 'benchmark': benchmark, 'score': score,
                        'variant': variant if isinstance(variant, str) else ''})
    return out


def fetch_source(spec: Mapping[str, Any], *, opener: Callable[..., Any] | None = None,
                 timeout: float = 10.0) -> bytes:
    """One bounded, credential-free GET through ``http_safe`` (no redirects)."""
    _validate_spec(spec)
    from reverse_agent.model_access import http_safe
    request = Request(spec['url'], headers={'Accept': 'application/json, text/csv'}, method='GET')
    with (opener or http_safe.urlopen)(request, timeout=timeout) as response:
        status = response.getcode()
        if status is not None and not 200 <= status < 300:
            raise ValueError('benchmark_source_http_error')
        body = response.read(MAX_FETCH_BYTES + 1)
    if len(body) > MAX_FETCH_BYTES:
        raise ValueError('benchmark_source_too_large')
    return body


def build_candidate(current: Mapping[str, Any], spec: Mapping[str, Any], rows: Sequence[Mapping[str, Any]],
                    *, retrieved_at: str, snapshot_id: str) -> tuple[dict[str, Any], list[str]]:
    """Replace this source's scores for matched families; report unmatched names."""
    candidate = json.loads(json.dumps(validate_snapshot(dict(current))))
    index = alias_index(candidate)
    matched: dict[str, list[dict[str, Any]]] = {}
    unmatched = set()
    for row in rows:
        family = resolve_family(row['model'], index)
        if family is None:
            unmatched.add(row['model'])
            continue
        matched.setdefault(family, []).append({'benchmark': row['benchmark'], 'score': row['score'],
            'source': spec['source'], 'url': spec['url'], 'retrieved_at': retrieved_at,
            'variant': row.get('variant') or row['model']})
    # A refresh replaces the whole source: models it no longer lists lose its rows.
    for family, entry in candidate['families'].items():
        entry['scores'] = [r for r in entry['scores'] if r['source'] != spec['source']] + matched.get(family, [])
    candidate['snapshot_id'] = snapshot_id
    return validate_snapshot(candidate), sorted(unmatched)


def diff_snapshots(old: Mapping[str, Any] | None, new: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Every difference that changes the digest: snapshot id, families, aliases and full score rows."""
    old = old or {'snapshot_id': None, 'families': {}}
    changes: list[dict[str, Any]] = []
    if old['snapshot_id'] != new['snapshot_id']:
        changes.append({'snapshot_id_old': old['snapshot_id'], 'snapshot_id_new': new['snapshot_id']})

    def rows(entry: Mapping[str, Any] | None) -> Counter[str]:
        # A multiset: a duplicated row also changes the digest.
        return Counter(json.dumps(r, sort_keys=True) for r in (entry or {}).get('scores', []))
    for family in sorted(old['families'].keys() | new['families'].keys()):
        before, after = old['families'].get(family), new['families'].get(family)
        if before is None or after is None:
            changes.append({'family': family, 'family_change': 'added' if before is None else 'removed',
                            'aliases': sorted((after or before)['aliases'])})
        elif before['aliases'] != after['aliases']:
            changes.append({'family': family, 'aliases_old': before['aliases'], 'aliases_new': after['aliases']})
        old_rows, new_rows = rows(before), rows(after)
        changes += [{'family': family, 'removed': json.loads(key)} for key in sorted((old_rows - new_rows).elements())]
        changes += [{'family': family, 'added': json.loads(key)} for key in sorted((new_rows - old_rows).elements())]
    return changes


def digest(snapshot: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def stage_candidate(state_dir: Path, candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Write the candidate beside the state and return the diff to show the Owner."""
    validate_snapshot(dict(candidate))
    state_dir = Path(state_dir)
    (state_dir / CANDIDATE_FILE).write_text(json.dumps(candidate, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return {'digest': digest(candidate), 'changes': diff_snapshots(read_snapshot(state_dir / SNAPSHOT_FILE), candidate)}


def adopt_candidate(state_dir: Path, confirm: str) -> dict[str, Any]:
    """Promote the staged candidate only when the Owner confirms its exact digest."""
    state_dir = Path(state_dir)
    candidate = read_snapshot(state_dir / CANDIDATE_FILE)
    if candidate is None:
        raise ValueError('no_candidate')
    if digest(candidate) != confirm:
        raise ValueError('candidate_digest_mismatch')
    (state_dir / SNAPSHOT_FILE).write_text(json.dumps(candidate, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (state_dir / CANDIDATE_FILE).unlink()
    return {'adopted': confirm, 'snapshot_id': candidate['snapshot_id']}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Benchmark capability snapshot (Owner command)')
    sub = parser.add_subparsers(dest='command', required=True)
    imp = sub.add_parser('import', help='fetch one source, stage a candidate and print the diff')
    imp.add_argument('--state-dir', required=True, type=Path)
    imp.add_argument('--spec', required=True, type=Path, help='JSON source spec')
    imp.add_argument('--fixture', type=Path, help='parse a recorded payload instead of fetching')
    imp.add_argument('--retrieved-at', default=date.today().isoformat())
    stage = sub.add_parser('stage', help='stage a reviewed snapshot file and print the diff')
    stage.add_argument('--state-dir', required=True, type=Path)
    stage.add_argument('--snapshot', required=True, type=Path)
    adopt = sub.add_parser('adopt', help='use the staged candidate')
    adopt.add_argument('--state-dir', required=True, type=Path)
    adopt.add_argument('--confirm', required=True, help='digest printed by import/stage')
    args = parser.parse_args(argv)
    try:
        if args.command == 'adopt':
            result = adopt_candidate(args.state_dir, args.confirm)
        elif args.command == 'stage':
            result = stage_candidate(args.state_dir, validate_snapshot(json.loads(args.snapshot.read_text(encoding='utf-8'))))
        else:
            spec = json.loads(args.spec.read_text(encoding='utf-8'))
            payload = args.fixture.read_bytes() if args.fixture else fetch_source(spec)
            current = read_snapshot(args.state_dir / SNAPSHOT_FILE) or seed_snapshot()
            candidate, unmatched = build_candidate(current, spec, parse_source(payload, spec),
                                                   retrieved_at=args.retrieved_at,
                                                   snapshot_id=f"{spec['source']}@{args.retrieved_at}")
            result = {**stage_candidate(args.state_dir, candidate), 'unmatched_models': unmatched}
    except (OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc) if isinstance(exc, ValueError) else 'io_error'}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
