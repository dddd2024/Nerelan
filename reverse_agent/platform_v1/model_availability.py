"""Rare host-side availability observations; catalogs never prove entitlement."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import threading
import time
from typing import Any, Callable, Mapping

# "model is not supported": Copilot answers "The requested model is not supported."
UNAVAILABLE_MARKERS = ('model_not_supported', 'model is not supported', 'not allowed for user type', 'not_allowed', 'not-allowed', 'not allowed',
                       'model_not_found', 'invalid_api_key', 'authentication_error')
# A tool-less review call the upstream refused outright (model_review_transport). One
# request can be refused for its own sake, so the binding rests for an hour, not a day.
REVIEW_REFUSED_RE = re.compile(r"MODEL_UNAVAILABLE:(review_http_4\d\d)")
REVIEW_REFUSED_TTL_SECONDS = 3600


def native_owner_account(binding: Mapping[str, Any], connection: Mapping[str, Any]) -> bool:
    return (connection.get('auth_method') == 'external_cli_session'
            or binding.get('executor_id') in {'codex', 'claude_code'}
            or binding.get('model_id', '').lower().split('/', 1)[0] in {'codex', 'claude'})


# Provider-side overload is transient: not an entitlement problem, a quota limit
# or capability evidence. The same model or tier is retried after a backoff.
# Only capacity wording: generic "try again later" also ends usage-limit messages.
OVERLOAD_RE = re.compile(r"at capacity|overloaded|server (?:is )?busy|api_error_(?:503|529)"
                         r"|(?:http|status|error)[ _:]*529|503 service unavailable", re.I)
# Stored classes that are never re-read as overload from their detail text.
_NOT_OVERLOAD_CLASS = re.compile(r"limit|quota|rate|429|unavailable|refus|no_willing|policy", re.I)
OVERLOADED = "provider_overloaded"

# Recognize an account's rate-limit reply in an executor error or an OpenCode
# retry event, including Magpie's generic exit diagnostics and bilingual CN/EN RPM/TPM limits.
_PROVIDER_RATE_LIMIT_REPLY_RE = re.compile(
    r"^(?:too many requests\b|rate[ _-]limit(?:ed)?\b|(?:(?:http|status)[ :=]+)?429\b)"
    r"|status=429\b|\(429\b|\b(?:rpm|tpm)(?:/(?:rpm|tpm))? (?:exhausted|limit)"
    r"|\b(?:free\s+)?usage\s+limit\s+reached\b|\bout\s+of\s+its\s+allowance\b"
    r"|inference\s+exceeds\s+(?:tpm|rpm)(?:/(?:tpm|rpm))?\s+limit"
    r"|请求频率超限|频率超限|调用频率超限|并发(?:数)?超限",
    re.IGNORECASE,
)


# Windows reports these for a child killed from outside: TerminateProcess during
# shutdown or logoff (DBG_TERMINATE_PROCESS) and a closed console or Ctrl+C
# (STATUS_CONTROL_C_EXIT). The agent did not fail; the machine stopped it.
EXTERNAL_TERMINATION_EXIT_CODES = frozenset({0x40010004, 0xC000013A})
EXECUTOR_TERMINATED = "executor_terminated"
# A redeploy changed the host's code under an in-flight run: its durable resume
# refuses the old authority/planning identity (#1515). A host fault, not the model's.
HOST_VERSION_CHANGED = "host_version_changed"
OWNER_WINDOW_POOL_MISROUTE = "owner_window_binding_outside_confirmed_pool"
# Owner decision 2026-11-12 B: failures the host classifies as not the model's fault
# (a stall with no output, an external kill, a redeploy under the run). Goal retries
# and measured agent profiles both read this one definition.
# The connection to the provider broke, or a gateway in front of it answered 502/504
# (or a 52x edge error). Nothing judged the model: #1505 stopped for good on an
# ECONNRESET and spent max_retries on a 502 (2026-11-23).
UPSTREAM_CONNECTION = "network_provider_failure"
HOST_RETRY_CLASSES = frozenset({"executor_stalled", "server_stream_stalled", EXECUTOR_TERMINATED, HOST_VERSION_CHANGED,
                                UPSTREAM_CONNECTION})
_GATEWAY_STATUS = r"(?:502|504|52[0-7])"
# Only the host's own diagnostic head (the structured status, or the "(502: you can
# retry your request)" suffix a relay adds), never a status quoted in free prose.
_GATEWAY_DETAIL_RE = re.compile(
    rf"^opencode_nonzero:exit=\d+:executor_nonzero(?: name=\w+)?"
    rf"(?: status={_GATEWAY_STATUS}\b| message=.*\({_GATEWAY_STATUS}: you can retry your request\))", re.DOTALL)
_GATEWAY_CLASS_RE = re.compile(rf"(?:claude_code|codex)_turn_failed:api_error_{_GATEWAY_STATUS}")


def upstream_connection_failure(classification: str, detail: str) -> bool:
    """A broken provider connection or a gateway error: an upstream fault, not the model's."""
    cls = (classification or "").strip().lower()
    return (cls == UPSTREAM_CONNECTION or bool(_GATEWAY_CLASS_RE.fullmatch(cls))
            or (cls == "executor_nonzero" and bool(_GATEWAY_DETAIL_RE.match((detail or "").strip()))))


