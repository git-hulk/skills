# Reading a repository before changing it

You are reading to *predict* what your change should look like, not to explain the project.
Every line you add should be something the repo could have written itself. That needs three
things: the layer map, the conventions, and a sibling to copy from.

## Order of reading

1. **Rules the maintainers wrote down.** `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/`,
   ADRs, the linter config (`.golangci.yml`, `eslint.config.*`, `ruff.toml`, `clippy.toml`).
   These encode constraints you cannot infer from code, and violating one costs a review round.
2. **Wiring.** `main`, the DI container, the router or command tree, the top-level constructor.
   This gives you the layer list and who owns whom.
3. **The boundary of each layer you will touch.** Router / proto / CLI definitions (API),
   service interfaces and model types (domain), migrations / models / store package (storage).
   Note the *conversion points*: where a request struct becomes a domain call, where a row
   becomes a model, how errors are translated at each crossing.
4. **The sibling feature, end to end.** Pick the existing feature closest to yours — same entity,
   same kind of operation — and read every file it touches, migration to handler to test, full
   bodies. Write down the file list; your change will touch the analogous files.
5. **Tests of the sibling.** They show which behaviors the maintainers thought worth protecting,
   the fixtures they use, and the assertion style. Your tests should be indistinguishable.
6. **History.** `git log --oneline -- <sibling files>` and the PR it points to often explain a
   choice (why nullable, why a separate table) that you would otherwise "fix".

## Finding the sibling

- Same entity, different operation: adding `archive` to `Project` → read how `Project.disabled`
  or `Project.deletedAt` is handled.
- Same operation, different entity: adding `PATCH /teams/{id}` → read `PATCH /users/{id}`.
- Same mechanism: adding a background check → read the existing scheduler's checks.
- A new statement in a parser: read the most recently added statement of the same category
  (its AST node, parse function, formatter case, and testdata file).

If two siblings disagree (an old style and a new style), follow the newer one and say so. If
there is no sibling, the change is introducing a pattern — that is a step-2 question for the
user, not a solo decision.

## Budget by size

| Source lines (tests excluded) | What to read yourself |
| --- | --- |
| < 20k | Everything in the layers you touch; skim the rest |
| 20k – 100k | Wiring, boundaries, the sibling; fan out subagents for the remaining packages you depend on |
| > 100k | Same, scoped to the subsystem; name what you did not read |

## Subagent fan-out brief

When the repo is large, spawn one `Explore` agent per package you depend on with this brief:

```text
Read <package path> in <repo path> completely (every non-test file; skim tests for intent).
Return, and nothing else:
1. CONCEPTS — project-specific nouns defined here: name | one-sentence meaning | file:line
2. PUBLIC SURFACE — exported types / interfaces / functions: symbol | role | file:line | who imports it (grep)
3. CONVENTIONS — naming, error handling, logging, validation location, test layout, with one example file:line each
4. SIBLING — the existing feature most like "<the change>": every file it touches, in call order
5. SURPRISES — anything the docs or comments claim that the code does not do
Cite file:line for every item. Do not summarise; list.
```

## What to write down

Keep a scratch list with: **concepts** (glossary candidates), **files by layer** (the sibling's, and
therefore yours), **conventions** (one line each), **questions** (anything the code did not
settle — these become grill questions in step 2).
