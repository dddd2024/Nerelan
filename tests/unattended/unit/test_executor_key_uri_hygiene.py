from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

_SCRIPT = (
    Path(__file__).parents[3]
    / "deploy"
    / "unattended"
    / "litellm-key-bootstrap.py"
)
_EXECUTOR_KEY = "sk-synthetic-executor-key-material"


class _Response:
    status = 200

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return b'{"info": {}}'


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("litellm_key_bootstrap", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_executor_key_is_bearer_only_and_never_in_uri(
    monkeypatch,
) -> None:
    module = _module()
    observed: list[object] = []

    def fake_urlopen(request, timeout: int):
        observed.append(request)
        assert timeout == 30
        return _Response()

    monkeypatch.setattr(module, "urlopen", fake_urlopen)
    module._request("GET", "/key/info", bearer=_EXECUTOR_KEY)

    assert len(observed) == 1
    request = observed[0]
    assert _EXECUTOR_KEY not in request.full_url
    assert request.full_url.endswith("/key/info")
    assert request.get_header("Authorization") == f"Bearer {_EXECUTOR_KEY}"
