# Reading a repository in good detail

The goal is to read enough that every box, arrow, and glossary row you produce is something you
saw, not something you inferred from a directory name. This file says how to get there without
reading 80k lines top to bottom.

## Order of reading

1. **Entry point → wiring.** `main`, the DI container, the router / command tree, the
   constructor of the top-level object. This tells you which components exist and who owns whom
   before you read any component. Note every constructor call: that is your component list.
2. **The boundary files.** Router / proto / command definitions (API surface), migrations /
   models / store package (schema), config struct (every knob is a concept the project has).
3. **The hottest path end-to-end.** Take the primary write request from transport to storage
   and read every function body on the way. Do the same for the primary read. Now you can draw the
   first two sequence diagrams from memory.
4. **Each remaining package**, declarations first (types, interfaces, exported funcs, doc
   comments), then bodies of anything the wiring or the hot paths call.
5. **Tests as documentation.** Integration tests show the intended call sequences and the
   invariants; table tests enumerate the edge cases the authors cared about. Read the names and
   the setup helpers even when you skip the bodies.
6. **History for intent.** `git log --oneline -- <path>` on a confusing package, and the PR or
   ADR it points to, explains *why* far faster than staring at the code.

## Scope

Read only what the entry point, the boundaries, and the flows lead you to, and only inside the
repository under study. A package nothing in the hot paths imports is context, not knowledge;
note it in one line ("`internal/integration/*`: 29 outbound connectors, all behind
`integration.SendEntry`") and move on. Never read sibling checkouts, the module cache, or
unrelated directories to "fill in" a dependency — cite the import and its doc URL instead.

## Budget by size

| Source lines (tests excluded) | What "good detail" means |
| --- | --- |
| < 20k | Read every non-test file yourself. |
| 20k – 100k | Read wiring, boundaries, and hot paths in full; read other packages only as the flows reach them, declarations first. |
| > 100k | Same, scoped to the subsystem the user cares about; name what you left out. |

Line counts come from `scripts/inventory.py`.

## Parallel research: rarely, and never one worker per directory

Keep the reading in one coherent pass when possible; the same reader needs enough context to
judge relationships and run the interview. Split out at most one or two narrow investigations,
only when a single hot path crosses a package too large to read inline (a generated client, a
parser family), with a brief such as:

```text
In <repo path>, follow <function> from <file:line> to where it <persists / sends / returns>.
Return only: the call chain (function names with file:line), the types crossing each boundary,
and anything the doc comments promise that the code does not do. No summaries, no inventories.
```

Never divide work as "read package X completely" — that produces an inventory that must be
re-read, and broad parallelism exhausts the session before the report is written.

## Tools that save reading

- `grep -rn "type X " --include=*.go` / `rg "class X\b"` to find definition sites; `rg "\bX\b" -l | wc -l`
  to measure how widespread a concept is (a concept used in 30 files is critical; one used in 1 is local).
- LSP `go to definition` / `find references` when available — cheaper than grep for call graphs.
- `git log --oneline -- <path> | head` and `git log -S "<symbol>" --oneline | head` for intent.
- An HTTP or browser tool for the doc site; fetch the concept pages, not the API reference.

## What to write down as you read

Keep a running scratch file with four lists: concepts, components, flows, questions. Every time a
name confuses you, that is a glossary candidate. Every time you ask "why is this here", that is an
interview question — keep it; you will use it in step 5.
