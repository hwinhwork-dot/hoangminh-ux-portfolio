"""Tool: build_chart — structured rows to studio markup. Pure, no I/O, no model.

The markup contract is not arbitrary: `index.html` already styles `.ai-table` and
`.ai-bars`, and the bar fill is animated by a `data-v` attribute the page reads after
insertion. Emitting anything else produces a chart that renders as unstyled text, which
is why `tests/test_tools/test_build_chart.py` asserts on the exact attributes.
"""

from __future__ import annotations

from html import escape


def _cell(value: str) -> str:
    """Row content is authored in the knowledge base and may carry <b>; nothing else."""
    return value if value.startswith("<b>") or "</b>" in value else escape(value, quote=False)


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
