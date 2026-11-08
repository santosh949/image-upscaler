# SKILLS & MCP DIRECTORY — AETHER UPSCALE

> Generated: 2026-11-07. Master reference of all installed skills and connected MCP servers.

## 1. Connected MCP Servers

### `context7`
- **Source:** `~/.gemini/config/mcp_config.json` (`@upstash/context7-mcp`)
- **Function:** Live up-to-date documentation and API references for popular libraries.
- **WHEN TO USE:** Writing code against FastAPI, Vite, Tailwind v4, Spandrel, PyTorch, Pillow.
- **WHEN NOT TO USE:** Hardware decisions, license verification, generic Python/logic.

### `Roblox_Studio`
- **Source:** `~/.gemini/config/mcp_config.json`
- **Function:** Roblox Studio integration.
- **WHEN TO USE:** Never in AETHER UPSCALE (Roblox only).
- **WHEN NOT TO USE:** Always in this project.

## 2. Core Project Workflow Skills

### `planning-with-files`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\planning-with-files\SKILL.md`
- **Function:** Persistent markdown file planning (task_plan.md, progress.md, findings.md).
- **WHEN TO USE:** Multi-step tasks (>5 tool calls), milestone planning, tracking task progress.
- **WHEN NOT TO USE:** Small 1-step edits or trivial queries.

### `systematic-debugging`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\systematic-debugging\SKILL.md`
- **Function:** Root-cause analysis and evidence-first debugging.
- **WHEN TO USE:** Any bug, error, CUDA crash, tile-seam defect, or unexpected output.
- **WHEN NOT TO USE:** Before an error actually occurs; do not speculate blindly.

### `verification-before-completion`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\verification-before-completion\SKILL.md`
- **Function:** Evidence before assertions; run tests before claiming done.
- **WHEN TO USE:** Before claiming any phase, fix, or milestone complete.
- **WHEN NOT TO USE:** Midway during active coding before testable artifacts exist.

### `test-driven-development`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\test-driven-development\SKILL.md`
- **Function:** Write unit tests first, verify failure, then implement.
- **WHEN TO USE:** Pure logic modules: tile engine coordinate math, router rules, metadata serialization.
- **WHEN NOT TO USE:** Exploratory environment checks or fast prototyping.

### `writing-plans`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\writing-plans\SKILL.md`
- **Function:** Structure multi-file implementation plans with review checkpoints.
- **WHEN TO USE:** Before beginning major architectural changes or new subsystem implementations.
- **WHEN NOT TO USE:** Single-file fixes or routine updates.

### `graphify`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\graphify\SKILL.md`
- **Function:** Codebase knowledge graph generation and navigation.
- **WHEN TO USE:** Phase 2 onwards: finding symbols, dependencies, and impact analysis across `ai_engine/`, `backend/`, `frontend/src/`, `scripts/`, `tests/`.
- **WHEN NOT TO USE:** Phase 0-1 (PRD rule), docs, weights, storage, or tools.

### `caveman`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\caveman\SKILL.md`
- **Function:** Ultra-compressed communication mode.
- **WHEN TO USE:** All general responses (per user rule: always use caveman unless asked to explain).
- **WHEN NOT TO USE:** When user explicitly requests full explanation or elaboration.

## 3. General & Auxiliary Installed Skills

