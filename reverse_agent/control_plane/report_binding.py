"""Phase F: local report subject binding.

The local report binds to the implementation subject via cryptographically
derived digests instead of claiming a final remote HEAD. Final commit/head
binding is the responsibility of the external publication seal (F2, F4,
Phase F 9.1).

Binding fields:

- ``activation_base_sha`` — the Decision's activation base SHA
- ``implementation_subject_paths`` — real code/test paths (excludes Decision,
  roadmap and generated artifacts)
- ``subject_tree_digest`` — SHA-256 of the subject file tree (sorted paths)
- ``subject_diff_digest`` — SHA-256 of the unified diff at report time
- ``observed_worktree_paths`` — sorted tuple of dirty paths
- ``local_seal_digest`` — digest from the LOCAL_RECONCILED seal

The binding deliberately does NOT expose ``final_head`` / ``remote_head`` /
``final_commit`` — those are external publication concerns.

Phase F 9.2: :func:`classify_path` and :class:`ClassifiedPaths` split a raw
changed-file list into ``implementation_paths``, ``generated_artifact_paths``
and ``governance_paths`` so the binding can bind to the implementation
subject only (roadmap 9.2: "不得再只列 decision_packet.md").
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


def classify_path(path: str) -> str:
    """Classify a single worktree path into one of three buckets.

    Returns one of:
    - ``"implementation"`` — real code and test modifications
    - ``"governance"`` — the Decision itself, roadmaps
    - ``"generated"`` — auto-generated report/gate artifacts

    Phase F 9.2: the Decision, roadmap and auto-generated artifacts must not
    appear in ``implementation_paths``.
    """

    normalized = path.replace("\\", "/").strip()
    # Governance: the Decision itself and roadmap documents.
    if normalized == "project_state/decision_packet.md":
        return "governance"
    if normalized.startswith("docs/roadmap/"):
        return "governance"
    # Generated: auto-generated report/gate/round artifacts under project_state/.
    if normalized.startswith("project_state/gates/"):
        return "generated"
    if normalized.startswith("project_state/rounds/"):
        return "generated"
    if normalized in (
        "project_state/execution_report.md",
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/bootstrap_state.json",
    ):
        return "generated"
    # Everything else is implementation (reverse_agent/**, tests/**, etc.).
    return "implementation"


@dataclass(frozen=True)
class ClassifiedPaths:
    """Phase F 9.2: a classified changed-file inventory.

    Sorts the raw path list into three canonical, sorted buckets so the
    report binding can bind to the implementation subject only.
    """

    implementation_paths: tuple[str, ...] = field(default=())
    governance_paths: tuple[str, ...] = field(default=())
    generated_artifact_paths: tuple[str, ...] = field(default=())

    @classmethod
    def from_paths(cls, paths: tuple[str, ...]) -> "ClassifiedPaths":
        impl: list[str] = []
        gov: list[str] = []
        gen: list[str] = []
        for path in paths:
            bucket = classify_path(path)
            if bucket == "implementation":
                impl.append(path)
            elif bucket == "governance":
                gov.append(path)
            else:
                gen.append(path)
        return cls(
            implementation_paths=tuple(sorted(impl)),
            governance_paths=tuple(sorted(gov)),
            generated_artifact_paths=tuple(sorted(gen)),
        )

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "implementation_paths": list(self.implementation_paths),
            "governance_paths": list(self.governance_paths),
            "generated_artifact_paths": list(self.generated_artifact_paths),
        }


def compute_subject_tree_digest(repo_root: Path, paths: tuple[str, ...]) -> str:
    """Compute a SHA-256 digest over the sorted contents of ``paths``.

    The digest is order-independent: paths are sorted before hashing so
    that callers cannot differentiate bindings that observe the same file
    contents in different order.
    """

    hasher = hashlib.sha256()
    for rel_path in sorted(paths):
        hasher.update(rel_path.encode("utf-8"))
        hasher.update(b"\0")
        abs_path = Path(repo_root) / rel_path
        if abs_path.is_file():
            hasher.update(abs_path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def compute_subject_diff_digest(diff_text: str) -> str:
    """Compute a SHA-256 digest over the unified diff text."""

    return hashlib.sha256(diff_text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReportSubjectBinding:
    """Local report binding to the implementation subject.

    Attributes are intentionally minimal: the binding proves what the
    local round observed, not what the remote eventually accepted.

    Phase F 9.1: ``implementation_subject_paths`` records the real code and
    test modifications only — the Decision, roadmap and auto-generated
    report/gate artifacts are excluded so the binding reflects the true
    implementation subject.
    """

    activation_base_sha: str
    subject_tree_digest: str
    subject_diff_digest: str
    observed_worktree_paths: tuple[str, ...] = field(default=())
    implementation_subject_paths: tuple[str, ...] = field(default=())
    local_seal_digest: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialize to a dict. Deliberately omits remote HEAD fields."""

        return {
            "activation_base_sha": self.activation_base_sha,
            "subject_tree_digest": self.subject_tree_digest,
            "subject_diff_digest": self.subject_diff_digest,
            "observed_worktree_paths": list(self.observed_worktree_paths),
            "implementation_subject_paths": list(self.implementation_subject_paths),
            "local_seal_digest": self.local_seal_digest,
        }


def build_report_subject_binding(
    *,
    repo_root: Path,
    activation_base_sha: str,
    subject_paths: tuple[str, ...],
    diff_text: str,
    observed_worktree_paths: tuple[str, ...],
    local_seal_digest: str,
    implementation_subject_paths: tuple[str, ...] = (),
) -> ReportSubjectBinding:
    """Build a :class:`ReportSubjectBinding` from observed inputs.

    ``observed_worktree_paths`` and ``implementation_subject_paths`` are
    sorted before storage so that the binding is canonical regardless of
    caller iteration order.

    Phase F 9.1: when ``implementation_subject_paths`` is omitted, it
    defaults to empty — callers that want the binding to record the
    implementation subject must pass the classified paths explicitly.
    """

    return ReportSubjectBinding(
        activation_base_sha=activation_base_sha,
        subject_tree_digest=compute_subject_tree_digest(repo_root, subject_paths),
        subject_diff_digest=compute_subject_diff_digest(diff_text),
        observed_worktree_paths=tuple(sorted(observed_worktree_paths)),
        implementation_subject_paths=tuple(sorted(implementation_subject_paths)),
        local_seal_digest=local_seal_digest,
    )
