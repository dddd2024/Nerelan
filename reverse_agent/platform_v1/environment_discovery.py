"""Provider-free, zero-execution project environment metadata discovery.

This module only reads a closed set of repository metadata. It never executes
repository code, package managers, setup scripts, containers, providers, or
network operations. Later bootstrap phases may consume this normalized evidence,
but discovery itself grants no setup authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tomllib
from typing import Any


MAX_PARSED_SOURCE_BYTES = 1024 * 1024
MAX_OPAQUE_SOURCE_BYTES = 64 * 1024 * 1024

_DISCOVERY_ERROR_CODES = frozenset(
    {
        "ENV_DISCOVERY_SOURCE_INVALID",
        "ENV_DISCOVERY_SOURCE_TOO_LARGE",
        "ENV_DISCOVERY_UNSUPPORTED_VALUE",
        "ENV_SOURCE_OUTSIDE_REPOSITORY",
    }
)

_SAFE_CONSTRAINT = re.compile(r"^[0-9A-Za-z.*+<>=!~^|,&_\- ]{1,160}$")
_EXACT_VERSION = re.compile(
    r"^\d+(?:\.\d+){0,3}(?:[-+][0-9A-Za-z.-]+)?$"
)
_PACKAGE_MANAGER = re.compile(r"^(npm|pnpm|yarn|bun)@([^@\s]{1,180})$")

_LOCK_SOURCES = (
    ("Cargo.lock", "lock:rust:cargo"),
    ("Pipfile.lock", "lock:python:pipenv"),
    ("bun.lock", "lock:node:bun"),
    ("bun.lockb", "lock:node:bun"),
    ("go.sum", "lock:go:modules"),
    ("npm-shrinkwrap.json", "lock:node:npm"),
    ("package-lock.json", "lock:node:npm"),
    ("pnpm-lock.yaml", "lock:node:pnpm"),
    ("poetry.lock", "lock:python:poetry"),
    ("uv.lock", "lock:python:uv"),
    ("yarn.lock", "lock:node:yarn"),
)

_SETUP_SOURCES = (
    (".devcontainer/devcontainer.json", "setup:devcontainer"),
    (".devcontainer.json", "setup:devcontainer"),
    ("devcontainer.json", "setup:devcontainer"),
    ("Dockerfile", "setup:dockerfile"),
    ("compose.yaml", "setup:compose"),
    ("compose.yml", "setup:compose"),
    ("docker-compose.yaml", "setup:compose"),
    ("docker-compose.yml", "setup:compose"),
    (".github/workflows/copilot-setup-steps.yml", "setup:copilot"),
    (".github/workflows/copilot-setup-steps.yaml", "setup:copilot"),
)

_TOOL_VERSION_RUNTIME = {
    "python": "python",
    "nodejs": "node",
    "rust": "rust",
    "golang": "go",
}


class EnvironmentDiscoveryError(ValueError):
    """Stable, sanitized failure from bounded metadata discovery."""

    def __init__(self, code: str, source: str = "") -> None:
        if code not in _DISCOVERY_ERROR_CODES:
            raise ValueError("invalid_environment_discovery_error_code")
        self.code = code
        self.source = source
        super().__init__(f"{code}:{source}" if source else code)


@dataclass(frozen=True)
class EnvironmentSource:
    path: str
    kind: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeRequirement:
    runtime: str
    constraint_kind: str
    constraint: str
    source: EnvironmentSource

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime,
            "constraint_kind": self.constraint_kind,
            "constraint": self.constraint,
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True)
class ToolRequirement:
    tool: str
    constraint: str
    source: EnvironmentSource

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "constraint": self.constraint,
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True)
class EnvironmentConflict:
    code: str
    subject: str
    values: tuple[str, ...]
    sources: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "subject": self.subject,
            "values": list(self.values),
            "sources": list(self.sources),
        }


@dataclass(frozen=True)
class EnvironmentDiscoveryResult:
    runtimes: tuple[RuntimeRequirement, ...]
    tools: tuple[ToolRequirement, ...]
    locks: tuple[EnvironmentSource, ...]
    setup_sources: tuple[EnvironmentSource, ...]
    conflicts: tuple[EnvironmentConflict, ...]
    digest: str

    @property
    def blocked(self) -> bool:
        return bool(self.conflicts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtimes": [item.to_dict() for item in self.runtimes],
            "tools": [item.to_dict() for item in self.tools],
            "locks": [item.to_dict() for item in self.locks],
            "setup_sources": [item.to_dict() for item in self.setup_sources],
            "conflicts": [item.to_dict() for item in self.conflicts],
            "digest": self.digest,
        }


def discover_environment_requirements(
    repository_root: str | Path,
) -> EnvironmentDiscoveryResult:
    """Discover a bounded environment contract without executing repository code."""

    root = _resolve_repository_root(repository_root)
    runtimes: list[RuntimeRequirement] = []
    tools: list[ToolRequirement] = []

    pyproject = _read_source(
        root, "pyproject.toml", "manifest:pyproject", MAX_PARSED_SOURCE_BYTES
    )
    if pyproject is not None:
        source, data = pyproject
        payload = _parse_toml(data, source)
        project = payload.get("project")
        if project is not None and not isinstance(project, Mapping):
            raise _unsupported(source)
        if isinstance(project, Mapping) and "requires-python" in project:
            constraint = _constraint(project["requires-python"], source)
            runtimes.append(
                RuntimeRequirement("python", "range", constraint, source)
            )

    python_version = _read_source(
        root, ".python-version", "version:python", MAX_PARSED_SOURCE_BYTES
    )
    if python_version is not None:
        source, data = python_version
        pin = _single_exact_pin(_decode(data, source), "python", source)
        runtimes.append(RuntimeRequirement("python", "exact", pin, source))

    package_json = _read_source(
        root, "package.json", "manifest:package-json", MAX_PARSED_SOURCE_BYTES
    )
    if package_json is not None:
        source, data = package_json
        payload = _parse_json(data, source)
        engines = payload.get("engines")
        if engines is not None and not isinstance(engines, Mapping):
            raise _unsupported(source)
        if isinstance(engines, Mapping) and "node" in engines:
            constraint = _constraint(engines["node"], source)
            runtimes.append(RuntimeRequirement("node", "range", constraint, source))
        if "packageManager" in payload:
            tools.append(_package_manager_requirement(payload["packageManager"], source))

    node_version = _read_source(
        root, ".node-version", "version:node", MAX_PARSED_SOURCE_BYTES
    )
    if node_version is not None:
        source, data = node_version
        pin = _single_exact_pin(_decode(data, source), "node", source)
        runtimes.append(RuntimeRequirement("node", "exact", pin, source))

    tool_versions = _read_source(
        root, ".tool-versions", "version:tool-versions", MAX_PARSED_SOURCE_BYTES
    )
    if tool_versions is not None:
        source, data = tool_versions
        runtimes.extend(_parse_tool_versions(_decode(data, source), source))

    cargo_toml = _read_source(
        root, "Cargo.toml", "manifest:cargo", MAX_PARSED_SOURCE_BYTES
    )
    if cargo_toml is not None:
        source, data = cargo_toml
        payload = _parse_toml(data, source)
        package = payload.get("package")
        if package is not None and not isinstance(package, Mapping):
            raise _unsupported(source)
        if isinstance(package, Mapping) and "rust-version" in package:
            version = _exact_version(package["rust-version"], "rust", source)
            runtimes.append(RuntimeRequirement("rust", "minimum", version, source))

    go_mod = _read_source(
        root, "go.mod", "manifest:go-mod", MAX_PARSED_SOURCE_BYTES
    )
    if go_mod is not None:
        source, data = go_mod
        version = _parse_go_directive(_decode(data, source), source)
        if version is not None:
            runtimes.append(RuntimeRequirement("go", "minimum", version, source))

    locks = tuple(
        item
        for relative, kind in _LOCK_SOURCES
        if (item := _opaque_source(root, relative, kind)) is not None
    )
    setup_sources = tuple(
        item
        for relative, kind in _SETUP_SOURCES
        if (item := _opaque_source(root, relative, kind)) is not None
    )

    normalized_runtimes = _dedupe_runtimes(runtimes)
    normalized_tools = _dedupe_tools(tools)
    normalized_locks = tuple(sorted(set(locks), key=_source_key))
    normalized_setup = tuple(sorted(set(setup_sources), key=_source_key))
    conflicts = _exact_pin_conflicts(normalized_runtimes)

    payload = {
        "schema_version": 1,
        "runtimes": [item.to_dict() for item in normalized_runtimes],
        "tools": [item.to_dict() for item in normalized_tools],
        "locks": [item.to_dict() for item in normalized_locks],
        "setup_sources": [item.to_dict() for item in normalized_setup],
        "conflicts": [item.to_dict() for item in conflicts],
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    return EnvironmentDiscoveryResult(
        runtimes=normalized_runtimes,
        tools=normalized_tools,
        locks=normalized_locks,
        setup_sources=normalized_setup,
        conflicts=conflicts,
        digest=digest,
    )


def _resolve_repository_root(repository_root: str | Path) -> Path:
    try:
        root = Path(repository_root).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise OSError
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise EnvironmentDiscoveryError("ENV_DISCOVERY_SOURCE_INVALID", ".") from exc
    return root


def _read_source(
    root: Path,
    relative: str,
    kind: str,
    limit: int,
) -> tuple[EnvironmentSource, bytes] | None:
    candidate = _safe_candidate(root, relative)
    if candidate is None:
        return None
    try:
        size = candidate.stat().st_size
        if size > limit:
            raise EnvironmentDiscoveryError(
                "ENV_DISCOVERY_SOURCE_TOO_LARGE", relative
            )
        data = candidate.read_bytes()
        if len(data) > limit:
            raise EnvironmentDiscoveryError(
                "ENV_DISCOVERY_SOURCE_TOO_LARGE", relative
            )
    except EnvironmentDiscoveryError:
        raise
    except OSError as exc:
        raise EnvironmentDiscoveryError(
            "ENV_DISCOVERY_SOURCE_INVALID", relative
        ) from exc
    return (
        EnvironmentSource(
            path=relative,
            kind=kind,
            sha256=hashlib.sha256(data).hexdigest(),
        ),
        data,
    )


def _opaque_source(
    root: Path,
    relative: str,
    kind: str,
) -> EnvironmentSource | None:
    admitted = _read_source(root, relative, kind, MAX_OPAQUE_SOURCE_BYTES)
    return admitted[0] if admitted is not None else None


def _safe_candidate(root: Path, relative: str) -> Path | None:
    parts = PurePosixPath(relative).parts
    if (
        not parts
        or PurePosixPath(relative).is_absolute()
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise EnvironmentDiscoveryError(
            "ENV_SOURCE_OUTSIDE_REPOSITORY", relative
        )

    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise EnvironmentDiscoveryError(
                "ENV_SOURCE_OUTSIDE_REPOSITORY", relative
            )

    if not current.exists():
        return None
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise EnvironmentDiscoveryError(
            "ENV_SOURCE_OUTSIDE_REPOSITORY", relative
        ) from exc
    if not resolved.is_file():
        raise EnvironmentDiscoveryError(
            "ENV_DISCOVERY_SOURCE_INVALID", relative
        )
    return resolved


def _decode(data: bytes, source: EnvironmentSource) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EnvironmentDiscoveryError(
            "ENV_DISCOVERY_SOURCE_INVALID", source.path
        ) from exc


def _parse_toml(data: bytes, source: EnvironmentSource) -> Mapping[str, Any]:
    try:
        payload = tomllib.loads(_decode(data, source))
    except ValueError as exc:
        raise EnvironmentDiscoveryError(
            "ENV_DISCOVERY_SOURCE_INVALID", source.path
        ) from exc
    if not isinstance(payload, Mapping):
        raise EnvironmentDiscoveryError(
            "ENV_DISCOVERY_SOURCE_INVALID", source.path
        )
    return payload


def _reject_json_constant(_: str) -> None:
    raise ValueError("non_standard_json_constant")


def _parse_json(data: bytes, source: EnvironmentSource) -> Mapping[str, Any]:
    try:
        payload = json.loads(
            _decode(data, source),
            parse_constant=_reject_json_constant,
        )
    except ValueError as exc:
        raise EnvironmentDiscoveryError(
            "ENV_DISCOVERY_SOURCE_INVALID", source.path
        ) from exc
    if not isinstance(payload, Mapping):
        raise EnvironmentDiscoveryError(
            "ENV_DISCOVERY_SOURCE_INVALID", source.path
        )
    return payload


def _unsupported(source: EnvironmentSource) -> EnvironmentDiscoveryError:
    return EnvironmentDiscoveryError(
        "ENV_DISCOVERY_UNSUPPORTED_VALUE", source.path
    )


def _constraint(value: Any, source: EnvironmentSource) -> str:
    if not isinstance(value, str):
        raise _unsupported(source)
    normalized = " ".join(value.split())
    if not _SAFE_CONSTRAINT.fullmatch(normalized):
        raise _unsupported(source)
    return normalized


def _exact_version(
    value: Any,
    runtime: str,
    source: EnvironmentSource,
) -> str:
    if not isinstance(value, str):
        raise _unsupported(source)
    normalized = value.strip()
    if (
        runtime == "node"
        and len(normalized) > 1
        and normalized[0] in {"v", "V"}
        and normalized[1].isdigit()
    ):
        normalized = normalized[1:]
    if not _EXACT_VERSION.fullmatch(normalized):
        raise _unsupported(source)
    return normalized


def _single_exact_pin(
    text: str,
    runtime: str,
    source: EnvironmentSource,
) -> str:
    values = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(values) != 1 or any(char.isspace() for char in values[0]):
        raise _unsupported(source)
    return _exact_version(values[0], runtime, source)


def _package_manager_requirement(
    value: Any,
    source: EnvironmentSource,
) -> ToolRequirement:
    if not isinstance(value, str):
        raise _unsupported(source)
    match = _PACKAGE_MANAGER.fullmatch(value.strip())
    if match is None:
        raise _unsupported(source)
    version = match.group(2)
    if "+sha" in version:
        version = version.split("+sha", 1)[0]
    if not _EXACT_VERSION.fullmatch(version):
        raise _unsupported(source)
    return ToolRequirement(match.group(1), version, source)


def _parse_tool_versions(
    text: str,
    source: EnvironmentSource,
) -> list[RuntimeRequirement]:
    requirements: list[RuntimeRequirement] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        runtime = _TOOL_VERSION_RUNTIME.get(parts[0])
        if runtime is None:
            continue
        if len(parts) != 2:
            raise _unsupported(source)
        requirements.append(
            RuntimeRequirement(
                runtime,
                "exact",
                _exact_version(parts[1], runtime, source),
                source,
            )
        )
    return requirements


def _parse_go_directive(
    text: str,
    source: EnvironmentSource,
) -> str | None:
    seen: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        if re.match(r"^go(?:\s|$)", line) is None:
            continue
        match = re.fullmatch(r"go\s+(\d+(?:\.\d+){1,2})", line)
        if match is None:
            raise _unsupported(source)
        seen.append(match.group(1))
    if not seen:
        return None
    if len(set(seen)) != 1:
        raise EnvironmentDiscoveryError(
            "ENV_DISCOVERY_SOURCE_INVALID", source.path
        )
    return seen[0]


def _runtime_key(
    item: RuntimeRequirement,
) -> tuple[str, str, str, str, str]:
    return (
        item.runtime,
        item.constraint_kind,
        item.constraint,
        item.source.path,
        item.source.sha256,
    )


def _tool_key(item: ToolRequirement) -> tuple[str, str, str, str]:
    return (
        item.tool,
        item.constraint,
        item.source.path,
        item.source.sha256,
    )


def _source_key(item: EnvironmentSource) -> tuple[str, str, str]:
    return (item.path, item.kind, item.sha256)


def _dedupe_runtimes(
    items: list[RuntimeRequirement],
) -> tuple[RuntimeRequirement, ...]:
    return tuple(sorted({_runtime_key(item): item for item in items}.values(), key=_runtime_key))


def _dedupe_tools(
    items: list[ToolRequirement],
) -> tuple[ToolRequirement, ...]:
    return tuple(sorted({_tool_key(item): item for item in items}.values(), key=_tool_key))


def _exact_pin_conflicts(
    runtimes: tuple[RuntimeRequirement, ...],
) -> tuple[EnvironmentConflict, ...]:
    exact: dict[str, dict[str, set[str]]] = {}
    for item in runtimes:
        if item.constraint_kind != "exact":
            continue
        exact.setdefault(item.runtime, {}).setdefault(
            item.constraint, set()
        ).add(item.source.path)

    conflicts: list[EnvironmentConflict] = []
    for runtime in sorted(exact):
        values = exact[runtime]
        if len(values) <= 1:
            continue
        conflicts.append(
            EnvironmentConflict(
                code="ENV_VERSION_CONFLICT",
                subject=runtime,
                values=tuple(sorted(values)),
                sources=tuple(
                    sorted(
                        {
                            source
                            for source_paths in values.values()
                            for source in source_paths
                        }
                    )
                ),
            )
        )
    return tuple(conflicts)
