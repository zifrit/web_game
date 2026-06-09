# Project Memory

`docs/project-memory/` is a compact navigation layer for the Browser Async RPG
MVP. It helps quickly identify where each domain lives, which entrypoints exist
in the project, and which knowledge has already been verified against code.

## Sources Of Truth

Project Memory helps explain project intent, history, and rules, but it is not
the source of truth for the current implementation. If memory conflicts with the
project, use this trust order:

1. Current repository code.
2. Tests, migrations, schemas, configs, and runtime settings.
3. Freshly generated project analysis, for example
   `graphify-out/GRAPH_REPORT.md`.
4. Project documentation.
5. This project memory.
6. Previous discussions and assumptions.

When conflicts appear, trust the code and update memory. If Graphify or
documentation disagrees with code, verify the real repository implementation
first. Do not read `.env` or `.env.*`, and do not copy their contents into
memory.

## Memory Model

- `curated/` - hand-written memory: project meaning, architectural navigation,
  domain rules, frontend/backend preferences, and gotchas.
- `inventories/` - generated-style inventory: lists and snapshots verified by
  code inspection. These are manually maintained markdown files; there is no
  generator.

## How To Use

- Before deep work, first open `INDEX.md`, then the relevant files from
  `curated/` and `inventories/`.
- For small local changes, inspect the target file directly, check the nearest
  tests or usages, and make the smallest safe change.
- For architectural, cross-module, or onboarding tasks, use Graphify first when
  `graphify-out/graph.json` exists; prefer `graphify query`, `graphify path`,
  and `graphify explain` before reading the larger
  `GRAPH_REPORT.md`.
- Open `curated/overview.md` for broad context.
- Open `curated/architecture.md` to locate a domain or entrypoint.
- Open `curated/working-rules.md` to check git/security/handoff and Graphify
  rules before changes.
- Check `inventories/` when you need an exact list of API routes, modules,
  screens, runtime services, or verification commands.
- Check `curated/gotchas.md` before making changes.
- After code changes, run `graphify update .` to keep the graph current.
