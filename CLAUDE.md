# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI_Novel is a local, human-AI collaborative novel writing system. The author owns top-level creative control (outline, chapter summaries), and AI generates compliant prose based on established settings. Target: 1.2 million words (~600 chapters).

## Behavioral Guidelines

These guidelines reduce common LLM coding mistakes. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- No new dependencies beyond those listed in the design doc.
- Functions ≤ 50 lines. Split if exceeded.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. External State Over Context Memory

**Don't rely on conversation history alone. Write it down.**

Project state must not depend solely on dialogue context. Track in documented files:

- **Current task** — what's actively being worked on
- **Completed modules** — what's been done and committed
- **Pending design decisions** — choices deferred or unresolved
- **Known issues** — bugs, limitations, accepted tech debt
- **Acceptance criteria** — verification checklist for milestones

Refer to `docs/progress.md` for the canonical project state. Update it when:
- A task starts or completes
- A design decision is made or changed
- A new issue is discovered
- Milestone acceptance criteria are met

This ensures interrupt-resilient workflows and is essential for long-lived, multi-phase projects.

### 5. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

### 6. Design Principles

- **Template-engine separation.** Prompt templates (.md) are decoupled from the generation engine. Template changes don't require code changes.
- **Task-level model routing.** Each task type (chapter_writing, outline_design, etc.) independently configures provider/model/params.
- **API key storage:** Frontend config (SQLite) > .env fallback. Simple obfuscation (base64 + local salt) in DB, NOT plaintext.

### 7. Version Management

- Project version is stored in `data/config.json` under the `version` key.
- **When making any functional change** (new feature, bug fix, refactor), bump the version:
  - Patch (`0.1.X`): bug fixes, minor tweaks, UI polish
  - Minor (`0.X.0`): new features, new tasks completed
  - Major (`X.0.0`): phase completion, major milestones
- After bumping version in `config.json`, also update `docs/progress.md` to reflect what changed.

### 8. Git Workflow

- Initialize git at project root before any coding begins.
- Commit after every completed task (each `P{phase}-T{task}` in `docs/task_moc.md`).
- Commit messages must reference the task ID and describe *why* the change was made, not just *what* changed.
- Good: `P1-T3: Add chapter CRUD endpoints with repository pattern`
- Bad: `update chapters`
- Keep `.env`, `*.db`, `logs/`, `node_modules/`, `__pycache__/` out of git (track via `.gitignore`).

## Tech Stack

- **Frontend:** Vite 5 + Vue 3.4+, Vue Router 4, Pinia 2, Naive UI 2, Vue Flow 1 (canvas), Tiptap 2 (rich text), axios
- **Backend:** Python 3.11+, FastAPI 0.110+, SQLAlchemy 2.x, SQLite, loguru, httpx, Pydantic v2
- **Data:** SQLite (structured), JSON files (world settings, maps, config), Markdown (prompt templates)

## Project Structure