def external_termination(exit_code: int) -> bool:
    return (exit_code & 0xFFFFFFFF) in EXTERNAL_TERMINATION_EXIT_CODES


def provider_overloaded(value: str) -> bool:
    return bool(OVERLOAD_RE.search(value or ""))


def provider_rate_limit_reply(value: str) -> bool:
    text = (value or "").strip()
    if no_credits_error(text):
        return False
    return bool(_PROVIDER_RATE_LIMIT_REPLY_RE.search(text))


# Classifications whose failure_detail may still be inspected for provider-overload
# wording (empty/generic/executor-nonzero/legacy turn failures/host-retry classes).
# Model-judging classifications (e.g. deterministic_validation_failure, timeout,
# model_review_rejected, MODEL_REFUSED, functional check failures) are excluded so
# test or review output mentioning "overloaded" is never misread as provider overload (#1620).
_OVERLOAD_DETAIL_CLASSES = frozenset({
    "",
    "failed",
    "executor_error",
    "executor_nonzero",
    "role_failed",
    "coordinator_execution_error",
    "server_session_error",
    "codex_turn_failed",
    "claude_code_turn_failed",
    "codex_process_failed",
    "claude_code_process_failed",
    "network_provider_failure",
}) | HOST_RETRY_CLASSES
_OVERLOAD_DETAIL_PREFIXES = (
    "codex_turn_failed:",
    "claude_code_turn_failed:",
    "opencode_nonzero",
)


def transient_overload(classification: str, detail: str) -> bool:
    """Return True for explicit provider overload or allowlisted generic/host failures with overload detail.

    Model-judging classifications (such as deterministic_validation_failure, timeout,
    model_review_rejected, MODEL_REFUSED, or functional check failures) as well as
    rate/quota limits, entitlement errors, and refusals are never reclassified from
    detail text.
    """
    cls = (classification or "").strip().lower()
    if cls.startswith(OVERLOADED):
        return True
    if _NOT_OVERLOAD_CLASS.search(cls):
        return False
    if cls not in _OVERLOAD_DETAIL_CLASSES and not cls.startswith(_OVERLOAD_DETAIL_PREFIXES):
        return False
    from .codex_protocol import usage_limit_hit
    return provider_overloaded(detail) and not usage_limit_hit(detail or "")


def availability_error(value: str) -> str | None:
    text = (value or '').lower()
    return next((marker.replace(' ', '_') for marker in UNAVAILABLE_MARKERS if marker in text or marker.replace(' ', '_') in text), None)