### `agentmail-sending`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\agentmail-sending\SKILL.md`
- **Function:** Canonical AgentMail send-message API reference for swarm agents. Pins the base URL, required field names, text-only rendering workaround, BCC policy, and ready-to-copy curl / swarm-script examples so agents do not rediscover the API surface at runtime.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `artifacts`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\artifacts\SKILL.md`
- **Function:** Serve interactive web content (HTML pages, dashboards, approval flows, static reports, custom Hono apps) to a public URL via localtunnel. Use when the user asks to "create an artifact for X", "host this for me", "make me a tunneled URL", "spin up a web server for X", "publish this report so I can see it", "share this file/page publicly", "expose this dashboard", "give me a live link", or anything that needs a browser-reachable URL pointing at agent-generated content. Wraps the `agent-swarm artifact` CLI plus the `createArtifactServer` SDK; covers static directories, custom Hono apps, daemonization (nohup / PM2), HTTP Basic auth, and the in-page swarm Browser SDK.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `attio-interaction`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\attio-interaction\SKILL.md`
- **Function:** How to read and write your Attio CRM via the REST API v2: query/filter records, upsert companies/people/deals with matching_attribute, write notes and tasks, manage list entries, and handle webhooks. Auth via ATTIO_API_KEY (Bearer token). Use this skill whenever you need to interact with Attio CRM data from the swarm.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `banner-design`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\banner-design\SKILL.md`
- **Function:** Design banners for social media, ads, website heroes, creative assets, and print. Multiple art direction options with AI-generated visuals. Actions: design, create, generate banner. Platforms: Facebook, Twitter/X, LinkedIn, YouTube, Instagram, Google Display, website hero, print. Styles: minimalist, gradient, bold typography, photo-based, illustrated, geometric, retro, glassmorphism, 3D, neon, duotone, editorial, collage. Uses ui-ux-pro-max, frontend-design, ai-artist, ai-multimodal skills.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `brag`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\brag\SKILL.md`
- **Function:** Turn the current project website into a short, polished, shareable launch video using Hyperframes. Use when someone says "/brag", "let's brag about this", "make a launch video", "turn this into a video", or wants to share what they built. Reads the project code directly — no live URL or screenshots needed.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `brainstorming`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\brainstorming\SKILL.md`
- **Function:** You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation.
- **WHEN TO USE:** Only when user explicitly requests it (conserves quota per AGENTS.md).
- **WHEN NOT TO USE:** Default autonomous execution.

### `brand`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\brand\SKILL.md`
- **Function:** Brand voice, visual identity, messaging frameworks, asset management, brand consistency. Activate for branded content, tone of voice, marketing assets, brand compliance, style guides.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `cavecrew`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\cavecrew\SKILL.md`
- **Function:** >
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `caveman-commit`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\caveman-commit\SKILL.md`
- **Function:** >
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `caveman-compress`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\caveman-compress\SKILL.md`
- **Function:** >
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `caveman-help`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\caveman-help\SKILL.md`
- **Function:** >
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `caveman-review`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\caveman-review\SKILL.md`
- **Function:** >
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `caveman-stats`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\caveman-stats\SKILL.md`
- **Function:** >
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `close-issue`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\close-issue\SKILL.md`
- **Function:** Close a GitHub or GitLab issue with a summary comment
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `code-review-skill`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\code-review-skill\SKILL.md`
- **Function:** |
- **WHEN TO USE:** End of major phases for code sanity checks.
- **WHEN NOT TO USE:** Every minor step.

