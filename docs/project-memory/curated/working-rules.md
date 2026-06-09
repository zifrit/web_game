# Working Rules

## Source priority

Project Memory helps explain intent, but it does not prove the current
implementation. Trust order:

1. Current repository code.
2. Tests, migrations, schemas, configs, and runtime settings.
3. Fresh Graphify analysis, for example `graphify-out/GRAPH_REPORT.md`.
4. Project documentation.
5. `docs/project-memory/`.
6. Previous discussions and assumptions.

If Project Memory, Graphify, or documentation conflicts with code, trust the
code and update the relevant memory files after the change.

## Before changes

- For small local changes: inspect the target file, check the nearest tests or
  usages, then make the smallest safe change.
- For deep, architectural, or cross-module work: start with
  `docs/project-memory/INDEX.md`, open the relevant `curated/` and
  `inventories/` files, use Graphify for structure, verify assumptions against
  current code, state the plan, and only then edit files.
- Do not use Project Memory as evidence of exact model fields, API behavior,
  signatures, business logic, dependencies, DB schema, background task flow, or
  current frontend component structure.

## Git hygiene

- The working tree may be dirty; do not revert or overwrite user changes
  without an explicit request.
- If new generated/local runtime files appear during work, do not commit them;
  add a pattern to `.gitignore` when appropriate.
- `frontend/next-env.d.ts` may be rewritten by Next in dev/build mode, so check
  it carefully before committing.

## Generated and local files

Do not commit:

- `.env`
- `.venv/`
- `backend/.venv/`
- `backend/db.sqlite3`
- `backend/celerybeat-schedule`
- `frontend/node_modules/`
- `frontend/.next/`
- `frontend/tsconfig.tsbuildinfo`
- `.DS_Store`
- `.idea/`

## Security

- Never open, read, or analyze `.env` and `.env.*`.
- Do not run commands that print `.env` file contents, including `cat`, `less`,
  `more`, `grep`, `rg`, `awk`, or `sed` on those files.
- If a task needs secrets, ask the user for masked values.

## Graphify

- For codebase questions, first run `graphify query "<question>"` when
  `graphify-out/graph.json` exists.
- For relationships, use `graphify path "<A>" "<B>"`; for focused concept
  explanations, use `graphify explain "<concept>"`.
- If `graphify-out/wiki/index.md` exists, use it for broad navigation instead
  of raw source browsing.
- Read `graphify-out/GRAPH_REPORT.md` only for architecture questions, impact
  analysis, cross-module changes, onboarding explanations, refactoring plans,
  or when query/path/explain did not provide enough context.
- Dirty `graphify-out/` files are expected after hooks or incremental updates
  and are not, by themselves, a reason to skip Graphify.
- After code changes, run `graphify update .`.

## Before handoff

- Backend-only change: `uv run python manage.py check` and targeted Django
  tests.
- API/game-flow change: add or update tests in `backend/apps/game/tests/`.
- Frontend change: `npm run build`.
- Docker/config change: `docker compose config --quiet`; if possible, start
  compose and smoke-check `3000`/`8000`.
- Docs-only project memory change: inspect changed markdown files, links, and
  confirm no `.env` / `.env.*` contents were copied; backend/frontend build is
  not required.
- In the final response, mention checks that could not be run and why.