# A billing answer that says the account has no credits to spend is not a
# transient state: the upstream stays unpaid until somebody buys credits. The
# binding is UNAVAILABLE for a week, so routing stops offering that upstream's
# paid models instead of re-paying for the same refusal every few hours
# (#1525).
NO_CREDITS = 'no_credits'
NO_CREDITS_TTL_SECONDS = 7 * 86400
# Wording that names an absent or spent credit balance and asks for a purchase.
_NO_CREDITS_RE = re.compile(
    r"\b(?:insufficient|exhausted|depleted|spent|exceeded|empty|lacking)\s+credits?\b"
    r"|\bcredits?\s+(?:are\s+|is\s+|have\s+been\s+|has\s+been\s+)?(?:exhausted|depleted|exceeded|used\s+up|spent|gone|empty)\b"
    r"|\b(?:no|without)\s+credits?\s+(?:remaining|left|available)\b"
    r"|\b(?:out\s+of|ran\s+out\s+of|not\s+enough)\s+credits?\b"
    r"|\bnever\s+purchased\s+credits?\b"
    r"|\b(?:insufficient|exhausted|depleted)\s+balance\b"
    r"|\bbalance\s+(?:is\s+|has\s+been\s+)?(?:insufficient|exhausted|depleted|too\s+low)\b"
    r"|\bpurchase\s+(?:add[-\s]?on\s+)?(?:packs?|credits?)\b",
    re.IGNORECASE,
)


def no_credits_error(value: str) -> str | None:
    """``NO_CREDITS`` when a provider answer says the account has no credits left.

    This is a billing state, not a rate limit and not an entitlement probe: the
    same upstream answers again until credits are bought, so the binding is held
    UNAVAILABLE instead of being retried on every dispatch.
    """
    text = value or ''
    return NO_CREDITS if _NO_CREDITS_RE.search(text) else None


def probe_failure_observation(*, now: float, status_code: int | None = None,
                              error: str = '') -> dict[str, Any]:
    """Classify a failed background probe so 402/404/403/400 stop tight re-probing."""
    if status_code == 402 or no_credits_error(error):
        return observation(now=now, state='UNAVAILABLE', reason=NO_CREDITS,
                           ttl_seconds=NO_CREDITS_TTL_SECONDS)
    marker = availability_error(error)
    if marker:
        return observation(now=now, state='UNAVAILABLE', reason=marker, ttl_seconds=86400)
    lowered = (error or '').lower()
    if status_code == 404 or 'not_found_error' in lowered:
        return observation(now=now, state='UNAVAILABLE', reason='model_not_found', ttl_seconds=86400)
    if status_code in (401, 403) or 'cloudflare' in lowered or 'error-1010' in lowered:
        reason = f'http_{status_code}' if isinstance(status_code, int) else 'http_403'
        return observation(now=now, state='UNAVAILABLE', reason=reason, ttl_seconds=86400)
    if status_code == 400 or 'invalid_request_error' in lowered:
        return observation(now=now, state='UNAVAILABLE', reason='probe_invalid_request', ttl_seconds=86400)
    if status_code == 429 or provider_rate_limit_reply(error):
        return observation(now=now, state='TRANSIENT', reason='rate_limited', ttl_seconds=1800)
    return observation(now=now, success=False, error=error)


def observation(*, now: float, success: bool = False, error: str = '',
                state: str | None = None, reason: str | None = None,
                ttl_seconds: float | None = None) -> dict[str, Any]:
    marker = None if success else availability_error(error)
    if success:
        resolved_state, resolved_reason = 'AVAILABLE', 'verified_request'
    elif state is not None:
        resolved_state = state
        resolved_reason = reason or 'transient_error'
    else:
        resolved_state = 'UNAVAILABLE' if marker else 'TRANSIENT'
        resolved_reason = marker or 'transient_error'
    if ttl_seconds is None:
        # A verified request and a durable unavailability last a day; an
        # unexplained failure lasts minutes.
        ttl_seconds = 86400 if success or marker else 300
    return {'state': resolved_state, 'reason': resolved_reason,
            'observed_at': now, 'expires_at': now + ttl_seconds}