### `composio`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\composio\SKILL.md`
- **Function:** Use Composio from Agent Swarm via the `agent-swarm x composio` CLI route or the `swarm_x` MCP tool. Trigger when a task needs connected third-party app tools such as Gmail, GitHub, Slack, Notion, or HubSpot through Composio Tool Router sessions, Connect Links, or connected accounts. This is the HUB skill — for Google apps see the sibling skills `composio-gmail`, `composio-google-calendar`, `composio-google-docs`.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `composio-gmail`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\composio-gmail\SKILL.md`
- **Function:** Per-app playbook for driving Gmail through Composio (toolkit slug `gmail`). Verified GMAIL_* tool slugs and argument shapes for reading, searching, sending, drafts, labels, and threads. Use alongside the `composio` hub skill whenever a task reads or sends Gmail for a connected user. Covers the metadata-first reads, the GMAIL_SEND_EMAIL HTML flag, and reply-to-thread.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `composio-google-calendar`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\composio-google-calendar\SKILL.md`
- **Function:** Per-app playbook for driving Google Calendar through Composio (toolkit slug `googlecalendar`). Verified GOOGLECALENDAR_* tool slugs and argument shapes for listing, finding, creating, and updating events plus free/busy. Use alongside the `composio` hub skill. CRITICAL — covers the "events from a year ago" trap: GOOGLECALENDAR_EVENTS_LIST has no default timeMin, so you MUST pass timeMin/orderBy/singleEvents to get upcoming events.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `composio-google-docs`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\composio-google-docs\SKILL.md`
- **Function:** Per-app playbook for driving Google Docs through Composio (toolkit slug `googledocs`). Verified GOOGLEDOCS_* tool slugs and argument shapes for searching, reading plaintext, creating (incl. from markdown), and editing documents. Use alongside the `composio` hub skill whenever a task reads or writes Google Docs for a connected user.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `create-pr`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\create-pr\SKILL.md`
- **Function:** Create a pull request (GitHub) or merge request (GitLab) from the current branch
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `creative-thinking`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\creative-thinking\SKILL.md`
- **Function:** Combined creative and critical thinking skills.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `creator-critic`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\creator-critic\SKILL.md`
- **Function:** Run a two-voice idea loop where one side generates options and the other side pressure-tests them. Use for concepts, positioning, campaigns, product ideas, and strategic directions.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `design`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\design\SKILL.md`
- **Function:** Comprehensive design skill: brand identity, design tokens, UI styling, logo generation (55 styles, Gemini AI), corporate identity program (50 deliverables, CIP mockups), HTML presentations (Chart.js), banner design (22 styles, social/ads/web/print), icon design (15 styles, SVG, Gemini 3.1 Pro), social photos (HTML→screenshot, multi-platform). Actions: design logo, create CIP, generate mockups, build slides, design banner, generate icon, create social photos, social media images, brand identity, design system. Platforms: Facebook, Twitter, LinkedIn, YouTube, Instagram, Pinterest, TikTok, Threads, Google Ads.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `design-system`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\design-system\SKILL.md`
- **Function:** Token architecture, component specifications, and slide generation. Three-layer tokens (primitive→semantic→component), CSS variables, spacing/typography scales, component specs, strategic slide creation. Use for design tokens, systematic design, brand-compliant presentations.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `dispatching-parallel-agents`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\dispatching-parallel-agents\SKILL.md`
- **Function:** Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `executing-plans`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\executing-plans\SKILL.md`
- **Function:** Use when you have a written implementation plan to execute in a separate session with review checkpoints
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `finishing-a-development-branch`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\finishing-a-development-branch\SKILL.md`
- **Function:** Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `frontend-slides`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\frontend-slides\SKILL.md`
- **Function:** Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to web, or create slides for a talk/pitch. Helps non-designers discover their aesthetic through visual exploration rather than abstract choices.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `impeccable`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\impeccable\SKILL.md`
- **Function:** Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, optimize, adapt, animate, colorize, extract, or otherwise improve a frontend interface. Covers websites, landing pages, dashboards, product UI, app shells, components, forms, settings, onboarding, and empty states. Handles UX review, visual hierarchy, information architecture, cognitive load, accessibility, performance, responsive behavior, theming, anti-patterns, typography, fonts, spacing, layout, alignment, color, motion, micro-interactions, UX copy, error states, edge cases, i18n, and reusable design systems or tokens. Also use for bland designs that need to become bolder or more delightful, loud designs that should become quieter, live browser iteration on UI elements, or ambitious visual effects that should feel technically extraordinary. Not for backend-only or non-UI tasks.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `implement-issue`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\implement-issue\SKILL.md`
- **Function:** Implement a GitHub issue or GitLab issue and create a PR/MR
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `investigate-sentry-issue`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\investigate-sentry-issue\SKILL.md`
- **Function:** Investigate and triage a Sentry error issue
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `kapso-whatsapp`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\kapso-whatsapp\SKILL.md`
- **Function:** How to interact with Kapso WhatsApp from the swarm — read inbound webhook payloads (text AND media), fetch message history, send free-form messages within the 24h session window (and template messages outside it), mark-as-read, show the typing indicator, send reactions, download media, verify webhook signatures, and resolve contacts to swarm users. Canonical reference for ANY Kapso interaction beyond the thin `send-whatsapp-message` / `reply-whatsapp-message` MCP tools — for templates, media, reactions, typing, mark-as-read, signature verify, contact resolution, conversation history, drop to the REST recipes here. Use whenever a task references a WhatsApp message routed through Kapso, or when a workflow needs to reply on WhatsApp.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `kv-storage`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\kv-storage\SKILL.md`
- **Function:** Use the swarm KV store (Redis-like, namespaced) for cross-task / cross-session / per-page state. Auto-scoped to your context (Slack thread / PR / Linear issue / agent / page). Use for counters, cursors, page state. Do NOT use for secrets (`swarm_config`), embedded knowledge (`memory`), or files (`agent-fs`).
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `m-skill`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\m-skill\SKILL.md`
- **Function:** Core operational directives, Pterodactyl constraints, and evidence-based debugging. This skill encapsulates absolute ground-truth principles and must be adhered to.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `options-challenge`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\options-challenge\SKILL.md`
- **Function:** Compare several strategic options, force explicit trade-offs, and rank the strongest path. Use when the user has multiple plausible directions and wants a sharper decision memo.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `pages`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\pages\SKILL.md`
- **Function:** General utility skill.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `playwright-skill`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\playwright-skill\SKILL.md`
- **Function:** Complete browser automation with Playwright. Auto-detects dev servers, writes clean test scripts to /tmp. Test pages, fill forms, take screenshots, check responsive design, validate UX, test login flows, check links, automate any browser task. Use when user wants to test websites, automate browser interactions, validate web functionality, or perform any browser-based testing.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `receiving-code-review`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\receiving-code-review\SKILL.md`
- **Function:** Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation
- **WHEN TO USE:** End of major phases for code sanity checks.
- **WHEN NOT TO USE:** Every minor step.

