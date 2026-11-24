"""Outbound alert delivery for unattended runs: a Windows toast per raised alert.

Best-effort and local: no network, no credentials. The text travels to the
notifier through environment variables, never through the command line, so an
alert detail cannot change the script that shows it.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Any, Callable, Mapping, Optional

LOG = logging.getLogger(__name__)

# Toasts need a registered AppUserModelID; Windows PowerShell's own is always present.
_APP_ID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
_SCRIPT = (
    "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;"
    "$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
    "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
    "$x = $t.GetElementsByTagName('text');"
    "$x.Item(0).AppendChild($t.CreateTextNode($env:NERELAN_TOAST_TITLE)) > $null;"
    "$x.Item(1).AppendChild($t.CreateTextNode($env:NERELAN_TOAST_BODY)) > $null;"
    "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($env:NERELAN_TOAST_APP).Show("
    "[Windows.UI.Notifications.ToastNotification]::new($t))"
)
NOTIFY_SEVERITIES = frozenset({"warning", "critical"})
MAX_TEXT = 200


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())[:MAX_TEXT]


def toast_sink(*, popen: Callable[..., Any] = subprocess.Popen,
               platform: str = sys.platform) -> Callable[[Mapping[str, Any]], None]:
    """Show one toast for each raised warning or critical alert; resolutions stay in the log."""

    def notify(event: Mapping[str, Any]) -> None:
        if event.get("event") != "raised" or event.get("severity") not in NOTIFY_SEVERITIES:
            return
        if platform != "win32":
            return
        environment = {**os.environ, "NERELAN_TOAST_APP": _APP_ID,
                       "NERELAN_TOAST_TITLE": _clean(f"Nerelan {event.get('severity')}: {event.get('code')}"),
                       "NERELAN_TOAST_BODY": _clean(event.get("detail") or event.get("subject"))}
        try:
            popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
                   "-Command", _SCRIPT], env=environment, stdin=subprocess.DEVNULL,
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError as exc:
            LOG.warning("alert toast not shown: %s", exc)

    return notify


def chain(*sinks: Optional[Callable[[Mapping[str, Any]], None]]) -> Optional[Callable[[Mapping[str, Any]], None]]:
    """One sink that feeds every given sink; one failing never stops the others."""
    present = [sink for sink in sinks if sink is not None]
    if not present:
        return None
    if len(present) == 1:
        return present[0]

    def deliver(event: Mapping[str, Any]) -> None:
        for sink in present:
            try:
                sink(event)
            except Exception:  # noqa: BLE001 - delivery is best-effort per sink
                LOG.warning("alert sink failed", exc_info=True)

    def close() -> None:
        for sink in present:
            closer = getattr(sink, "close", None)
            if closer is not None:
                closer()

    deliver.close = close  # type: ignore[attr-defined]
    return deliver
