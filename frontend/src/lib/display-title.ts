/**
 * Display titles for Goal/Task rows.
 *
 * The platform stores an execution title, not a display title: a task title is
 * built as `[<goal title>] T001 <boilerplate>\n\n<objective tail>`. Rendering
 * that verbatim turns a one-line row into a paragraph and gives every row an
 * accessible name measured in thousands of characters.
 *
 * This module derives the *short* semantic title used by compact rows and the
 * task header, and is the single source of that derivation: the same rule was
 * previously re-implemented ad hoc inside individual components.
 */

/** Bounded length for a compact row/header title. */
export const DISPLAY_TITLE_MAX = 80;

/** Plan step marker injected by the platform, e.g. `T001`, `T0123`. */
const STEP_MARKER = /^T\d{2,4}\b[\s:：·\-—]*/;

/** Fixed plan boilerplate that carries no user information. */
const BOILERPLATE = [
  /^Analyze,\s*implement,?\s*and\s*verify\s*the\s*goal\b[·:：\s-]*/i,
  /^Analyze\b[·:：\s-]*/i,
  /^分析[、，,]?\s*实现[、，,]?\s*(?:并)?验证(?:目标)?[·:：\s-]*/,
];

/** `.` `。` `；` `;` `,` `，` plus ASCII/ideographic spaces. */
const BREAK_BEFORE = /[\s。；;，,、）)】」]/;

function collapseWhitespace(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function stripPrefixes(value: string): string {
  let text = value;
  for (let guard = 0; guard < 6; guard += 1) {
    const before = text;
    text = text.replace(STEP_MARKER, "");
    for (const pattern of BOILERPLATE) text = text.replace(pattern, "");
    text = text.trim();
    if (text === before) break;
  }
  return text;
}

function bound(value: string, maxLength: number): string {
  if (value.length <= maxLength) return value;
  const slice = value.slice(0, maxLength);
  let cut = slice.length;
  for (let index = slice.length - 1; index >= Math.floor(maxLength * 0.5); index -= 1) {
    if (BREAK_BEFORE.test(slice[index])) {
      cut = index;
      break;
    }
  }
  return `${slice.slice(0, cut).trimEnd()}…`;
}

/**
 * Derive the short, human-readable title for a task or goal row.
 *
 * Order of preference:
 *   1. the `[...]` prefix, which is the human-authored goal title;
 *   2. the first paragraph of the raw title with the platform step markers and
 *      plan boilerplate removed;
 *   3. the raw title, bounded.
 */
export function displayTitle(
  raw: string | null | undefined,
  maxLength: number = DISPLAY_TITLE_MAX,
): string {
  if (!raw) return "";
  const firstParagraph = (raw.split(/\r?\n\s*\r?\n/)[0] ?? "").trim();
  const source = collapseWhitespace(firstParagraph);

  const bracketed = /^\[([^\]]{1,300})\]\s*/.exec(source);
  const bracketTitle = bracketed ? stripPrefixes(collapseWhitespace(bracketed[1])) : "";
  const stripped = stripPrefixes(bracketed ? source.slice(bracketed[0].length) : source);

  const candidate = bracketTitle || stripped || source;
  return bound(candidate, maxLength);
}

/**
 * Full normalized objective text, for progressive disclosure behind an
 * explicit "goal detail" affordance.
 */
export function displayObjective(raw: string | null | undefined): string {
  if (!raw) return "";
  const paragraphs = raw.split(/\r?\n\s*\r?\n/);
  const head = collapseWhitespace(paragraphs[0] ?? "");
  const body = paragraphs
    .slice(1)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .join("\n\n");
  const withoutBracket = head.replace(/^\[[^\]]{1,300}\]\s*/, "");
  return [collapseWhitespace(withoutBracket), body].filter(Boolean).join("\n\n");
}