```
AI_Novel/
├── backend/
│   ├── main.py                       # FastAPI entry, router registration
│   ├── config.py                     # Config (.env + config.json)
│   ├── database.py                   # SQLAlchemy engine + Session
│   ├── logger.py                     # loguru config (daily rotation, 30-day retention)
│   ├── init_db.py                    # DB initialization script
│   ├── routers/                      # REST endpoints (one per module)
│   │   ├── chapters.py              # Chapter & volume CRUD + version/revert/reorder
│   │   ├── generate.py              # Single & batch generation (SSE)
│   │   ├── characters.py            # Character & relation CRUD
│   │   ├── worldview.py             # World settings + map
│   │   ├── model_routes.py          # Model routing config
│   │   ├── templates.py             # Prompt template CRUD (disk files)
│   │   ├── events.py                # Timeline events
│   │   └── system.py                # Settings, stats, export, logs
│   ├── services/
│   │   ├── generator.py             # Generation engine core
│   │   ├── prompt_builder.py        # Prompt assembly (template + variables)
│   │   ├── model_router.py          # LLM route selection + API calls
│   │   └── log_streamer.py          # Log SSE push
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── chapter.py              # Volume, Chapter, ChapterVersion
│   │   ├── character.py            # Character, CharacterRelation
│   │   ├── item.py                 # Item, ItemOwnershipHistory
│   │   ├── event.py                # WorldEvent, EventParticipant
│   │   ├── model_route.py          # ModelRoute
│   │   └── story_line.py           # StoryLine, ChapterStoryLine, ChapterCharacter
│   ├── repositories/                # Data access layer (Repository pattern)
│   │   ├── chapter_repo.py
│   │   ├── character_repo.py
│   │   └── event_repo.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── stores/                  # Pinia stores
│   │   │   ├── chapters.js
│   │   │   ├── characters.js
│   │   │   ├── worldview.js
│   │   │   └── settings.js
│   │   ├── api/                     # Axios + SSE API wrappers
│   │   │   ├── chapters.js
│   │   │   ├── characters.js
│   │   │   ├── generate.js
│   │   │   ├── worldview.js
│   │   │   └── settings.js
│   │   ├── views/                   # Page components
│   │   │   ├── Dashboard.vue
│   │   │   ├── OutlineView.vue
│   │   │   ├── ChapterEditor.vue
│   │   │   ├── WorldviewEditor.vue
│   │   │   ├── MapEditor.vue
│   │   │   ├── CharacterList.vue
│   │   │   ├── CharacterDetail.vue
│   │   │   ├── CharacterGraph.vue
│   │   │   ├── ItemManager.vue
│   │   │   ├── Timeline.vue
│   │   │   ├── TemplateLibrary.vue
│   │   │   ├── ModelRouteSettings.vue
│   │   │   ├── SystemSettings.vue
│   │   │   └── LogViewer.vue
│   │   └── components/
│   │       ├── layout/              # SideNav.vue, TopBar.vue
│   │       ├── chapter/            # ChapterList.vue, VersionHistory.vue
│   │       └── common/             # StreamOutput.vue, LogTag.vue
│   ├── vite.config.js
│   └── package.json
├── data/
│   ├── config.json                  # Module switches + system config
│   ├── worldview.json               # World settings (free-form JSON)
│   ├── map.json                     # Map nodes/edges (Vue Flow format)
│   ├── writing_style.json           # Global writing style
│   └── templates/                   # Prompt templates (.md with YAML frontmatter)
├── logs/                            # Auto-generated log files
├── novel.db                         # SQLite database
├── .env                             # API keys (not committed)
└── .env.example
```

## Core Architecture

### Layered Backend Pattern
- **routers/**: Handle HTTP, validate params, call services — NO SQL directly
- **services/**: Business logic, orchestrate across models
- **repositories/**: All database operations, one file per domain entity
- **models/**: SQLAlchemy ORM definitions only

### Module Toggle System
Each module has an `enabled` flag in `data/config.json`. Backend dynamically registers routes at startup based on config; frontend shows/hides nav items based on module list from API.

## API Conventions

- Base URL: `/api/v1`
- Request/Response: `application/json`
- SSE streaming: `text/event-stream`
- Error format: `{"code": "ERROR_CODE", "message": "...", "detail": {}}`
- All database operations go through Repository pattern

## Development Phases

The project follows incremental phases documented in `docs/task_moc.md`. Tasks are tracked by ID (`P{phase}-T{task}`, e.g. `P1-T3`):

1. **Phase 1 — MVP Core Flow:** Outline → generate → save loop, API key config, single chapter SSE generation
2. **Phase 2 — World Building:** World settings editor, character CRUD + relation graph, template library UI, chapter-character associations
3. **Phase 3 — Advanced Features:** Map canvas, timeline/events, batch generation queue, log viewer, version history with rollback
4. **Phase 4 — Polish:** Dashboard stats, storylines, item ownership tracking, export (TXT/MD/EPUB)

## Common Commands

```bash
# Backend
uvicorn backend.main:app --reload    # Start dev server (http://localhost:8000)
python init_db.py                    # Create/initialize SQLite tables

# Frontend
npm run dev                          # Vite dev server (http://localhost:5173)
npm run build                        # Production build
```

## Modular Configuration

`data/config.json` controls which modules are active:

```json
{
  "modules": {
    "world_builder": true,
    "character_manager": true,
    "timeline_manager": true,
    "prompt_library": true,
    "model_router": true,
    "log_viewer": true
  }
}
```
