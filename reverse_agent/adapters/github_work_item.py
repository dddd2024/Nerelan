"""Fixture-only GitHub Work Item adapter."""

from __future__ import annotations

from typing import Any, Mapping

from reverse_agent.architecture.contracts import GitHubWorkItem


def load_github_work_item(payload: Mapping[str, Any]) -> GitHubWorkItem:
    return GitHubWorkItem.from_mapping(payload)
