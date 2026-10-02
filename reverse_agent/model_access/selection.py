"""Provider-free pairing preview, deliberately separate from dispatch authority.

Inputs are one trusted store snapshot and a bounded user preference request.
This module performs no I/O, writes no bindings and grants no model budget.
Advertised IDs and requested model names are not underlying-model attestation.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any


_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
_CAPABILITY = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
_UNKNOWN = ["cost", "quality", "task_success", "underlying_model_identity"]
_FIELDS = {
    "selection_mode", "manual_binding_ref", "purpose", "required_capabilities",
    "orchestration_mode", "executor_preference", "preferred_binding_refs",
}
_REASONS = {
    "binding_disabled": "绑定已停用",
    "connection_missing": "连接不存在",
    "connection_disabled": "连接已停用",
    "executor_missing": "执行器不存在",
    "executor_not_operational": "执行器尚未就绪",
    "readiness_not_observed": "尚未观测执行器就绪状态",
    "capability_missing": "执行器缺少任务所需能力",
    "executor_preference_mismatch": "与明确选择的执行器不符",
    "protocol_unsupported": "连接协议与执行器不兼容",
    "credential_missing": "API 凭据尚未配置或不可用",
    "session_not_observed": "此执行器的登录状态尚未就绪",
    "native_single_only": "原生 Codex 仅支持单执行器模式",
    "model_namespace_mismatch": "模型 ID 与连接的执行器命名空间不符",
    "model_invalid": "模型 ID 无效",
    "configuration_stale": "连接配置已变化，请重新获取目录",
    "catalog_stale": "目录已失效，请重新获取",
    "requires_bounded_gpt_approval": "GPT 选择需要另行批准的调用与重试预算",
    "model_family_unknown": "模型类别未知，无法作为常规自动选择",
    "explicit_preference": "按你的明确偏好排列",
    "configured_deepseek": "已配置的 DeepSeek 模型",
    "configured_agnes": "已配置的 Agnes 模型",
}


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"{field} must be a bounded identifier")
    return value


def _request(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or set(payload) - _FIELDS:
        raise ValueError("selection preview contains unsupported fields")
    mode = payload.get("selection_mode", "automatic")
    if mode not in {"automatic", "manual"}:
        raise ValueError("selection_mode must be automatic or manual")
    orchestration = payload.get("orchestration_mode", "single")
    if orchestration not in {"single", "sequential_team"}:
        raise ValueError("unsupported orchestration_mode")
    purpose = payload.get("purpose", "development")
    if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 80 or any(ord(c) < 32 for c in purpose):
        raise ValueError("purpose must be bounded text")
    preferred = payload.get("preferred_binding_refs", [])
    if not isinstance(preferred, list) or len(preferred) > 32:
        raise ValueError("preferred_binding_refs must be a bounded list")
    preferred = list(dict.fromkeys(_identifier(x, "preferred_binding_ref") for x in preferred))
    capabilities = payload.get("required_capabilities", ["workspace_execution"])
    if not isinstance(capabilities, list) or len(capabilities) > 16 or any(not isinstance(x, str) or not _CAPABILITY.fullmatch(x) for x in capabilities):
        raise ValueError("required_capabilities must be a bounded list")
    manual = payload.get("manual_binding_ref")
    if manual is not None:
        manual = _identifier(manual, "manual_binding_ref")
    if mode == "manual" and manual is None:
        raise ValueError("manual selection requires manual_binding_ref")
    if mode == "automatic" and manual is not None:
        raise ValueError("manual_binding_ref requires manual mode")
    executor = payload.get("executor_preference")
    if executor is not None:
        executor = _identifier(executor, "executor_preference")
    return {"mode": mode, "manual": manual, "preferred": preferred,
            "capabilities": set(capabilities), "orchestration": orchestration,
            "executor": executor}


def _index(values: Any, field: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(values, list) or len(values) > 4096:
        raise ValueError("selection snapshot is invalid or exceeds bounds")
    result = {}
    for value in values:
        if not isinstance(value, Mapping):
            raise ValueError("selection snapshot entry is invalid")
        key = _identifier(value.get(field), field)
        if key in result:
            raise ValueError("selection snapshot contains duplicate identities")
        result[key] = value
    return result


def _revision(value: Any) -> str | None:
    return value if isinstance(value, str) and 0 < len(value) <= 128 and all(32 <= ord(c) < 127 for c in value) else None


def _model(raw: Any, namespace: Any, native: bool) -> str | None:
    if not isinstance(raw, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,199}", raw):
        return None
    if "://" in raw or raw.casefold().startswith(("sk-", "sk_", "bearer")):
        return None
    if native:
        return raw if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", raw) else None
    if not isinstance(namespace, str) or not _ID.fullmatch(namespace):
        return None
    prefix = namespace + "/"
    if raw.startswith(prefix):
        return raw[len(prefix):] or None
    return raw if "/" not in raw else None


def _model_family(model: str | None, connection: Mapping[str, Any]) -> str:
    if model is None:
        return "unknown"
    normalized = model.casefold()
    # Deny recognizable GPT IDs even when a custom provider relabels a connection.
    if re.search(r"gpt(?:[0-9]|[-._]|$)|(?:^|[/._-])(?:o[134](?:[-._]|$)|codex(?:[-._]|$))", normalized):
        return "gpt"
    # These are configured families, never proofs of the actual underlying model.
    if normalized.startswith(("deepseek-", "deepseek/")) and connection.get("upstream_provider_id") in {"deepseek", "openrouter"}:
        return "deepseek"
    if normalized.startswith(("agnes-", "agnes/")) and connection.get("upstream_provider_id") == "sensetime":
        return "agnes"
    return "unknown"


def recommend_model_selection(snapshot: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a preference preview; callers must still enforce dispatch authority."""
    request = _request(payload)
    if not isinstance(snapshot, Mapping):
        raise ValueError("selection snapshot is invalid")
    connections = _index(snapshot.get("connections", []), "connection_id")
    executors = _index(snapshot.get("executors", []), "executor_id")
    bindings = _index(snapshot.get("bindings", []), "binding_id")
    catalogs = snapshot.get("catalogs", {})
    if not isinstance(catalogs, Mapping):
        raise ValueError("selection catalogs are invalid")
    if request["manual"] is not None and request["manual"] not in bindings:
        raise ValueError("manual binding not found")
    candidates: list[dict[str, Any]] = []
    ranks: dict[str, tuple[int, str]] = {}
    for binding_id, binding in bindings.items():
        if request["mode"] == "manual" and binding_id != request["manual"]:
            continue
        connection_id = _identifier(binding.get("connection_id"), "connection_id")
        executor_id = _identifier(binding.get("executor_id"), "executor_id")
        connection = connections.get(connection_id, {})
        executor = executors.get(executor_id, {})
        reasons: list[str] = []
        if binding.get("enabled") is not True:
            reasons.append("binding_disabled")
        if not connection:
            reasons.append("connection_missing")
        elif connection.get("enabled") is not True:
            reasons.append("connection_disabled")
        if not executor:
            reasons.append("executor_missing")
        elif executor.get("operational") is not True:
            reasons.append("executor_not_operational")
        if executor.get("readiness_status") not in {"ready", "managed_login_ready"}:
            reasons.append("readiness_not_observed")
        caps = executor.get("capabilities", [])
        if not isinstance(caps, (list, tuple)) or not request["capabilities"].issubset({x for x in caps if isinstance(x, str)}):
            reasons.append("capability_missing")
        if request["executor"] is not None and executor_id != request["executor"]:
            reasons.append("executor_preference_mismatch")
        native = executor_id == "codex"
        auth = connection.get("auth_method")
        protocol = connection.get("protocol_family")
        namespace = connection.get("executor_provider_id", connection.get("provider"))
        if native:
            if protocol != "codex-cli" or namespace != "codex" or connection.get("upstream_provider_id") != "openai" or auth != "external_cli_session":
                reasons.append("protocol_unsupported")
            if request["orchestration"] != "single":
                reasons.append("native_single_only")
        elif executor_id != "opencode" or protocol != "openai" or auth not in {"api_key", "none", "account_login", "external_cli_session"}:
            reasons.append("protocol_unsupported")
        if auth == "api_key" and connection.get("secret_status") not in {"session", "environment", "stored"}:
            reasons.append("credential_missing")
        if auth in {"account_login", "external_cli_session"} and connection.get("external_session_status") not in {"available", "executor_managed"}:
            reasons.append("session_not_observed")
        model = _model(binding.get("model_id"), namespace, native)
        if model is None:
            reasons.append("model_namespace_mismatch" if isinstance(binding.get("model_id"), str) and "/" in binding["model_id"] else "model_invalid")
        family = _model_family(model, connection)
        if family == "gpt" or native:
            reasons.append("requires_bounded_gpt_approval")
        elif family == "unknown":
            reasons.append("model_family_unknown")
        generation = _revision(connection.get("configuration_revision"))
        catalog = catalogs.get(connection_id, {})
        if not isinstance(catalog, Mapping):
            catalog = {}
        catalog_revision = _revision(catalog.get("catalog_revision"))
        advertised = catalog.get("models", [])
        active_catalog = catalog.get("ok") is True and generation is not None and catalog.get("configuration_revision") == generation
        source = "discovered" if binding.get("source") == "discovered" else "manual"
        if source == "discovered":
            if generation is None or binding.get("configuration_revision") != generation:
                reasons.append("configuration_stale")
            if not active_catalog or binding.get("catalog_revision") != catalog_revision or not isinstance(advertised, list) or model not in advertised:
                reasons.append("catalog_stale")
        eligible = not reasons
        preference_rank = request["preferred"].index(binding_id) if binding_id in request["preferred"] else len(request["preferred"])
        if binding_id in request["preferred"] or request["mode"] == "manual":
            reasons.append("explicit_preference")
        if family in {"deepseek", "agnes"}:
            reasons.append("configured_" + family)
        availability = "advertised_unverified" if active_catalog and isinstance(advertised, list) and model in advertised else "not_observed"
        explanation = "；".join(_REASONS[code] for code in reasons) or "协议与就绪检查匹配"
        explanation += "。这是选择预览，质量和费用证据不足；执行仍需授权与预算检查。"
        candidates.append({
            "binding_ref": binding_id, "connection_id": connection_id,
            "executor_id": executor_id, "model_id": binding.get("model_id") if model is not None else "",
            "configuration_revision": generation, "catalog_revision": catalog_revision if active_catalog else None,
            "source": source, "eligible": eligible, "reason_codes": reasons,
            "explanation": explanation, "availability": availability,
            "underlying_identity": None, "underlying_identity_status": "not_observed",
            "cost": None, "quality": None,
        })
        ranks[binding_id] = (preference_rank, binding_id)
    candidates.sort(key=lambda x: (not x["eligible"], ranks[x["binding_ref"]]))
    recommended = next((x for x in candidates if x["eligible"]), None)
    status = "recommended" if recommended else "manual_blocked" if request["mode"] == "manual" else "no_eligible_pairing"
    message = (
        "按明确偏好与兼容条件提供预览，执行仍需授权与预算检查。"
        if request["preferred"] or request["mode"] == "manual"
        else "按兼容条件提供稳定预览，尚未指定绑定偏好；执行仍需授权与预算检查。"
    ) if recommended else "当前没有通过兼容与就绪检查的绑定；请查看原因，保留手动设置。"
    return {"preview_only": True, "policy_id": "catalog-preview-v1", "status": status,
            "message": message, "recommended": recommended, "candidates": candidates,
            "evidence_unknowns": list(_UNKNOWN)}
