"""Chart markup must match the CSS that already exists in index.html."""

from agent.orchestrator.nodes.viz_kai import PROJECTS, SKILLS, TIMELINE
from agent.tools.build_chart import build_bars, build_table


def test_bars_emit_data_v_for_the_fill_transition():
    html = build_bars([("User research", 92)])
    assert 'data-v="92"' in html and 'class="ai-bars"' in html and 'class="track"' in html


def test_bar_values_are_clamped_not_trusted():
    assert 'data-v="100"' in build_bars([("x", 400)])
    assert 'data-v="0"' in build_bars([("x", -5)])


def test_table_emits_the_classes_the_page_styles():
    html = build_table(["Project", "Role"], [["<b>EchoMind</b>", "PO"]])
    assert 'class="ai-table"' in html and "<thead>" in html and "<th>Project</th>" in html


def test_bold_in_authored_rows_survives_but_stray_markup_does_not():
    html = build_table(["A"], [["<b>keep</b>"], ["<script>no</script>"]])
    assert "<b>keep</b>" in html and "<script>" not in html


def test_empty_input_produces_nothing_rather_than_an_empty_shell():
    assert build_bars([]) == "" and build_table([], []) == ""


def test_skill_values_match_the_knowledge_base():
    from agent.config import KNOWLEDGE_RAW

    profile = (KNOWLEDGE_RAW / "01-profile.md").read_text(encoding="utf-8")
    for label, value in SKILLS:
        assert f"| {value} |" in profile, f"{label} = {value} is not in 01-profile.md"


def test_project_and_timeline_rows_are_rectangular():
    assert all(len(row) == 4 for row in PROJECTS)
    assert all(len(row) == 3 for row in TIMELINE)


def test_captions_are_escaped():
    assert "<b>" not in build_bars([("x", 1)], caption="<b>evil</b>")
