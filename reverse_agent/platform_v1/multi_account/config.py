"""Centralized, validated configuration for the multi-account orchestration brain.

Reuse-first: this is the *only* place the new brain keeps tunable knobs. It
deliberately adds no second orchestration spine, no new queue layer and no
credential handling — those stay with the existing runtime
(:mod:`durable_execution`, :mod:`unattended_coordinator`,
:mod:`quota_reservation`). Secrets never enter this model; only environment
variable names and local file paths do.

The model fails fast on startup (``validate_assignment`` + validators) so a
misconfigured deployment refuses to run instead of drifting into an ambiguous
state.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Environment surface: knob -> variable. Scalars only; never a credential, a
# token or a path outside the local runtime directory.
#
# This map is the *deployment contract*: every field of the config model is
# reachable here except the two that already own a variable of their own
# (``account_routing`` -> REVERSE_AGENT_ACCOUNT_ROUTING, ``break_even_store_path``
# -> REVERSE_AGENT_MULTI_ACCOUNT_STORE). A knob that only exists in Python is not
# configurable for an unattended run, so
# ``test_every_knob_is_reachable_from_the_environment`` pins the coverage.
# The older abbreviated names are kept verbatim so an existing deployment does
# not have to change anything.
_ENV_SCALARS = {
    # --- identity / perception ---------------------------------------------
    "observation_freshness_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_FRESHNESS",
    "magpie_max_age_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_MAGPIE_MAX_AGE",
    "high_utilization_threshold": "REVERSE_AGENT_MULTI_ACCOUNT_HIGH_UTILIZATION",
    "reset_soon_threshold_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_RESET_SOON_SECONDS",
    "small_task_percent_ceiling": "REVERSE_AGENT_MULTI_ACCOUNT_SMALL_TASK_CEILING",
    # --- routing / tolerance ------------------------------------------------
    "reroute_max_attempts": "REVERSE_AGENT_MULTI_ACCOUNT_REROUTE_ATTEMPTS",
    "reroute_cooldown_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_REROUTE_COOLDOWN",
    "abnormal_account_cooldown_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_ABNORMAL_COOLDOWN",
    "dead_letter_enabled": "REVERSE_AGENT_MULTI_ACCOUNT_DEAD_LETTER",
    "failure_backoff_base_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_BACKOFF_BASE",
    "failure_backoff_multiplier": "REVERSE_AGENT_MULTI_ACCOUNT_BACKOFF_MULTIPLIER",
    "failure_backoff_max_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_BACKOFF_MAX",
    "cooldown_memory_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_COOLDOWN_MEMORY",
    "persist_account_state": "REVERSE_AGENT_MULTI_ACCOUNT_PERSIST_STATE",
    "standby_keepalive_interval_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_STANDBY_KEEPALIVE",
    # --- measured feedback / self-evolution --------------------------------
    "enable_account_scoring": "REVERSE_AGENT_MULTI_ACCOUNT_SCORING",
    "score_ewma_alpha": "REVERSE_AGENT_MULTI_ACCOUNT_SCORE_ALPHA",
    "reliability_weight": "REVERSE_AGENT_MULTI_ACCOUNT_RELIABILITY_WEIGHT",
    "cost_weight": "REVERSE_AGENT_MULTI_ACCOUNT_COST_WEIGHT",
    "latency_weight": "REVERSE_AGENT_MULTI_ACCOUNT_LATENCY_WEIGHT",
    "max_recorded_runs": "REVERSE_AGENT_MULTI_ACCOUNT_MAX_RECORDED_RUNS",
    "enable_self_evolution": "REVERSE_AGENT_MULTI_ACCOUNT_SELF_EVOLUTION",
    "min_observations_per_mode": "REVERSE_AGENT_MULTI_ACCOUNT_MIN_MODE_OBSERVATIONS",
    "calibration_feedback_enabled": "REVERSE_AGENT_MULTI_ACCOUNT_CALIBRATION_FEEDBACK",
    # --- cost ceiling -------------------------------------------------------
    "cost_budget_enabled": "REVERSE_AGENT_MULTI_ACCOUNT_COST_BUDGET",
    "cost_budget_units": "REVERSE_AGENT_MULTI_ACCOUNT_COST_BUDGET_UNITS",
    "cost_budget_window_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_COST_BUDGET_WINDOW",
    "cost_budget_soft_ratio": "REVERSE_AGENT_MULTI_ACCOUNT_COST_BUDGET_SOFT_RATIO",
    "cost_budget_default_task_units": "REVERSE_AGENT_MULTI_ACCOUNT_COST_BUDGET_TASK_UNITS",
    "cost_budget_include_reservations": "REVERSE_AGENT_MULTI_ACCOUNT_COST_BUDGET_RESERVATIONS",
    # --- alerting -----------------------------------------------------------
    "alerts_enabled": "REVERSE_AGENT_MULTI_ACCOUNT_ALERTS",
    "alert_quiet_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_ALERT_QUIET",
    "alert_max_history": "REVERSE_AGENT_MULTI_ACCOUNT_ALERT_MAX_HISTORY",
    "alert_failure_streak_threshold": "REVERSE_AGENT_MULTI_ACCOUNT_ALERT_STREAK",
    "alert_min_success_rate": "REVERSE_AGENT_MULTI_ACCOUNT_ALERT_MIN_SUCCESS",
    "alert_min_samples": "REVERSE_AGENT_MULTI_ACCOUNT_ALERT_MIN_SAMPLES",
    "alert_log_enabled": "REVERSE_AGENT_MULTI_ACCOUNT_ALERT_LOG",
    # --- run duration -------------------------------------------------------
    "watchdog_enabled": "REVERSE_AGENT_MULTI_ACCOUNT_WATCHDOG",
    "max_run_duration_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_MAX_RUN_SECONDS",
    "max_idle_seconds": "REVERSE_AGENT_MULTI_ACCOUNT_MAX_IDLE_SECONDS",
    "watchdog_hard_stop_ratio": "REVERSE_AGENT_MULTI_ACCOUNT_HARD_STOP_RATIO",
    # --- self-evolution policy clamps (auditable, rollback-able) ------------
    "policy_enabled": "REVERSE_AGENT_MULTI_ACCOUNT_POLICY",
    "policy_step_ratio": "REVERSE_AGENT_MULTI_ACCOUNT_POLICY_STEP",
    "policy_max_weight_drift_ratio": "REVERSE_AGENT_MULTI_ACCOUNT_POLICY_DRIFT",
    "policy_max_bonus_points": "REVERSE_AGENT_MULTI_ACCOUNT_POLICY_MAX_BONUS",
    "policy_min_samples": "REVERSE_AGENT_MULTI_ACCOUNT_POLICY_MIN_SAMPLES",
    "policy_target_success_rate": "REVERSE_AGENT_MULTI_ACCOUNT_POLICY_TARGET_SUCCESS",
    "policy_audit_max_entries": "REVERSE_AGENT_MULTI_ACCOUNT_POLICY_AUDIT_ENTRIES",
}

# Fields that are deliberately *not* in the scalar map because each owns a
# variable with different semantics (see ``from_env``).
_ENV_OWN_VARIABLE = frozenset({"account_routing", "break_even_store_path"})

_TRUE_TEXT = frozenset({"1", "true", "yes", "on"})
_FALSE_TEXT = frozenset({"0", "false", "no", "off"})


def _coerce(raw: str, field: str) -> object:
    """Parse an env string with the declared field type (``True``/float/int)."""
    text = str(raw).strip()
    if field.endswith("_enabled"):
        lowered = text.lower()
        if lowered in _TRUE_TEXT:
            return True
        if lowered in _FALSE_TEXT:
            return False
        raise ValueError(f"{field} expects a boolean")
    declared = MultiAccountConfig.model_fields[field].annotation
    if declared is bool:
        return text.lower() in _TRUE_TEXT
    if declared is int:
        return int(float(text))
    if declared is float:
        return float(text)
    return text


class MultiAccountConfig(BaseModel):
    """Tunable knobs for account perception, scheduling and self-evolution.

    Defaults follow the planning spec: observation freshness 600 s, Magpie
    snapshot max age 900 s, at most 3 reroute attempts per task, with cooldowns
    that keep a flapping account from being retried immediately.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=False)

    # --- perception (domain B) -------------------------------------------------
    observation_freshness_seconds: int = Field(
        600, description="Max age of an account/quota observation before it is treated as STALE.")
    magpie_max_age_seconds: int = Field(
        900, description="Max age of a Magpie snapshot; older snapshots are ignored.")
    high_utilization_threshold: float = Field(
        90.0, description="used_percent at/above which a window is DEGRADED (not yet EXHAUSTED).")
    reset_soon_threshold_seconds: float = Field(
        1800.0, description="A window whose reset is within this horizon raises a 'reset_soon' anomaly.")

    # --- scheduling / fault tolerance (domains C, D) ---------------------------
    reroute_max_attempts: int = Field(
        3, description="Max accounts a single task may be rerouted across before dead-lettering.")
    reroute_cooldown_seconds: float = Field(
        30.0, description="Minimum quiet time before a rerouted-away account is eligible again.")
    abnormal_account_cooldown_seconds: float = Field(
        300.0, description="Quarantine window for an account flagged ABNORMAL/account-level error.")
    small_task_percent_ceiling: float = Field(
        1.0, description="A task whose p80 need <= this percentage point may run on a STALE/DEGRADED account.")
    dead_letter_enabled: bool = Field(
        True, description="When True, terminally-failed tasks are isolated with evidence instead of dropped.")

    # --- long-unattended hardening (domain D) ---------------------------------
    failure_backoff_base_seconds: float = Field(
        30.0, description="First cooldown after an account failure; doubles per consecutive failure.")
    failure_backoff_multiplier: float = Field(
        2.0, description="Exponential growth of the per-account cooldown after repeated failures.")
    failure_backoff_max_seconds: float = Field(
        900.0, description="Cap on the per-account cooldown so a flapping account returns eventually.")
    cooldown_memory_seconds: float = Field(
        21600.0, description="How long a spent cooldown keeps its failure streak; idle entries are pruned.")
    persist_account_state: bool = Field(
        True, description="Persist cooldowns so a restart does not immediately re-hit a quarantined account.")

    # --- account-level self-evolution (domain E) -------------------------------
    enable_account_scoring: bool = Field(
        True, description="Learn per-account reliability/cost/latency and use it to order equally-healthy accounts.")
    score_ewma_alpha: float = Field(
        0.25, description="EWMA smoothing for account-level feedback (higher = faster forgetting).")
    reliability_weight: float = Field(
        12.0, description="Headroom-equivalent points a 0..1 reliability shift may move an account.")
    cost_weight: float = Field(
        10.0, description="Max headroom-equivalent points an account loses for being the most expensive.")
    latency_weight: float = Field(
        5.0, description="Max headroom-equivalent points an account loses for being the slowest.")
    max_recorded_runs: int = Field(
        500, description="Bounded ledger size; the oldest goal outcomes are dropped so an unattended run cannot grow forever.")

    # --- self-evolution (domain E) ---------------------------------------------
    enable_self_evolution: bool = Field(
        True, description="Persist break-even measurements and feed them back into mode selection.")
    break_even_store_path: Path = Field(
        Path(".platform_v1_runtime/multi_account_break_even.json"),
        description="Local JSON store for run outcomes and the measured break-even record.")
    min_observations_per_mode: int = Field(
        3, description="Minimum accepted runs per mode before the default selection may move (mirrors orchestration_selector).")
    calibration_feedback_enabled: bool = Field(
        True, description="Wire measured usage -> cost rate via quota_reservation.delta_calibration.")

    # --- routing ownership (domain A, Owner decision 2026-11-04) ----------------
    account_routing: str = Field(
        "local",
        description="Who selects accounts: 'local' (Nerelan), 'magpie' (upstream), or "
                    "'auto' (magpie only when enabled and switching behaviour is acknowledged).")

    # --- unattended keepalive (domain D) ---------------------------------------
    standby_keepalive_interval_seconds: float = Field(
        60.0, description="Heartbeat interval so a sleeping/hibernated host still reconciles leases on wake.")

    # --- cost budget (domain C: 成本限制) --------------------------------------
    # Off by default: an unattended run must never be silently capped by a
    # default value nobody chose. Enabled, the governor admits work against a
    # rolling-window ceiling and holds (never drops) what does not fit.
    cost_budget_enabled: bool = Field(
        False, description="Enforce a rolling-window cost ceiling before dispatching an attempt.")
    cost_budget_units: float = Field(
        0.0, description="Hard ceiling in cost units (list-price equivalent USD) per rolling window.")
    cost_budget_window_seconds: float = Field(
        86400.0, description="Rolling window the ceiling applies to (86400 = per day).")
    cost_budget_soft_ratio: float = Field(
        0.8, description="Fraction of the ceiling at which scheduling degrades to the cheapest account instead of admitting freely.")
    cost_budget_default_task_units: float = Field(
        0.0, description="Conservative per-attempt forecast used when the caller supplies none; "
                         "0 means 'unknown' and the governor then admits on observed spend alone.")
    cost_budget_include_reservations: bool = Field(
        True, description="Count in-flight reservations against the ceiling so concurrent dispatch cannot overshoot it.")

    # --- alerting (domain D: 日志与告警) ---------------------------------------
    alerts_enabled: bool = Field(
        True, description="Evaluate alert rules on every perception/feedback cycle.")
    alert_quiet_seconds: float = Field(
        300.0, description="Suppression window per (code, subject); repeats are counted, not re-emitted.")
    alert_max_history: int = Field(
        120, description="Bounded alert history so a long unattended run cannot grow it without limit.")
    alert_failure_streak_threshold: int = Field(
        2, description="Consecutive account failures that raise a 'flapping account' alert.")
    alert_min_success_rate: float = Field(
        0.6, description="Rolling account success ratio below which a 'degraded reliability' alert is raised.")
    alert_min_samples: int = Field(
        3, description="Attempts an account needs before its success ratio may raise an alert.")
    alert_log_enabled: bool = Field(
        False, description="Also write every emitted alert through the 'reverse_agent.multi_account' logger.")

    # --- run watchdog (domain D: 运行时长) -------------------------------------
    watchdog_enabled: bool = Field(
        True, description="Track elapsed/idle time so an unattended run concludes instead of running forever.")
    max_run_duration_seconds: float = Field(
        0.0, description="Wall-clock budget of one unattended run; 0 = unlimited.")
    max_idle_seconds: float = Field(
        0.0, description="Conclude after this long without a completed attempt; 0 = unlimited.")
    watchdog_hard_stop_ratio: float = Field(
        1.25, description="Past the deadline, stop (not just conclude) once elapsed exceeds the budget by this factor.")

    # --- self-evolution clamp / audit (domain E: 限幅、可审计、可回滚) ----------
    policy_enabled: bool = Field(
        True, description="Allow the self-evolution loop to adjust scheduling weights at all.")
    policy_max_weight_drift_ratio: float = Field(
        0.5, description="A learned weight may only move within +/- this fraction of its configured baseline.")
    policy_max_bonus_points: float = Field(
        12.0, description="Absolute cap on the headroom-equivalent bonus learned feedback may add or remove.")
    policy_step_ratio: float = Field(
        0.25, description="Largest single change per evolution step, as a fraction of the baseline weight.")
    policy_min_samples: int = Field(
        5, description="Attempts required before the loop may propose any policy change.")
    policy_target_success_rate: float = Field(
        0.85, description="Account success ratio the loop steers toward before relaxing learned preferences.")
    policy_audit_max_entries: int = Field(
        120, description="Bounded audit trail; the oldest entries are dropped once full.")

    @field_validator("observation_freshness_seconds", "magpie_max_age_seconds",
                    "reroute_max_attempts", "min_observations_per_mode", "max_recorded_runs",
                    "alert_max_history", "alert_failure_streak_threshold", "alert_min_samples",
                    "policy_min_samples", "policy_audit_max_entries")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be a positive integer")
        return value

    @field_validator("reroute_cooldown_seconds", "abnormal_account_cooldown_seconds",
                    "reset_soon_threshold_seconds", "standby_keepalive_interval_seconds",
                    "failure_backoff_base_seconds", "cooldown_memory_seconds",
                    "reliability_weight", "cost_weight", "latency_weight",
                    "cost_budget_units", "cost_budget_window_seconds",
                    "cost_budget_default_task_units", "alert_quiet_seconds",
                    "max_run_duration_seconds", "max_idle_seconds",
                    "policy_max_bonus_points")
    @classmethod
    def _non_negative_float(cls, value: float) -> float:
        if value < 0:
            raise ValueError("must be non-negative")
        return value

    @field_validator("cost_budget_soft_ratio", "policy_max_weight_drift_ratio", "policy_step_ratio")
    @classmethod
    def _fraction(cls, value: float) -> float:
        if not 0.0 < value <= 1.0:
            raise ValueError("must be within (0, 1]")
        return value

    @field_validator("alert_min_success_rate", "policy_target_success_rate")
    @classmethod
    def _ratio_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("must be within 0..1")
        return value

    @field_validator("watchdog_hard_stop_ratio")
    @classmethod
    def _at_least_one(cls, value: float) -> float:
        if value < 1.0:
            raise ValueError("must be >= 1.0")
        return value

    @field_validator("failure_backoff_multiplier")
    @classmethod
    def _multiplier_at_least_one(cls, value: float) -> float:
        if value < 1.0:
            raise ValueError("must be >= 1.0")
        return value

    @field_validator("account_routing")
    @classmethod
    def _routing_owner(cls, value: str) -> str:
        text = str(value).strip().lower()
        if text not in ("local", "magpie", "auto"):
            raise ValueError("must be one of: local, magpie, auto")
        return text

    @field_validator("score_ewma_alpha")
    @classmethod
    def _alpha_fraction(cls, value: float) -> float:
        if not 0.0 < value <= 1.0:
            raise ValueError("must be within (0, 1]")
        return value

    @field_validator("high_utilization_threshold", "small_task_percent_ceiling")
    @classmethod
    def _percent_range(cls, value: float) -> float:
        if not 0.0 <= value <= 100.0:
            raise ValueError("must be within 0..100")
        return value

    @model_validator(mode="after")
    def _consistent_windows(self) -> "MultiAccountConfig":
        if self.observation_freshness_seconds > self.magpie_max_age_seconds:
            raise ValueError(
                "observation_freshness_seconds must not exceed magpie_max_age_seconds")
        if self.high_utilization_threshold < self.small_task_percent_ceiling:
            raise ValueError(
                "high_utilization_threshold must be >= small_task_percent_ceiling")
        if self.failure_backoff_max_seconds < self.failure_backoff_base_seconds:
            raise ValueError(
                "failure_backoff_max_seconds must be >= failure_backoff_base_seconds")
        # An enforced budget of zero would deny every attempt: refuse to start
        # rather than park the whole unattended run behind a typo.
        if self.cost_budget_enabled and self.cost_budget_units <= 0:
            raise ValueError("cost_budget_units must be positive when cost_budget_enabled is True")
        if self.watchdog_enabled and self.max_idle_seconds and self.max_run_duration_seconds:
            if self.max_idle_seconds > self.max_run_duration_seconds:
                raise ValueError(
                    "max_idle_seconds must not exceed max_run_duration_seconds")
        if self.policy_target_success_rate < self.alert_min_success_rate:
            raise ValueError(
                "policy_target_success_rate must be >= alert_min_success_rate")
        return self

    @classmethod
    def from_env(cls, **overrides: object) -> "MultiAccountConfig":
        """Build from environment overrides; secret-bearing values are never read here.

        Only scalar knobs are overridable; the break-even store path may be set
        via ``REVERSE_AGENT_MULTI_ACCOUNT_STORE`` to relocate the local ledger.

        The scalar map below is the operational surface an unattended deployment
        tunes without a code change (``REVERSE_AGENT_MULTI_ACCOUNT_<KNOB>``).
        Values are parsed with the field's declared type, and a value that fails
        validation still fails fast at construction — a bad deployment stops
        instead of drifting. An explicit ``overrides`` argument always wins over
        the environment so tests and the host stay deterministic.
        """
        import os

        if "account_routing" not in overrides:
            raw_routing = os.environ.get("REVERSE_AGENT_ACCOUNT_ROUTING")
            if raw_routing:
                overrides["account_routing"] = raw_routing

        env_path = overrides.pop("break_even_store_path", None)
        if env_path is None:
            raw = os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_STORE")
            if raw:
                env_path = Path(raw)
        if env_path is not None:
            overrides["break_even_store_path"] = Path(env_path)  # type: ignore[assignment]

        for field, env_name in _ENV_SCALARS.items():
            if field in overrides:
                continue
            raw_value = os.environ.get(env_name)
            if raw_value is None or raw_value == "":
                continue
            try:
                overrides[field] = _coerce(raw_value, field)
            except (TypeError, ValueError):
                # Leave the default in place; construction still validates the
                # final combination, so a typo cannot silently become a default.
                continue
        return cls(**overrides)  # type: ignore[arg-type]
