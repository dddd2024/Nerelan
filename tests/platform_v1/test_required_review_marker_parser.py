from __future__ import annotations

from html.parser import HTMLParser
from importlib.metadata import version
from pathlib import Path
import sys
import tomllib

from markdown_it import MarkdownIt
import pytest

from reverse_agent.platform_v1.required_review_artifact import _parse_review_marker

SHA = "a" * 40
ACCEPT = f"Nerelan-Review: ACCEPT {SHA}"


@pytest.fixture(autouse=True, params=["native", "batched", "until_close"])
def feed_mode(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> str:
    """Run every case on the installed stdlib and on controlled delayed feeds.

    A model only, NOT execution of an actual CPython 3.13.17 runtime: CI
    supplies that evidence. "batched" queues input after a stalled parse until
    as much again accumulates (the upstream 3.13.17 feed mitigation); public
    docs only promise that close() flushes buffered input, so "until_close"
    withholds every callback until close(). monkeypatch restores both.
    """
    if request.param == "native":
        return request.param
    original_feed, original_close = HTMLParser.feed, HTMLParser.close

    def deferred_feed(self: HTMLParser, text: str) -> None:
        chunks = getattr(self, "_probe_chunks", [])
        queued = getattr(self, "_probe_queued", 0) + len(text)
        chunks.append(text)
        self._probe_chunks = chunks  # type: ignore[attr-defined]
        self._probe_queued = queued  # type: ignore[attr-defined]
        if request.param == "until_close" or queued < getattr(self, "_probe_threshold", 1):
            return
        data = "".join(chunks)
        chunks.clear()
        self._probe_queued = 0  # type: ignore[attr-defined]
        before = len(self.rawdata) + len(data)
        original_feed(self, data)
        self._probe_threshold = (  # type: ignore[attr-defined]
            1 if len(self.rawdata) < before else len(self.rawdata))

    def deferred_close(self: HTMLParser) -> None:
        chunks = getattr(self, "_probe_chunks", [])
        if chunks:
            data = "".join(chunks)
            chunks.clear()
            self._probe_queued = 0  # type: ignore[attr-defined]
            original_feed(self, data)
        original_close(self)

    monkeypatch.setattr(HTMLParser, "feed", deferred_feed)
    monkeypatch.setattr(HTMLParser, "close", deferred_close)
    return request.param


def test_feed_model_really_withholds_callbacks_until_close(feed_mode: str) -> None:
    class Recorder(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=False)
            self.tags: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            self.tags.append(tag)

    parser = Recorder()
    for chunk in ['<span title="\n', ACCEPT + "\n", '">\n']:
        parser.feed(chunk)
    if feed_mode == "until_close":
        # The completed tag is still queued: feed gave no callback guarantee.
        # ("batched" queues it too, but its accounting reads the installed
        # runtime's buffer, so only this mode is asserted on every runtime.)
        assert parser.tags == []
    parser.close()
    assert parser.tags == ["span"]


def test_genuine_live_marker_accepted() -> None:
    assert _parse_review_marker(ACCEPT) == (("ACCEPT", SHA), "")


def test_nested_html_fake_only_rejected() -> None:
    content = "\n".join(["<pre>", "<code>", ACCEPT, "</code>", "</pre>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_inner_code_close_does_not_exit_outer_pre() -> None:
    # Regression: a single bool cleared at the inner </code> while the outer
    # <pre> was still open, letting this quoted ACCEPT falsely count as live.
    content = "\n".join(["<pre>", "<code>", ACCEPT, "</code>", ACCEPT, "</pre>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_closed_nested_then_outside_marker_accepted() -> None:
    content = "\n".join(["<pre>", "<code>", ACCEPT, "</code>", "</pre>", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_unclosed_pre_refused() -> None:
    marker, error = _parse_review_marker("\n".join(["<pre>", ACCEPT]))
    assert marker is None
    assert error == "review_html_code_unclosed"


def test_unclosed_code_refused() -> None:
    marker, error = _parse_review_marker("\n".join(["<pre>", "<code>", ACCEPT]))
    assert marker is None
    assert error == "review_html_code_unclosed"


def test_mismatched_close_refused() -> None:
    marker, error = _parse_review_marker("\n".join(["<pre>", "<code>", ACCEPT, "</pre>"]))
    assert marker is None
    assert error == "review_html_code_mismatched"


def test_mismatched_wrong_close_refused() -> None:
    marker, error = _parse_review_marker("\n".join(["<pre>", "</code>", ACCEPT]))
    assert marker is None
    assert error == "review_html_code_mismatched"


def test_fenced_fake_ignored() -> None:
    marker, error = _parse_review_marker("\n".join(["```", ACCEPT, "```"]))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_fenced_html_fake_ignored() -> None:
    marker, error = _parse_review_marker(
        "\n".join(["```", "<pre>", ACCEPT, "</pre>", "```"])
    )
    assert marker is None
    assert error


def test_comment_fake_ignored() -> None:
    marker, error = _parse_review_marker(f"<!-- {ACCEPT} -->")
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_indented_fake_ignored() -> None:
    marker, error = _parse_review_marker(f"    {ACCEPT}")
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_fence_unclosed_refused() -> None:
    marker, error = _parse_review_marker("\n".join(["```", ACCEPT]))
    assert marker is None
    assert error == "review_fence_unclosed"


def test_comment_unclosed_refused() -> None:
    marker, error = _parse_review_marker(f"<!-- {ACCEPT}")
    assert marker is None
    assert error == "review_comment_unclosed"


def test_ambiguous_multiple_markers_refused() -> None:
    marker, error = _parse_review_marker("\n".join([ACCEPT, ACCEPT]))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_explicit_failure_outcome_refused() -> None:
    marker, error = _parse_review_marker(f"Outcome: REJECT\n{ACCEPT}")
    assert marker is None
    assert error == "review_explicit_failure_outcome"


def test_stray_close_does_not_reject_genuine() -> None:
    assert _parse_review_marker("\n".join(["</pre>", ACCEPT])) == (("ACCEPT", SHA), "")


def test_attribute_text_does_not_close_pre() -> None:
    # A literal "</pre>" inside a quoted attribute value is attribute text, not
    # a close tag: the surrounding <pre> stays open and the fake ACCEPT inside
    # it is not live.
    content = "\n".join([
        "<pre>",
        '<span title="</pre>">example</span>',
        ACCEPT,
        "</pre>",
    ])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_html_literal_inside_markdown_fence_does_not_hide_live_verdict() -> None:
    # A literal unclosed <pre> inside a fenced Markdown example is example text:
    # it must not open a real HTML block, so the genuine ACCEPT outside the
    # fence still counts.
    content = "\n".join([
        "```html",
        "<pre>",
        ACCEPT,
        "```",
        ACCEPT,
    ])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_markdown_fence_close_with_content_does_not_hide_live_verdict() -> None:
    # Positive control: the fence must actually close before the live verdict,
    # even when the example contains pre/code-looking HTML.
    content = "\n".join([
        "```",
        "<pre>",
        "<code>",
        ACCEPT,
        "</code>",
        "</pre>",
        "```",
        ACCEPT,
    ])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_multiline_attribute_does_not_close_pre() -> None:
    # A literal "</pre>" inside a quoted attribute value that itself spans
    # lines is attribute text, not a close tag: the surrounding <pre> stays
    # open and the fake ACCEPT inside it is not live.
    content = "\n".join([
        "<pre>",
        '<span title="',
        "</pre>",
        '">example</span>',
        ACCEPT,
        "</pre>",
    ])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_multiline_pre_opener_excludes_marker() -> None:
    # A <pre opener split over a newline still opens the block when its ">"
    # arrives; a marker line before the opener completes is inside an unfinished
    # tag and must not count as live.
    content = "\n".join([
        "<pre",
        ' class="example">',
        ACCEPT,
        "</pre>",
    ])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_marker_inside_unfinished_non_block_tag_excluded() -> None:
    # A marker line inside an unfinished (non pre/code) tag is lexically inside
    # the tag, not a top-level verdict line: it must not count as live even
    # though the tag later completes and the file ends cleanly.
    content = "\n".join([
        '<span title="',
        ACCEPT,
        '">',
    ])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_unfinished_tag_fail_closed() -> None:
    # An unfinished HTML tag that never closes fails closed: the marker line
    # inside it is not a declaration and the unclosed tag is refused.
    content = "\n".join([
        '<span title="',
        ACCEPT,
    ])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_html_code_unclosed"


def test_comment_literal_in_fence_does_not_hide_real_marker() -> None:
    # A literal "<!--" inside a fenced Markdown example is example text, not a
    # comment: it must not open a comment that hides the genuine ACCEPT below.
    content = "\n".join([
        "```html",
        "<!--",
        "```",
        ACCEPT,
    ])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_live_marker_after_comment_and_fence_literals_accepted() -> None:
    # Positive control: comment and fenced literals never mask a genuine live
    # verdict, and a raw standalone marker outside every context still counts.
    content = "\n".join([
        "<!-- example -->",
        "```",
        "Nerelan-Review: ACCEPT " + "a" * 40,
        "```",
        ACCEPT,
    ])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_newline_is_not_removed_from_partial_tag() -> None:
    # Regression: lines were fed without their terminator, so "<pre" and
    # 'class=...' fused into an unknown "<preclass" tag and the fake counted.
    content = "\n".join(["<pre", 'class="example">', ACCEPT, "</pre>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_crlf_partial_tag_keeps_lexical_separation() -> None:
    content = "\r\n".join(["<pre", 'class="example">', ACCEPT, "</pre>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_comment_on_pre_opening_line_does_not_erase_the_tag() -> None:
    # Regression: a comment sharing the line used to skip the real <pre>.
    content = "\n".join(["<pre><!-- note -->", ACCEPT, "</pre>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_comment_before_pre_does_not_erase_the_tag() -> None:
    content = "\n".join(["<!-- note --><pre>", ACCEPT, "</pre>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error


def test_second_unclosed_comment_fails_closed() -> None:
    # Regression: only the first "-->" after the first "<!--" was checked.
    marker, error = _parse_review_marker("\n".join([ACCEPT, "<!-- one --><!-- unclosed"]))
    assert marker is None
    assert error == "review_comment_unclosed"


def test_unclosed_comment_after_closed_comment_hides_later_marker() -> None:
    content = "\n".join(["<!-- one --><!-- open", ACCEPT, "-->"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_stray_comment_close_refused() -> None:
    marker, error = _parse_review_marker("\n".join(["-->", ACCEPT]))
    assert marker is None
    assert error == "review_comment_unclosed"


def test_closed_comment_and_real_outside_marker_accepted() -> None:
    content = "\n".join(["<!-- note -->", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_closed_comment_and_closed_pre_on_one_line_then_live_marker_accepted() -> None:
    content = "\n".join(["<!-- note --><pre>example</pre><!-- two -->", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_multiline_pre_opener_then_outside_marker_accepted() -> None:
    content = "\n".join(["<pre", 'class="example">', "example", "</pre>", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_fence_inside_real_pre_is_inert() -> None:
    # A Markdown fence inside a real <pre> is literal text: it neither opens a
    # fence nor makes the fake marker inside the block live.
    content = "\n".join(["<pre>", "```", ACCEPT, "```", "</pre>", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_fence_inside_real_comment_is_inert() -> None:
    content = "\n".join(["<!--", "```", "-->", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_escaped_marker_is_never_decoded() -> None:
    content = "Nerelan-Review: &#65;CCEPT " + SHA
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_live_marker_beside_closed_example_and_duplicate_live_refused() -> None:
    content = "\n".join(["<pre>", ACCEPT, "</pre>", ACCEPT, ACCEPT])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


@pytest.mark.parametrize("tag", ["script", "style", "SCRIPT"])
def test_script_style_raw_text_fake_only_is_not_live(tag: str) -> None:
    # Regression: HTMLParser raw-text state was ignored, so this was live.
    marker, error = _parse_review_marker(f"<{tag}>\n{ACCEPT}\n</{tag}>")
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_self_closing_script_still_opens_raw_text() -> None:
    marker, error = _parse_review_marker(f"<script/>\n{ACCEPT}\n</script>")
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_unclosed_script_fails_closed() -> None:
    marker, error = _parse_review_marker(f"<script>\n{ACCEPT}\n")
    assert marker is None
    assert error == "review_html_code_unclosed"


def test_closed_script_style_examples_then_live_marker_accepted() -> None:
    # Fences, comment closers and pre tags inside raw text are inert data.
    content = "\n".join([
        "<script>", "```", "if (a --> b) {}", "<pre>", ACCEPT, "</script>",
        "<style>", "/* <!-- */", ACCEPT, "</style>",
        ACCEPT,
    ])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_script_literal_inside_comment_fence_and_pre_keeps_priority() -> None:
    content = "\n".join([
        "<!-- <script> -->",
        "```html", "<script>", "```",
        "<pre>", "<script>", ACCEPT, "</script>", "</pre>",
        ACCEPT,
    ])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("delimiter", ["`", "``"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_multiline_inline_code_fake_only_is_not_live(delimiter: str, newline: str) -> None:
    # Regression: a code span continuing across line ends was ignored.
    marker, error = _parse_review_marker(newline.join([delimiter, ACCEPT, delimiter]))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


@pytest.mark.parametrize("delimiter", ["`", "``"])
def test_closed_multiline_code_span_then_live_marker_accepted(delimiter: str) -> None:
    content = "\n".join([f"Example {delimiter}code", ACCEPT, f"end{delimiter} done", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_code_span_closes_only_on_exact_backtick_run() -> None:
    # A two-backtick run does not close a one-backtick span, nor vice versa.
    marker, error = _parse_review_marker("\n".join(["`", ACCEPT, "``", ACCEPT, "`"]))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"
    content = "\n".join(["``", ACCEPT, "`", "``", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_inline_code_on_one_line_does_not_hide_live_marker() -> None:
    assert _parse_review_marker("\n".join(["Use `x` and ``y``.", ACCEPT])) == (("ACCEPT", SHA), "")


def test_stray_backtick_before_paragraph_break_does_not_hide_live_marker() -> None:
    assert _parse_review_marker("\n".join(["Stray ` here", "", ACCEPT, "`"])) == (("ACCEPT", SHA), "")


def test_escaped_backtick_does_not_open_code_span() -> None:
    content = "\n".join(["Literal \\` tick", ACCEPT, "`"])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_backtick_in_fence_or_comment_does_not_open_code_span() -> None:
    content = "\n".join(["```", "`", "```", "<!-- ` -->", ACCEPT, "`"])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_html_inside_multiline_code_span_is_inert() -> None:
    content = "\n".join(["`", "see <pre> and <!-- here", "`", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


FAKE = ACCEPT.replace(SHA, "b" * 40)


def _html_literal_in_code(tag: str, where: str) -> str:
    if where == "opening":
        return f"`{tag}\n{FAKE}\n`\n"
    return f"`\n{FAKE}\n{tag}`\n"


@pytest.mark.parametrize("tag", ["<pre>", "<!--"])
@pytest.mark.parametrize("where", ["opening", "closing"])
def test_html_literal_on_code_span_edge_line_does_not_leak(tag: str, where: str) -> None:
    # Regression: the opening line was fed whole to the HTML lexer, and the
    # closing line's literal code prefix too, so a code-literal <pre>/<!--
    # opened a real block that hid the genuine verdict after the span.
    content = _html_literal_in_code(tag, where) + ACCEPT + "\n"
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("tag", ["<pre>", "<!--"])
@pytest.mark.parametrize("where", ["opening", "closing"])
def test_html_literal_on_code_span_edge_line_fake_only_is_not_live(tag: str, where: str) -> None:
    marker, error = _parse_review_marker(_html_literal_in_code(tag, where))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_html_literal_in_single_line_code_span_is_inert() -> None:
    content = "\n".join(["Use `<pre>` and ``<!--`` here.", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_real_html_after_closed_code_span_still_opens_block() -> None:
    content = "\n".join(["`", FAKE, "` <pre>", ACCEPT, "</pre>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_code_span_cannot_close_on_fence_line() -> None:
    content = "\n".join(["x ```", "```", ACCEPT, "```", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_code_span_cannot_cross_real_script_block_start() -> None:
    # The <script> line interrupts the paragraph: the backtick is literal and
    # the raw-text block, not a code span, decides that the fake is inert.
    content = "\n".join(["x `", "<script>", "`", ACCEPT, "</script>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_multiline_code_span_inside_pre_is_not_tracked() -> None:
    content = "\n".join(["<pre>", "`", "</pre>", ACCEPT, "`"])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_multiline_attribute_then_outside_marker_accepted() -> None:
    # Positive control: once the real </pre> arrives the multiline quoted
    # attribute is fully closed, so a genuine ACCEPT after it is live.
    content = "\n".join([
        "<pre>",
        '<span title="',
        "</pre>",
        '">example</span>',
        "</pre>",
        ACCEPT,
    ])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("tag", ["blockquote", "BLOCKQUOTE", "q"])
def test_html_quotation_sole_marker_is_not_live(tag: str) -> None:
    # Regression from independent REJECT at ef658f6e: quoted report text was live.
    marker, error = _parse_review_marker(f"<{tag}>\n{ACCEPT}\n</{tag}>\n")
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_inner_quote_close_does_not_exit_outer_quote() -> None:
    content = "\n".join(["<blockquote>", "<blockquote>", FAKE, "</blockquote>",
                         ACCEPT, "</blockquote>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


def test_unclosed_quote_fails_closed() -> None:
    marker, error = _parse_review_marker("\n".join(["<blockquote>", ACCEPT]))
    assert marker is None
    assert error == "review_html_code_unclosed"


def test_genuine_marker_after_closed_quote_with_stale_markers_accepted() -> None:
    content = "\n".join(["<blockquote>", "<blockquote>", ACCEPT, "</blockquote>",
                         FAKE, ACCEPT.replace("ACCEPT", "REJECT"), "</blockquote>",
                         ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_comment_adjacent_to_quote_keeps_the_tag() -> None:
    marker, error = _parse_review_marker("\n".join(["<!-- note --><blockquote>", ACCEPT,
                                                    "</blockquote>"]))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"
    content = "\n".join(["<blockquote><!-- note --></blockquote><!-- two -->", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_multiline_quote_attribute_does_not_close_quote() -> None:
    lines = ['<blockquote cite="', "</blockquote>", '">', ACCEPT, "</blockquote>"]
    marker, error = _parse_review_marker("\n".join(lines))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"
    assert _parse_review_marker("\n".join(lines + [ACCEPT])) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("content", [
    "Use `<blockquote>` here.\n",
    "See `quoted <blockquote>\n" + ACCEPT + "\n</blockquote>` end\n",
    "```html\n<blockquote>\n" + ACCEPT + "\n```\n",
    "~~~\n<q>\n~~~\n",
])
def test_quote_markup_inside_code_is_inert(content: str) -> None:
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"
    assert _parse_review_marker(content + ACCEPT + "\n") == (("ACCEPT", SHA), "")


def test_code_span_cannot_cross_real_blockquote_block_start() -> None:
    content = "\n".join(["x `", "<blockquote>", "`", ACCEPT, "</blockquote>"])
    marker, error = _parse_review_marker(content)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


@pytest.mark.parametrize("opener", ["<blockquote/>", "<blockquote />", "<pre/>",
                                    "<code/>", "<q/>"])
def test_self_closing_container_does_not_close_empty(opener: str) -> None:
    # Browsers ignore "/>" on non-void elements; the container stays open.
    marker, error = _parse_review_marker(f"{opener}\n{ACCEPT}\n")
    assert marker is None
    assert error == "review_html_code_unclosed"
    tag = opener.strip("</ >")
    content = f"{opener}\n{FAKE}\n</{tag}>\n{ACCEPT}\n"
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


# The eight cases that failed on CI's delayed stdlib feed: (lines whose last
# line closes the lexical context, typed reason once that line is missing).
DELAYED_FEED_CASES = {
    "unfinished_tag": (['<span title="', FAKE, '">'], "review_html_code_unclosed"),
    "comment_after_comment": (["<!-- one --><!-- open", FAKE, "-->"],
                              "review_comment_unclosed"),
    "script": (["<script>", FAKE, "</script>"], "review_html_code_unclosed"),
    "style": (["<style>", FAKE, "</style>"], "review_html_code_unclosed"),
    "SCRIPT": (["<SCRIPT>", FAKE, "</SCRIPT>"], "review_html_code_unclosed"),
    "self_closing_script": (["<script/>", FAKE, "</script>"], "review_html_code_unclosed"),
    "priority": (["<!-- <script> -->", "```html", "<script>", "```", "<pre>", "<script>",
                  FAKE, "</script>", "</pre>"], "review_html_code_unclosed"),
    "span_vs_script": (["x `", "<script>", "`", FAKE, "</script>"],
                       "review_html_code_unclosed"),
}


@pytest.mark.parametrize("case", sorted(DELAYED_FEED_CASES))
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_delayed_feed_closed_contexts_keep_typed_reasons(case: str, newline: str) -> None:
    lines, unclosed = DELAYED_FEED_CASES[case]
    # Only-fake control: the closed context hides the fake, nothing is live.
    marker, error = _parse_review_marker(newline.join(lines) + newline)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"
    # A genuine marker outside the closed context is accepted.
    content = newline.join([*lines, ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    # A genuine marker inside the context is still not live.
    inside = [ACCEPT if line == FAKE else line for line in lines]
    marker, error = _parse_review_marker(newline.join(inside))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"
    # Without its closing line the context fails closed, even with a marker after.
    marker, error = _parse_review_marker(newline.join([*lines[:-1], ACCEPT]))
    assert marker is None
    assert error == unclosed


@pytest.mark.parametrize("closer", ["</script>", "</script >", "</SCRIPT\n>",
                                    '</script x=">">'])
def test_raw_text_close_tag_split_across_lines_is_recognized(closer: str) -> None:
    content = "\n".join(["<script>", "</scrip", FAKE, closer, ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_long_unfinished_attribute_stays_inside_tag_across_many_lines() -> None:
    lines = ['<span title="', *[FAKE] * 200, ACCEPT, '">']
    marker, error = _parse_review_marker("\n".join(lines))
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"
    assert _parse_review_marker("\n".join([*lines, ACCEPT])) == (("ACCEPT", SHA), "")


# Regression from independent REJECT at 93944f56: an unprefixed line lazily
# continuing a quoted paragraph is quoted text, not a live verdict.
LAZY_QUOTES = {
    "lazy": ["> Earlier quoted template:"],
    "continued": ["> Earlier quoted template:", "> continuing quotation"],
    "nested": ["> > Outer template:", "> inner"],
    "indented_prefix": ["   > Earlier quoted template:"],
    "lazy_text_first": ["> Earlier quoted template:", "still quoted text"],
    "quoted_list_item": ["> - quoted item"],
    "code_span": ["> see `multi", "line` span"],
    "inline_html": ["> quoted <code>inline", "more</code> text"],
}


@pytest.mark.parametrize("case", sorted(LAZY_QUOTES))
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_lazy_quote_continuation_marker_is_not_live(case: str, newline: str) -> None:
    quote = LAZY_QUOTES[case]
    marker, error = _parse_review_marker(newline.join([*quote, ACCEPT]) + newline)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"
    # A lazy quoted fake never counts beside a genuine marker after a blank line.
    content = newline.join([*quote, FAKE, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("separator", [
    [""], ["   "], ["# Current review"], ["## Current review"], ["---"], ["***"],
    ["- note"], ["1. note"], ["```", FAKE, "```"], ["<pre>", FAKE, "</pre>"],
    ["<!-- note -->"],
])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_terminated_quote_then_outside_marker_accepted(separator: list[str],
                                                       newline: str) -> None:
    lines = ["> Earlier quoted template:", "> " + FAKE, *separator, ACCEPT]
    assert _parse_review_marker(newline.join(lines) + newline) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("quote", [
    [">"], ["> "], ["> # Quoted heading"], ["> ```", "> " + FAKE, "> ```"],
    ["> ---"], [">     quoted code"],
])
def test_quote_without_open_paragraph_has_no_lazy_continuation(quote: list[str]) -> None:
    assert _parse_review_marker("\n".join([*quote, ACCEPT])) == (("ACCEPT", SHA), "")


def test_ordinary_lists_are_not_quotes() -> None:
    content = "\n".join(["- point", "* other", "+ more", "1. item", "", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    content = "\n".join(["Summary:", "- point a > b", "", ACCEPT])
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_lazy_quoted_failure_outcome_still_refused() -> None:
    content = "\n".join(["> Template:", "Outcome: REJECT", "", ACCEPT])
    assert _parse_review_marker(content) == (None, "review_explicit_failure_outcome")


# Regression from independent REJECT at f3dde86a: an invalid backtick fence
# (info string containing a backtick) is quoted paragraph text, and a Setext
# underline only completes a quoted paragraph at its own quote depth.
STILL_QUOTED = {
    "invalid_fence_info": ["> ```foo`"],
    "invalid_fence_info_nested": ["> > ```foo`"],
    "invalid_fence_info_spaced": ["> ``` foo`bar"],
    "lazy_after_invalid_fence": ["> quote", "> ```foo`"],
    "standalone_setext_underline": ["> ==="],
    "nested_standalone_setext_underline": ["> > ==="],
    "lazy_setext_underline": ["> quote", "==="],
    "shallower_setext_underline": ["> > quote", "> ==="],
    "deeper_setext_underline": ["> quote", "> > ==="],
    "plain": ["> quote"],
    "nested_plain": ["> > quote"],
}


@pytest.mark.parametrize("case", sorted(STILL_QUOTED))
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_quoted_paragraph_text_keeps_lazy_marker_quoted(case: str, newline: str) -> None:
    quote = STILL_QUOTED[case]
    content = newline.join([*quote, ACCEPT]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    # A genuine marker after the quote is terminated still counts.
    content = newline.join([*quote, FAKE, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("quote", [
    ["> ```foo`", ""], ["> > ```foo`", ""], ["> ``` foo`bar", ""],
    ["> quote", "> ==="], ["> quote", "> ---"], ["> quote", "> -"],
    ["> quote", ">    =  "], ["> > quote", "> > ==="], ["> quote", "> more", "> ==="],
    ["> ~~~foo"], ["> ~~~foo`bar"], ["> ```foo"], ["> ```"], ["> > ~~~foo"],
])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_terminated_quote_paragraph_then_outside_marker_accepted(quote: list[str],
                                                                 newline: str) -> None:
    content = newline.join([*quote, ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    # A quoted template beside the genuine marker is still not a declaration.
    content = newline.join([*quote, ">", "> " + FAKE, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


# Regression from independent REJECT at af7cd119: a quoted link reference
# definition is not a paragraph, so the CommonMark quote ends on its line and
# an immediately following unprefixed marker is outside the quote.
@pytest.mark.parametrize("quote", [
    ["> [link]: /example"], ["> > [link]: /example"],
    ['> [link]: /example "title"'], ["> quote", ">", "> [link]: /example"],
])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_quoted_link_definition_then_outside_marker_accepted(quote: list[str],
                                                             newline: str) -> None:
    content = newline.join([*quote, ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    marker, error = _parse_review_marker(newline.join(quote) + newline)
    assert marker is None
    assert error == "review_verdict_missing_or_ambiguous"


@pytest.mark.parametrize("quote", [
    ["> [link]: /example", "> definition followed by text"],
    ["> [not a definition] text"], ["> [link]:"], ["> > [link] /example"],
])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_quoted_link_lookalike_paragraph_keeps_lazy_marker_quoted(quote: list[str],
                                                                 newline: str) -> None:
    content = newline.join([*quote, ACCEPT]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    content = newline.join([*quote, FAKE, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("depth", [20, 50, 100])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_deeply_nested_quote_bounds(depth: int, newline: str) -> None:
    quote = "> " * depth
    # A lazy line after a deep quote and a fake inside it are never live.
    content = newline.join([quote + "deep template", ACCEPT]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    content = newline.join([quote + FAKE]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    # A blank line ends every level; the genuine marker after it counts.
    content = newline.join([quote + FAKE, quote + "more", "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("separator", [chr(0x2028), chr(0x85), chr(0x0C)])
def test_non_commonmark_line_separator_never_splits_a_quoted_line(separator: str) -> None:
    # CommonMark breaks lines only on CR/LF; an original line after U+2028,
    # NEL or form feed still lies inside the quoted parser line.
    content = f"> quote{separator}{ACCEPT}\n"
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    content = f"> quote{separator}{FAKE}\n\n{ACCEPT}\n"
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


# Regression from independent REJECT at 7d31e90c: quote syntax inside a closed
# lexical literal opened a CommonMark quote that lazily swallowed the genuine
# marker after the literal. Each case: (opening line, literal lines, closing).
LITERAL_SEAMS = {
    "double_attribute": ['<span title="', "> template", '">'],
    "single_attribute": ["<span title='", "> template", "'>"],
    "code_span": ["`", "> template", "`"],
    "double_code_span": ["see ``code", "> template", "end`` done"],
    "comment": ["Note <!--", "> template", "-->"],
    "pre": ["Note <pre>", "> template", "</pre>"],
    "script": ["Note <script>", "> template", "</script>"],
    "q": ["Note <q>", "> template", "</q>"],
}


@pytest.mark.parametrize("case", sorted(LITERAL_SEAMS))
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_quote_syntax_inside_closed_literal_does_not_quote_later_marker(
        case: str, newline: str) -> None:
    seam = LITERAL_SEAMS[case]
    content = newline.join([*seam, ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    content = newline.join([*seam, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    # The literal itself still hides a marker inside it.
    content = newline.join([seam[0], seam[1], ACCEPT, seam[2]]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")


@pytest.mark.parametrize("case", sorted(LITERAL_SEAMS))
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_real_quote_after_closed_literal_still_quotes_lazy_marker(
        case: str, newline: str) -> None:
    seam = LITERAL_SEAMS[case]
    content = newline.join([*seam, "> real quote", ACCEPT]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    # The real quote covers a lazy fake; a blank line ends it before the genuine one.
    content = newline.join([*seam, "> real quote", FAKE, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_quote_syntax_after_blank_line_inside_literal_stays_literal() -> None:
    content = "\n".join(['<span title="', "", "> template", '">', ACCEPT]) + "\n"
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    content = "\n".join(['<span title="', "", "> template", '">', "> real", ACCEPT]) + "\n"
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")


def test_plain_closed_attribute_with_quote_character_keeps_marker_live() -> None:
    content = '<span title="quoted > template">\n' + ACCEPT + "\n"
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


def test_real_quote_containing_literal_keeps_its_lazy_continuation() -> None:
    # A quote opened before the literal still lazily covers the marker after it.
    content = "\n".join(['> quoted <span title="', "> template", '">', ACCEPT]) + "\n"
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    content = "\n".join(["> quoted `code", "> template", "end`", ACCEPT]) + "\n"
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")


_CAP = 128 * 1024


def _near_cap(unit: str, tail: str) -> str:
    content = unit * ((_CAP - len(tail.encode("utf-8"))) // len(unit.encode("utf-8"))) + tail
    assert _CAP - len(unit.encode("utf-8")) < len(content.encode("utf-8")) <= _CAP
    return content


@pytest.mark.parametrize("unit", [
    "> " * 100 + "deep quoted template\n",
    "> quoted template\n\n",
    "plain paragraph text\n",
])
def test_near_byte_cap_quotes_keep_exact_boundaries(unit: str) -> None:
    # No timing claim: a report at the read cap still gets the exact verdict.
    lazy = _near_cap(unit, "> template\n" + ACCEPT + "\n")
    assert _parse_review_marker(lazy) == (None, "review_verdict_missing_or_ambiguous")
    outside = _near_cap(unit, "\n" + ACCEPT + "\n")
    assert _parse_review_marker(outside) == (("ACCEPT", SHA), "")


def test_missing_markdown_parser_fails_closed_without_fallback(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "markdown_it", None)
    assert _parse_review_marker(ACCEPT + "\n") == (None, "review_markdown_parser_unavailable")


def test_markdown_parser_error_fails_closed_without_fallback(
        monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(self: MarkdownIt, src: str, env: object = None) -> list[object]:
        raise RuntimeError("parser failure")

    monkeypatch.setattr(MarkdownIt, "parse", broken)
    assert _parse_review_marker(ACCEPT + "\n") == (None, "review_markdown_parse_failed")


def test_markdown_parser_is_a_pinned_runtime_dependency() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    project = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]
    assert "markdown-it-py==4.0.0" in project["dependencies"]
    assert version("markdown-it-py") == "4.0.0"


# Regression from independent REJECT at 11c328ce: the host HTML lexer closed a
# line-start HTML container, but the parser's own HTML block outlived the close
# and swallowed the real quote after it, so its lazy fake passed as genuine.
CLOSED_HTML_SEAMS = {
    "blockquote": ["<blockquote>", "> literal", "</blockquote>"],
    "code": ["<code>", "> literal", "</code>"],
    "q": ["<q>", "> literal", "</q>"],
    "script_split_close": ["<script>", "> literal", "</script", ">"],
    "style_split_close": ["<style>", "> literal", "</style", ">"],
    "pre_split_close": ["<pre>", "> literal", "</pre", ">"],
}


@pytest.mark.parametrize("case", sorted(CLOSED_HTML_SEAMS))
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_real_quote_after_closed_line_start_html_quotes_lazy_marker(
        case: str, newline: str) -> None:
    seam = CLOSED_HTML_SEAMS[case]
    content = newline.join([*seam, "> real quote", ACCEPT]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    # The real quote covers a lazy fake; a blank line ends it before the genuine one.
    content = newline.join([*seam, "> real quote", FAKE, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("case", sorted(CLOSED_HTML_SEAMS))
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_genuine_marker_after_closed_line_start_html_is_live(
        case: str, newline: str) -> None:
    seam = CLOSED_HTML_SEAMS[case]
    content = newline.join([*seam, ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    content = newline.join([*seam, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    # The container itself still hides a marker inside it.
    content = newline.join([seam[0], seam[1], ACCEPT, *seam[2:]]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")


@pytest.mark.parametrize("case", sorted(CLOSED_HTML_SEAMS))
def test_unclosed_line_start_html_before_real_quote_fails_closed(case: str) -> None:
    seam = CLOSED_HTML_SEAMS[case]
    content = "\n".join([seam[0], seam[1], "> real quote", ACCEPT]) + "\n"
    assert _parse_review_marker(content)[0] is None


# Regression from FAILED candidate 55b26f57: with the parser's HTML rules off,
# a real line-start HTML block no longer interrupted an earlier quoted
# paragraph, so the genuine marker after the closed block stayed lazily quoted.
INTERRUPTING_HTML = {
    "pre": ["<pre>", FAKE, "</pre>"],
    "comment": ["<!-- note -->"],
    "multiline_comment": ["<!--", FAKE, "-->"],
    "script": ["<script>", FAKE, "</script>"],
    "style_split_close": ["<style>", FAKE, "</style", ">"],
    "blockquote": ["<blockquote>", "> " + FAKE, "</blockquote>"],
    "indented_upper_pre": ["   <PRE class=x>", FAKE, "</PRE>"],
}
QUOTES_BEFORE_HTML = {
    "plain": ["> Earlier quoted template:", "> " + FAKE],
    "lazy": ["> Earlier quoted template:", "still quoted text"],
    "nested": ["> > Outer template:", "> " + FAKE],
    "deep": ["> " * 50 + "deep template"],
}


@pytest.mark.parametrize("case", sorted(INTERRUPTING_HTML))
@pytest.mark.parametrize("quote", sorted(QUOTES_BEFORE_HTML))
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_line_start_html_block_interrupts_earlier_quote(case: str, quote: str,
                                                         newline: str) -> None:
    seam, before = INTERRUPTING_HTML[case], QUOTES_BEFORE_HTML[quote]
    content = newline.join([*before, *seam, ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    # A real quote opened after the closed block still lazily covers the marker.
    content = newline.join([*before, *seam, "> real quote", ACCEPT]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    content = newline.join([*before, *seam, "> real quote", FAKE, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
    if len(seam) > 1:
        # The block itself still hides a marker inside it.
        content = newline.join([*before, seam[0], ACCEPT, *seam[2:]]) + newline
        assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")


@pytest.mark.parametrize("seam", [
    ["Note <pre>", FAKE, "</pre>"], ["<code>", FAKE, "</code>"],
    ["<q>inline</q> text"], ['<span title="x">inline</span>'],
    ['<span title="', "> template", '">'], ["`", "> template", "`"],
])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_inline_html_or_code_span_does_not_interrupt_quote(seam: list[str],
                                                           newline: str) -> None:
    content = newline.join(["> quote", *seam, ACCEPT]) + newline
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    content = newline.join(["> quote", *seam, FAKE, "", ACCEPT]) + newline
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")


@pytest.mark.parametrize("separator", [chr(0x2028), chr(0x85), chr(0x0C)])
def test_html_start_after_non_commonmark_separator_never_ends_quote(separator: str) -> None:
    # "<pre>" after U+2028, NEL or form feed is not at a CommonMark line start:
    # it stays inside the quoted parser line, so no boundary is synthesized.
    content = f"> quote{separator}<pre>\n{FAKE}\n</pre>\n{ACCEPT}\n"
    assert _parse_review_marker(content) == (None, "review_verdict_missing_or_ambiguous")
    content = f"> quote{separator}<pre>\n{FAKE}\n</pre>\n\n{ACCEPT}\n"
    assert _parse_review_marker(content) == (("ACCEPT", SHA), "")
