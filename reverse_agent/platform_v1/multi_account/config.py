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


class MultiAccountConfig(BaseModel):
    """Tunable knobs for account perception, scheduling and self-evolution.

    Defaults follow the planning spec: observation freshness 600 s, Magpie
    snapshot max age 900 s, at most 3 reroute attempts per task, with cooldowns
    that keep a flapping account from being retried immediately.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=False,
                             allow_inf_nan=False)

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
    enable_feedback_routing: bool = Field(
        False, description="Opt in to bounded measured-account adjustments in the production task router.")
    feedback_routing_min_attempts: int = Field(
        3, ge=3, description="Minimum account attempts before measured routing adjustments may apply.")
    feedback_routing_max_adjustment: float = Field(
        0.1, ge=0, le=0.25, description="Maximum absolute adjustment to the existing routing cost score.")
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
    enable_policy_evolution: bool = Field(False, description="Opt in to audited, bounded account-weight evolution.")
    policy_min_new_attempts: int = Field(30, ge=3, le=10000)
    policy_step_ratio: float = Field(0.1, gt=0, le=0.25)
    policy_max_weight_drift_ratio: float = Field(0.25, ge=0, le=1)
    policy_target_success_rate: float = Field(0.85, gt=0, le=1)
    policy_audit_limit: int = Field(64, ge=2, le=256)
    policy_observation_max_age_seconds: float = Field(86400, gt=0, le=30 * 86400)

    # --- self-evolution (domain E) ---------------------------------------------
    enable_self_evolution: bool = Field(
        True, description="Persist break-even measurements and feed them back into mode selection.")
    break_even_store_path: Path = Field(
        Path(".platform_v1_runtime/multi_account_break_even.json"),
        description="Local JSON store for run outcomes and the measured break-even record.")
    min_observations_per_mode: int = Field(
        3, ge=3, description="Minimum usable accepted runs per mode and size band; the core floor of three cannot be lowered.")
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

    @field_validator("observation_freshness_seconds", "magpie_max_age_seconds",
                    "reroute_max_attempts", "min_observations_per_mode", "max_recorded_runs")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be a positive integer")
        return value

    @field_validator("reroute_cooldown_seconds", "abnormal_account_cooldown_seconds",
                    "reset_soon_threshold_seconds", "standby_keepalive_interval_seconds",
                    "failure_backoff_base_seconds", "cooldown_memory_seconds",
                    "reliability_weight", "cost_weight", "latency_weight")
    @classmethod
    def _non_negative_float(cls, value: float) -> float:
        if value < 0:
            raise ValueError("must be non-negative")
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
        if self.enable_policy_evolution and self.policy_min_new_attempts > self.max_recorded_runs:
            raise ValueError("policy_min_new_attempts must fit the retained feedback window")
        if self.observation_freshness_seconds > self.magpie_max_age_seconds:
            raise ValueError(
                "observation_freshness_seconds must not exceed magpie_max_age_seconds")
        if self.high_utilization_threshold < self.small_task_percent_ceiling:
            raise ValueError(
                "high_utilization_threshold must be >= small_task_percent_ceiling")
        if self.failure_backoff_max_seconds < self.failure_backoff_base_seconds:
            raise ValueError(
                "failure_backoff_max_seconds must be >= failure_backoff_base_seconds")
        return self

    @classmethod
    def from_env(cls, **overrides: object) -> "MultiAccountConfig":
        """Build from environment overrides; secret-bearing values are never read here.

        Only scalar knobs are overridable; the break-even store path may be set
        via ``REVERSE_AGENT_MULTI_ACCOUNT_STORE`` to relocate the local ledger.
        """
        import os
        for name in cls.model_fields:
            if name in {"account_routing", "break_even_store_path"} or name in overrides:
                continue
            raw = os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_" + name.upper())
            if raw is not None:
                # Pydantic parses the declared scalar type and rejects invalid,
                # non-finite and out-of-range values without guessing a default.
                overrides[name] = raw
        if "account_routing" not in overrides:
            raw_routing = os.environ.get("REVERSE_AGENT_ACCOUNT_ROUTING")
            if raw_routing:
                overrides["account_routing"] = raw_routing
        env_path = overrides.pop("break_even_store_path", None)
        if env_path is None:
            import os
            raw = os.environ.get("REVERSE_AGENT_MULTI_ACCOUNT_STORE")
            if raw:
                env_path = Path(raw)
        if env_path is not None:
            overrides["break_even_store_path"] = Path(env_path)  # type: ignore[assignment]
        return cls(**overrides)  # type: ignore[arg-type]
