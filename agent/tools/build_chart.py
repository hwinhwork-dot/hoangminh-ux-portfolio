"""Tool: build_chart — structured rows to studio markup. Pure, no I/O, no model.

The markup contract is not arbitrary: `index.html` already styles `.ai-table` and
`.ai-bars`, and the bar fill is animated by a `data-v` attribute the page reads after
insertion. Emitting anything else produces a chart that renders as unstyled text, which
is why `tests/test_tools/test_build_chart.py` asserts on the exact attributes.
"""

from __future__ import annotations

from html import escape


def _cell(value: str) -> str:
    """Escape everything, then allow back exactly one tag: <b>.

    The previous version escaped a cell only when it contained no `<b>`, which meant the
    author had to know which branch their string would take before deciding whether to
    pre-escape it. They could not, and the result reached production: "&lt;1s latency"
    was escaped a second time and a recruiter saw the literal text `&lt;1s`, while
    "R&amp;D" in a bold cell rendered correctly — the same data, two behaviours.

    Escaping unconditionally and restoring `<b>` afterwards removes the choice. Row data
    is now plain text with `<b>` where bold is wanted; `<` and `&` are just characters.
    """
    escaped = escape(value, quote=False)
    return escaped.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")


def build_bars(rows: list[tuple[str, int]], caption: str = "") -> str:
    if not rows:
        return ""
    bars = "".join(
        '<div class="ai-bar">'
        f'<span class="bl">{escape(str(label), quote=False)}</span>'
        f'<span class="track"><i data-v="{max(0, min(100, int(value)))}"></i></span>'
        f'<span class="bv">{max(0, min(100, int(value)))}</span>'
        "</div>"
        for label, value in rows
    )
    tail = f'<span class="cap">{escape(caption, quote=False)}</span>' if caption else ""
    return f'<div class="ai-bars">{bars}</div>{tail}'


def build_table(head: list[str], rows: list[list[str]], caption: str = "") -> str:
    if not head or not rows:
        return ""
    header = "".join(f"<th>{escape(str(h), quote=False)}</th>" for h in head)
    body = "".join(
        "<tr>" + "".join(f"<td>{_cell(str(c))}</td>" for c in row) + "</tr>" for row in rows
    )
    tail = f'<span class="cap">{escape(caption, quote=False)}</span>' if caption else ""
    return f'<table class="ai-table"><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>{tail}'
