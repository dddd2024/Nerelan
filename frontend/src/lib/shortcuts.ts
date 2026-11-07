const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);

/** Shortcut label for this platform, for example `Ctrl K` or `⌘K`. */
export function shortcutLabel(key: string): string {
  return isMac ? `⌘${key}` : `Ctrl ${key}`;
}

/**
 * The platform's primary modifier plus exactly `key`.
 *
 * Shift and Alt are excluded so a different chord is not swallowed. On macOS
 * only Command counts: Ctrl+B and Ctrl+K are native text-editing keys there.
 */
export function isPrimaryShortcut(event: KeyboardEvent, key: string): boolean {
  const primary = isMac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey;
  return primary && !event.shiftKey && !event.altKey && event.key.toLowerCase() === key;
}