class AvailabilityCache:
    """Sanitized daily cache, keyed by public pairing + endpoint configuration.

    A global per-host minute limit bounds first-time catalog exploration. The
    callback receives public metadata and must use the host relay/executor; no
    keys or upstream response text enter this cache.
    """
    def __init__(self, path: Path | None = None):
        self.path = path
        self.entries: dict[str, Any] = {}
        self.next_probe = 0.
        self.lock = threading.RLock()
        if path:
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    self.entries = {key: value for key, value in data.items()
                                    if isinstance(value, dict) and value.get("state") in {"AVAILABLE", "UNAVAILABLE", "TRANSIENT"}
                                    and all(type(value.get(field)) in (int, float) and math.isfinite(value[field])
                                            for field in ("observed_at", "expires_at"))}
            except (OSError, ValueError):
                pass

    @staticmethod
    def key(binding: Mapping[str, Any], connection: Mapping[str, Any]) -> str:
        identity = [binding.get(k) for k in ('binding_id', 'model_id', 'executor_id', 'native_endpoint')]
        identity += [connection.get(k) for k in ('connection_id', 'base_url', 'auth_method')]
        return hashlib.sha256(json.dumps(identity).encode()).hexdigest()

    def remember(self, binding: Mapping[str, Any], connection: Mapping[str, Any], result: Mapping[str, Any]) -> None:
        with self.lock:
            key = self.key(binding, connection)
            result = dict(result)
            previous = self.entries.get(key, {})
            if result.get("state") == "TRANSIENT":
                if previous.get("state") == "AVAILABLE":
                    result["verified_until"] = previous.get("expires_at", 0)
                elif previous.get("state") == "TRANSIENT":
                    result["verified_until"] = previous.get("verified_until", 0)
            self.entries[key] = result
            if self.path:
                from ..model_access.store import _write_atomic
                _write_atomic(json.dumps(self.entries, allow_nan=False).encode('utf-8'), self.path)

    def check(self, binding: Mapping[str, Any], connection: Mapping[str, Any], *,
              probe: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
              allow_probe: bool = False, now: float | None = None,
              recent_success: float | None = None) -> dict[str, Any]:
        now = time.time() if now is None else now
        with self.lock:
            entry = self.entries.get(self.key(binding, connection), {})
            # A more recent successful task supersedes an earlier rejection.
            if recent_success is not None and 0 <= now - recent_success < 86400 and recent_success > entry.get('observed_at', 0):
                entry = observation(now=recent_success, success=True)
                self.remember(binding, connection, entry)
            if entry.get('observed_at', 0) > now:
                return {'state': 'UNKNOWN', 'reason': 'clock_discontinuity'}
            if entry.get('state') == 'TRANSIENT' and entry.get('verified_until', 0) > now and entry.get('expires_at', 0) <= now:
                return dict(entry, state='AVAILABLE', penalty=0., reason='recent_success', expires_at=entry['verified_until'])
            if entry.get('expires_at', 0) > now:
                if entry.get('state') == 'TRANSIENT' and entry.get('verified_until', 0) > now:
                    return dict(entry, state='AVAILABLE', penalty=.5)
                return dict(entry)
            owner_account = native_owner_account(binding, connection)
            if not allow_probe or owner_account or probe is None or now < self.next_probe:
                return {'state': 'UNKNOWN', 'reason': 'unverified'}
            self.next_probe = now + 60
            try:
                value = probe(binding)
                if value.get('ok') is True:
                    result = observation(now=now, success=True)
                else:
                    result = probe_failure_observation(
                        now=now,
                        status_code=value.get('status_code'),
                        error=str(value.get('error', '')),
                    )
            except Exception:
                result = observation(now=now, error='transient')
            self.remember(binding, connection, result)
            return result
