# Agent Instructions

Read SKILLS.md at the start of every session and follow it.

## Skills policy
- **planning-with-files**: Use for any task needing more than ~5 tool calls or when the session is long. It is the ONLY progress tracker; do not also maintain separate status files beyond `docs/IMPLEMENTATION_STATUS.md` pointing to it.
- **superpowers**: Use ONLY `systematic-debugging` (any error or unexpected behavior; find root cause before changing code) and `verification-before-completion` (before claiming any phase or fix is done). Do not run `brainstorming` or `subagent-driven-development` unless asked (conserves quota).
- **graphify**: Do not use during Phase 0-1. From Phase 2 onwards, use only on `ai_engine/`, `backend/`, and `frontend/src/`. Query the graph before grepping for "where is X / what depends on X". No `--watch`.
- **Context7 MCP**: Use when writing code against FastAPI, Vite, Tailwind v4, Spandrel, PyTorch, or Pillow. Not for licensing or hardware decisions.
- **Single workflow**: Never use more than one workflow system at a time. If skills conflict with `AGENTS.md` or `PRD.md`, stop and report. Skills never replace real verification runs.
- **Safety**: Never let a skill download models or run destructive commands without explicit confirmation.

