"""Kai — analyst. Deterministic templating, no model call.

Values come from the knowledge base by way of the retrieved chunks, never from the model,
so a chart cannot disagree with the prose next to it. The tables below mirror
`01-profile.md` and `02-projects.md`; `tests/test_tools/test_build_chart.py` asserts they
stay in step.
"""

from __future__ import annotations

from agent.orchestrator.state import StudioState
from agent.schemas import Citation, Intent
from agent.tools.build_chart import build_bars, build_table

SKILLS = [
    ("User research", 92), ("Journey mapping", 90), ("AI product framing", 90),
    ("User stories & AC", 88), ("VPC / problem framing", 86), ("Agent & prompt design", 86),
    ("Usability & UAT", 84), ("Guardrails & AI evals", 82), ("RAG & knowledge design", 80),
    ("Figma & prototyping", 78), ("Data & Python", 72),
]

PROJECTS = [
    ["<b>ViVi · VinFast</b>", "Product Owner · UI/UX", "Multi-agent booking assistant",
     "Agent + web UI + admin, guarded"],
    ["<b>EchoMind</b>", "Product Owner", "AI brain-to-text, Agile + RACI",
     "55-65 WPM, &lt;1s latency, 100% milestones"],
    ["<b>E-Reader Ecosystem</b>", "Product Lead", "HCI activation journey",
     "Top 20 finalist (HCMC People's Committee)"],
    ["<b>SIHUB</b>", "PM Executive", "Startup onboarding, insights, NPS",
     "150+ stakeholders, Board reporting"],
]

TIMELINE = [
    ["2022 - 2026", "<b>UEH University</b>", "B. of Technology &amp; Innovation, GPA 3.57"],
    ["Jul - Dec 2024", "<b>SIHUB, R&amp;D Intern</b>", "City-level study, 150+ stakeholders"],
    ["Jan - Oct 2025", "<b>SIHUB, PM Executive</b>", "Startup journeys, A/B tests, Board reports"],
    ["Sep - Dec 2025", "<b>EchoMind, Product Owner</b>", "Brain-to-text, 100% milestones"],
    ["Jul 2026 - now", "<b>VinGroup, AI Talent</b>", "AI products end to end; PO &amp; UI/UX on ViVi"],
]

_TIMELINE_WORDS = ("experience", "timeline", "career", "history", "kinh nghi")


async def visualise(state: StudioState) -> StudioState:
    if not state.needs_chart:
        return state

    message = state.message.lower()
    if state.intent == Intent.METRIC or "skill" in message or "chart" in message:
        chart = build_bars(SKILLS, "Self-assessment, calibrated against real project work.")
        source = "01-profile.md"
        heading = "Self-assessed skill profile"
        lead = "Here is Minh's core skill profile:"
    elif any(word in message for word in _TIMELINE_WORDS):
        chart = build_table(["When", "Where", "What"], TIMELINE)
        source, heading = "02-projects.md", "Timeline"
        lead = "Minh's path so far:"
    else:
        chart = build_table(["Project", "Role", "Focus", "Result"], PROJECTS)
        source, heading = "02-projects.md", "Comparison at a glance"
        lead = "Four projects Minh led, side by side:"

    state.answer_html = f"{lead}{chart}"
    state.citations = [Citation(source=source, heading=heading)]
    state.speaker = "kai"
    state.raw_answer = ""
    state.step(actor="kai", act="chart", label="Charting the numbers...")
    return state
