"""Phase F: local report subject binding.

The local report binds to the implementation subject via cryptographically
derived digests instead of claiming a final remote HEAD. Final commit/head
binding is the responsibility of the external publication seal (F2, F4,
Phase F 9.1).

Binding fields:

- ``activation_base_sha`` — the Decision's activation base SHA
- ``subject_tree_digest`` — SHA-256 of the subject file tree (sorted paths)
- ``subject_diff_digest`` — SHA-256 of the unified diff at report time
- ``observed_worktree_paths`` — sorted tuple of dirty paths
- ``local_seal_digest`` — digest from the LOCAL_RECONCILED seal

The binding deliberately does NOT expose ``final_head`` / ``remote_head`` /
``final_commit`` — those are external publication concerns.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


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
    """

    activation_base_sha: str
    subject_tree_digest: str
    subject_diff_digest: str
    observed_worktree_paths: tuple[str, ...] = field(default=())
    local_seal_digest: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialize to a dict. Deliberately omits remote HEAD fields."""

        return {
            "activation_base_sha": self.activation_base_sha,
            "subject_tree_digest": self.subject_tree_digest,
            "subject_diff_digest": self.subject_diff_digest,
            "observed_worktree_paths": list(self.observed_worktree_paths),
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
) -> ReportSubjectBinding:
    """Build a :class:`ReportSubjectBinding` from observed inputs.

    ``observed_worktree_paths`` is sorted before storage so that the
    binding is canonical regardless of caller iteration order.
    """

    return ReportSubjectBinding(
        activation_base_sha=activation_base_sha,
        subject_tree_digest=compute_subject_tree_digest(repo_root, subject_paths),
        subject_diff_digest=compute_subject_diff_digest(diff_text),
        observed_worktree_paths=tuple(sorted(observed_worktree_paths)),
        local_seal_digest=local_seal_digest,
    )