### `remotion`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\remotion\SKILL.md`
- **Function:** Best practices for Remotion - Video creation in React
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `requesting-code-review`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\requesting-code-review\SKILL.md`
- **Function:** Use when completing tasks, implementing major features, or before merging to verify work meets requirements
- **WHEN TO USE:** End of major phases for code sanity checks.
- **WHEN NOT TO USE:** Every minor step.

### `research-antigravity`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\research-antigravity\SKILL.md`
- **Function:** Use for any task that requires finding, verifying, and synthesizing real-world information rather than generating it from memory — market research, technical due diligence, competitive/vendor comparisons, literature review, fact-checking, "what's the best X", "investigate Y", pre-build discovery, or any open-ended "find out about..." question. Triggers on "research", "find out", "investigate", "look into", "compare options", "due diligence", "what's the current state of", "fact-check", "is it true that". Not for questions the agent can already answer confidently from stable general knowledge (math, syntax, well-established history) — only invoke when the answer depends on current, external, or verifiable information.
- **WHEN TO USE:** Researching external model architectures or unknown paper details.
- **WHEN NOT TO USE:** Known tasks covered by PRD.

### `respond-github`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\respond-github\SKILL.md`
- **Function:** Respond to a GitHub issue/PR or GitLab issue/MR
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `review-offered-task`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\review-offered-task\SKILL.md`
- **Function:** Review a task that has been offered to you and decide whether to accept or reject it
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `review-pr`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\review-pr\SKILL.md`
- **Function:** Review a pull request (GitHub) or merge request (GitLab) and provide detailed feedback
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `roblox-dev-mentor`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\roblox-dev-mentor\SKILL.md`
- **Function:** A senior full-stack Roblox game developer guiding architecture, scripting, UI/UX, performance, and best practices.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `roblox-production`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\roblox-production\SKILL.md`
- **Function:** Production-grade all-in-one Roblox Studio development skill for Antigravity. Covers modular service architecture, Humanoid+custom rig animations, networking optimization, combat systems, responsive GUI, performance profiling, and monetization patterns. Research-backed by top games (Blox Fruits, Doors, Arsenal, Adopt Me). Questions inefficient approaches, provides trade-off analysis, scales from 10 to 1000 players. Use for any Roblox game production task—architecture, animation sync, combat loops, network optimization, GUI responsiveness, scaling, or debugging.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `roblox-universal-gui`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\roblox-universal-gui\SKILL.md`
- **Function:** Universal UI layout masterclass for Roblox. Enforces mathematically flawless, un-stretchable constraint structures (learned from advanced analysis of StickShopRework and DailyRewardGUI). Can adapt to any visual theme specified by the user.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `skill-installer`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\skill-installer\SKILL.md`
- **Function:** Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos).
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `slides`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\slides\SKILL.md`
- **Function:** Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, copywriting formulas, and contextual slide strategies.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `smolagents-video-script-generator`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\smolagents-video-script-generator\SKILL.md`
- **Function:** A multi-agent AI system for planning, researching, and writing highly engaging video scripts for TikTok, YouTube Shorts, and Instagram Reels using DeepSeek and SerpAPI. Use when the user wants to generate a high-quality video script, research a topic for social media, or create structured video content with AI agents.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `start-leader`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\start-leader\SKILL.md`
- **Function:** Start the Agent Swarm Leader
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `start-worker`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\start-worker\SKILL.md`
- **Function:** Start an Agent Swarm Worker
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `strategy-debate`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\strategy-debate\SKILL.md`
- **Function:** Run a structured Claude + Codex strategy debate for ideas, trade-offs, positioning, or decisions. Use when the user wants both voices, cross-critique, revised positions, a chosen finalizer, and a saved transcript.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `sub-agents`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\sub-agents\SKILL.md`
- **Function:** Run agent definitions as sub-agents. Use when the user names an agent or sub-agent to run, references an agent definition, or delegates a task to an agent.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `subagent-driven-development`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\subagent-driven-development\SKILL.md`
- **Function:** Use when executing implementation plans with independent tasks in the current session
- **WHEN TO USE:** Only when user explicitly requests it (conserves quota per AGENTS.md).
- **WHEN NOT TO USE:** Default autonomous execution.

### `swarm-chat`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\swarm-chat\SKILL.md`
- **Function:** Effective communication within the agent swarm using internal Slack
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `swarm-local-e2e`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\swarm-local-e2e\SKILL.md`
- **Function:** Guide for running local E2E tests with API server, Docker lead/worker containers, task creation, log verification, UI dashboard, and cleanup
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `swarm-scripts`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\swarm-scripts\SKILL.md`
- **Function:** Use swarm scripts for bulk SDK calls, repetitive fan-out, and context-efficient data processing.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `todos`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\todos\SKILL.md`
- **Function:** Handle the agent personal todos.md file
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `ui-styling`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\ui-styling\SKILL.md`
- **Function:** Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first styling, and canvas-based visual designs. Use when building user interfaces, implementing design systems, creating responsive layouts, adding accessible components (dialogs, dropdowns, forms, tables), customizing themes and colors, implementing dark mode, generating visual designs and posters, or establishing consistent styling patterns across applications.
- **WHEN TO USE:** When building or styling the React frontend in Phase 2-3.
- **WHEN NOT TO USE:** Backend, AI engine, or data pipeline tasks.

