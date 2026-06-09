# AGENTS.md

## Project Memory

`docs/project-memory/` is the entry point for project context, past decisions, architectural agreements, and accumulated project memory.

Project Memory helps understand the intent, history, and rules of the project, but is not the source of truth for the current implementation.

### Source Priority

When working with the project, use the following order of trust:

1. Current repository code
2. Tests, migrations, schemas, configs, and runtime settings
3. Freshly generated project analysis, e.g. `graphify-out/GRAPH_REPORT.md`
4. Project documentation
5. `docs/project-memory/`
6. Previous discussions and assumptions

If `docs/project-memory/` conflicts with current code, trust the code.

If Graphify conflicts with current code, trust the code.

If documentation conflicts with current code, first verify the actual implementation in the repository.

### How to Use Project Memory

Before any deep work on this repository, first open:

1. `docs/project-memory/INDEX.md`
2. Relevant files from `docs/project-memory/curated/`
3. Relevant files from `docs/project-memory/inventories/`

Use Project Memory for:

- Understanding project goals
- Understanding architectural preferences
- Accounting for past decisions
- Following the agreed working style
- Understanding why certain approaches were chosen or rejected
- Preserving context between sessions

Do NOT use Project Memory as evidence of:

- Exact file locations
- Current model fields
- Current API behavior
- Current function signatures
- Current business logic
- Current inter-module dependencies
- Current database schema
- Current background task flow
- Current frontend component structure

All such details must be verified against the actual repository files.

### Before Making Changes

For small, localized changes:

1. Examine the target file directly.
2. Check the nearest tests or usages.
3. Make the minimal safe change.

For deep, architectural, or cross-module work:

1. Open `docs/project-memory/INDEX.md`.
2. Review relevant files from `docs/project-memory/curated/` and `docs/project-memory/inventories/`.
3. If an up-to-date `graphify-out/GRAPH_REPORT.md` exists, use it to understand structure and relationships.
4. Verify all important assumptions against the current code.
5. Identify affected modules, tests, migrations, configs, and API contracts.
6. Explain the plan first.
7. Then make minimal safe changes.
8. Run or suggest relevant tests.

### Working with Stale Memory

Project Memory may be outdated.

If memory says one thing but the code shows another:

- Trust the current code
- Briefly note the discrepancy
- Do not bend the code to match memory without an explicit request
- After changes, update the relevant files in `docs/project-memory/`

Example:

> Project Memory indicates that report generation lives only in `reports/tasks.py`, but the current code also uses `reports/services/`. I will follow the current code structure and update the memory after the change.

### What Is Worth Storing in Project Memory

Good candidates for `docs/project-memory/`:

- Project purpose
- Architectural principles
- Code style conventions
- Testing requirements
- Security requirements
- Naming rules
- Accepted trade-offs
- Rejected approaches
- Product decisions
- Environment specifics that rarely change

Bad candidates:

- Exact file paths without necessity
- Exact function names
- Temporary bugs
- Current TODOs
- Generated graph content
- Details that are easy to derive from the code
- Aging lists of all models, endpoints, or tasks

### Rule of Thumb

Use `docs/project-memory/` to understand intent.

Use Graphify to understand structure.

Use the repository code to understand reality.

When in doubt — read the code.

## Security Rules

- Never open, read, or analyze `.env` and `.env.*` files.
- Do not run commands that print the contents of `.env` files (`cat`, `less`,
  `more`, `grep`, `rg`, `awk`, `sed`, etc. on those files).
- If a task requires access to secrets, ask the user only for masked values,
  e.g. `API_KEY=***`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

# Graphify usage

Use graphify-out/GRAPH_REPORT.md only for:
- architecture questions
- impact analysis
- cross-module changes
- onboarding explanations
- refactoring plans

Do not use Graphify for small localized edits where the target file is already known.

Before large changes, first identify related files/modules using Graphify, then inspect source files directly before editing.
