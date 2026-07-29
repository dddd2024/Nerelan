"""Machine verification for the fixed Gate 2 component projection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROJECTION_SHA256 = (
    "e7c334033f8999d7b53fdd7b4b34e4469c3f87a871d4524e4270c707b7f2f83d"
)
COMPONENTS = frozenset(
    {
        "temporal-server",
        "temporal-ui",
        "temporal-admin-tools",
        "postgresql",
        "temporal-python-sdk",
        "openhands-agent-canvas",
        "openhands-agent-server",
        "litellm-proxy",
    }
)
_CONTAINER_FIELDS = frozenset(
    {
        "component",
        "upstream_repository",
        "release_tag",
        "container_image",
        "image_digest",
        "license",
        "selected_at",
        "compatibility_evidence",
    }
)
_PACKAGE_FIELDS = frozenset(
    {
        "component",
        "upstream_repository",
        "package_name",
        "package_version",
        "archive_type",
        "archive_digest",
        "license",
        "selected_at",
        "compatibility_evidence",
    }
)


def load_component_lock(path: Path) -> dict[str, Any]:
    """Load the JSON-compatible YAML lock and validate its exact projection."""

    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("schema_version") != 2:
        raise ValueError("component_lock_schema")
    components = lock.get("components")
    if not isinstance(components, list) or len(components) != 8:
        raise ValueError("component_lock_count")
    names = [entry.get("component") for entry in components if isinstance(entry, dict)]
    if len(names) != 8 or len(set(names)) != 8 or set(names) != COMPONENTS:
        raise ValueError("component_lock_inventory")

    projection: list[str] = []
    for entry in components:
        required = (
            _PACKAGE_FIELDS
            if entry["component"] == "temporal-python-sdk"
            else _CONTAINER_FIELDS
        )
        if set(entry) != required or any(
            not isinstance(entry[field], str) or not entry[field]
            for field in required
        ):
            raise ValueError(f"component_lock_fields:{entry['component']}")
        serialized = json.dumps(entry, sort_keys=True)
        if "latest" in serialized.lower():
            raise ValueError(f"floating_component:{entry['component']}")
        if entry["component"] == "temporal-python-sdk":
            if entry["archive_type"] != "sdist":
                raise ValueError("temporal_sdk_archive_type")
            selection = f"{entry['archive_type']}-{entry['archive_digest']}"
            projection.append(
                f"{entry['component']}|{entry['package_version']}|{selection}"
            )
        else:
            if not entry["image_digest"].startswith("sha256:"):
                raise ValueError(f"component_digest:{entry['component']}")
            projection.append(
                f"{entry['component']}|{entry['release_tag']}|"
                f"{entry['container_image']}@{entry['image_digest']}"
            )

    projection_text = "\n".join(projection)
    projection_digest = hashlib.sha256(projection_text.encode("utf-8")).hexdigest()
    if projection_digest != PROJECTION_SHA256:
        raise ValueError("component_projection_content_drift")
    if lock.get("projection_sha256") != projection_digest:
        raise ValueError("component_projection_digest_drift")
    return lock