### `ui-ux-pro-max`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\ui-ux-pro-max\SKILL.md`
- **Function:** UI/UX design intelligence for web and mobile. Includes 50+ styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines, and 25 chart types across 10 stacks (React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, and HTML/CSS). Actions: plan, build, create, design, implement, review, fix, improve, optimize, enhance, refactor, and check UI/UX code. Projects: website, landing page, dashboard, admin panel, e-commerce, SaaS, portfolio, blog, and mobile app. Elements: button, modal, navbar, sidebar, card, table, form, and chart. Styles: glassmorphism, claymorphism, minimalism, brutalism, neumorphism, bento grid, dark mode, responsive, skeuomorphism, and flat design. Topics: color systems, accessibility, animation, layout, typography, font pairing, spacing, interaction states, shadow, and gradient. Integrations: shadcn/ui MCP for component search and examples.
- **WHEN TO USE:** When building or styling the React frontend in Phase 2-3.
- **WHEN NOT TO USE:** Backend, AI engine, or data pipeline tasks.

### `user-management`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\user-management\SKILL.md`
- **Function:** How to manage the user registry — creating users for new Slack/GitHub/GitLab/Linear identities, managing aliases, resolving users across platforms. Use when a new human interacts with the swarm or when user identity needs updating.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `using-git-worktrees`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\using-git-worktrees\SKILL.md`
- **Function:** Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `using-superpowers`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\using-superpowers\SKILL.md`
- **Function:** Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `work-on-task`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\work-on-task\SKILL.md`
- **Function:** Work on a specific task assigned to you in the agent swarm
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `writing-skills`
- **Source:** `C:\Users\Santhosh\.gemini\config\skills\writing-skills\SKILL.md`
- **Function:** Use when creating new skills, editing existing skills, or verifying skills work before deployment
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `agy-customizations`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\agy-customizations\SKILL.md`
- **Function:** >-
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `antigravity_guide`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\antigravity_guide\SKILL.md`
- **Function:** Provides a comprehensive guide, quick reference, and sitemap for Google Antigravity (AGY), including the Antigravity CLI (agy), Antigravity 2.0, Antigravity IDE, Python SDK, slash commands, keybindings, and customizations (skills, rules, MCP, sidecars). Activate this skill when the user asks questions about how to use, configure, or customize Antigravity, AGY, the agy CLI, the Antigravity IDE, or Antigravity 2.0.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `automation`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\automation\SKILL.md`
- **Function:** Interactive guide to design and create a scheduled background automation. Use this skill when the user wants to create an automated or recurring scheduled task (e.g. "summarize my emails every morning", "every Monday send me a to-do list"). Also triggered by the /automation slash command.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `generative_ui`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\generative_ui\SKILL.md`
- **Function:** How to render rich interactive HTML widgets inline in the chat or as standalone artifacts. Use this skill when you want to show the user diagrams, data visualizations, interactive controls, educational walkthroughs, or any rich visual content beyond plain text and markdown.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `migrate-agent-settings`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\migrate-agent-settings\SKILL.md`
- **Function:** Migrates the user's MCP servers, skills, slash commands, subagents, and instruction files from other coding agents (Claude Code, Codex, Cursor, Gemini CLI) into one new Antigravity plugin. Use when the user wants to bring over, import, or migrate their setup or config from another agent or tool. Don't use for installing Marketplace plugins or authoring a new plugin from scratch (use the plugin skill).
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `migrate-workflows`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\migrate-workflows\SKILL.md`
- **Function:** Automatically migrate legacy workflows to modern skills across global and workspace configurations. Scans for existing workflows, creates target SKILL.md files, and safely archives old workflow files.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `native_swarm`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\native_swarm\SKILL.md`
- **Function:** >-
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `permissioned-github`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\permissioned-github\SKILL.md`
- **Function:** Guidelines for interacting with GitHub and request permissions from the user when commands fail due to restrictions in the agent environment.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `plugin`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\plugin\SKILL.md`
- **Function:** How to manage and create plugins — namespaced bundles of skills, agents, rules, MCP servers and hooks that install, enable and disable as a single unit. Use this skill when the user wants to enable, disable, install or uninstall a plugin, when they want to create a new plugin, or when a new customization should be packaged into a plugin rather than left loose. Also triggered by the /plugin slash command. Don't use for the underlying customization system itself — discovery roots, loading priority, or authoring a standalone skill, agent, rule, hook or MCP server outside a plugin; see the customizations guide skill for those.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `run-workflow`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\run-workflow\SKILL.md`
- **Function:** >-
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `swarm_monitor`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\swarm_monitor\SKILL.md`
- **Function:** >-
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `swarm_narrator`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\swarm_narrator\SKILL.md`
- **Function:** >-
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

### `ui-plugin-navigation`
- **Source:** `C:\Users\Santhosh\.gemini\antigravity\builtin\skills\ui-plugin-navigation\SKILL.md`
- **Function:** Discover UI plugin panels relevant to the current task and surface a one-click pill in chat to open (toggle) them in the side pane. Use when a running UI plugin's panel would help with what the user is doing, or right after the user enables a new UI plugin pane and a shortcut to open it is handy.
- **WHEN TO USE:** Only when specifically relevant to specialized sub-tasks.
- **WHEN NOT TO USE:** General AETHER upscale core development unless specifically needed.

## 4. Skills Not Found On Disk

- `model-license-check`: Not installed on disk (source: unknown). Handled manually via PRD Section 5.7 & `docs/MODEL_LICENSES.md`.
- `model-smoke-test`: Not installed on disk (source: unknown). Handled via `scripts/test_upscale.py` and adapter tests.
- `phase-handoff`: Not installed on disk (source: unknown). Handled via Phase Acceptance Reports and `docs/IMPLEMENTATION_STATUS.md`.
