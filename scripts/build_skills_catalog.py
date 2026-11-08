import os
import re

search_paths = [
    r"C:\Users\Santhosh\.gemini\config\skills",
    r"C:\Users\Santhosh\.gemini\antigravity\builtin\skills"
]

skills = []
for p in search_paths:
    if not os.path.exists(p):
        continue
    for name in sorted(os.listdir(p)):
        spath = os.path.join(p, name, "SKILL.md")
        if os.path.isfile(spath):
            desc = ""
            try:
                with open(spath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(2048)
                    m = re.search(r"description:\s*(?:\"([^\"]+)\"|'([^']+)'|([^\r\n]+))", content)
                    if m:
                        desc = (m.group(1) or m.group(2) or m.group(3) or "").strip()
            except Exception as e:
                desc = str(e)
            skills.append((name, spath, desc))

out = []
out.append("# SKILLS & MCP DIRECTORY — AETHER UPSCALE")
out.append("")
out.append("> Generated: 2026-11-07. Master reference of all installed skills and connected MCP servers.")
out.append("")
out.append("## 1. Connected MCP Servers")
out.append("")
out.append("### `context7`")
out.append("- **Source:** `~/.gemini/config/mcp_config.json` (`@upstash/context7-mcp`)")
out.append("- **Function:** Live up-to-date documentation and API references for popular libraries.")
out.append("- **WHEN TO USE:** Writing code against FastAPI, Vite, Tailwind v4, Spandrel, PyTorch, Pillow.")
out.append("- **WHEN NOT TO USE:** Hardware decisions, license verification, generic Python/logic.")
out.append("")
out.append("### `Roblox_Studio`")
out.append("- **Source:** `~/.gemini/config/mcp_config.json`")
out.append("- **Function:** Roblox Studio integration.")
out.append("- **WHEN TO USE:** Never in AETHER UPSCALE (Roblox only).")
out.append("- **WHEN NOT TO USE:** Always in this project.")
out.append("")
out.append("## 2. Core Project Workflow Skills")
out.append("")

core_skills = {
    "planning-with-files": (
        "Persistent markdown file planning (task_plan.md, progress.md, findings.md).",
        "Multi-step tasks (>5 tool calls), milestone planning, tracking task progress.",
        "Small 1-step edits or trivial queries."
    ),
    "systematic-debugging": (
        "Root-cause analysis and evidence-first debugging.",
        "Any bug, error, CUDA crash, tile-seam defect, or unexpected output.",
        "Before an error actually occurs; do not speculate blindly."
    ),
    "verification-before-completion": (
        "Evidence before assertions; run tests before claiming done.",
        "Before claiming any phase, fix, or milestone complete.",
        "Midway during active coding before testable artifacts exist."
    ),
    "test-driven-development": (
        "Write unit tests first, verify failure, then implement.",
        "Pure logic modules: tile engine coordinate math, router rules, metadata serialization.",
        "Exploratory environment checks or fast prototyping."
    ),
    "writing-plans": (
        "Structure multi-file implementation plans with review checkpoints.",
        "Before beginning major architectural changes or new subsystem implementations.",
        "Single-file fixes or routine updates."
    ),
    "graphify": (
        "Codebase knowledge graph generation and navigation.",
        "Phase 2 onwards: finding symbols, dependencies, and impact analysis across `ai_engine/`, `backend/`, `frontend/src/`, `scripts/`, `tests/`.",
        "Phase 0-1 (PRD rule), docs, weights, storage, or tools."
    ),
    "caveman": (
        "Ultra-compressed communication mode.",
        "All general responses (per user rule: always use caveman unless asked to explain).",
        "When user explicitly requests full explanation or elaboration."
    )
}

for name, (summary, when_use, when_not) in core_skills.items():
    match = [s for s in skills if s[0] == name]
    spath = match[0][1] if match else "source: unknown"
    out.append(f"### `{name}`")
    out.append(f"- **Source:** `{spath}`")
    out.append(f"- **Function:** {summary}")
    out.append(f"- **WHEN TO USE:** {when_use}")
    out.append(f"- **WHEN NOT TO USE:** {when_not}")
    out.append("")

out.append("## 3. General & Auxiliary Installed Skills")
out.append("")

for name, spath, desc in skills:
    if name in core_skills:
        continue
    clean_desc = desc if desc else "General utility skill."
    # Determine project relevance
    if name in ["ui-styling", "ui-ux-pro-max"]:
        w_use = "When building or styling the React frontend in Phase 2-3."
        w_not = "Backend, AI engine, or data pipeline tasks."
    elif name in ["research-antigravity", "research"]:
        w_use = "Researching external model architectures or unknown paper details."
        w_not = "Known tasks covered by PRD."
    elif name in ["brainstorming", "subagent-driven-development"]:
        w_use = "Only when user explicitly requests it (conserves quota per AGENTS.md)."
        w_not = "Default autonomous execution."
    elif name in ["code-review-skill", "receiving-code-review", "requesting-code-review"]:
        w_use = "End of major phases for code sanity checks."
        w_not = "Every minor step."
    else:
        w_use = "Only when specifically relevant to specialized sub-tasks."
        w_not = "General AETHER upscale core development unless specifically needed."

    out.append(f"### `{name}`")
    out.append(f"- **Source:** `{spath}`")
    out.append(f"- **Function:** {clean_desc}")
    out.append(f"- **WHEN TO USE:** {w_use}")
    out.append(f"- **WHEN NOT TO USE:** {w_not}")
    out.append("")

out.append("## 4. Skills Not Found On Disk")
out.append("")
out.append("- `model-license-check`: Not installed on disk (source: unknown). Handled manually via PRD Section 5.7 & `docs/MODEL_LICENSES.md`.")
out.append("- `model-smoke-test`: Not installed on disk (source: unknown). Handled via `scripts/test_upscale.py` and adapter tests.")
out.append("- `phase-handoff`: Not installed on disk (source: unknown). Handled via Phase Acceptance Reports and `docs/IMPLEMENTATION_STATUS.md`.")
out.append("")

with open("SKILLS.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"SKILLS.md generated successfully with {len(skills)} skills.")

