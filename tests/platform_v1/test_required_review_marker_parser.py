from __future__ import annotations

import pytest

from reverse_agent.platform_v1.required_review_artifact import _parse_review_marker

SHA = "a" * 40
ACCEPT = f"Nerelan-Review: ACCEPT {SHA}"


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
