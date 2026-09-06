---
name: fast-learning
description: >
  Learn an unfamiliar code repository from scratch and end up able to defend a mental model of
  it: glossary of the project's critical concepts (from README, docs/, and the external doc site),
  how the concepts relate, then — for a service — architecture, critical data flows, database
  schema, and key APIs as Mermaid diagrams plus an API-orthogonality analysis; for a library —
  the public interface map plus an interface-orthogonality analysis; finishing with a guided
  interview that checks the user's understanding one question at a time. Use this whenever
  the user wants to understand, onboard onto, ramp up on, study, explore, or "get the full
  picture" of a repo, service, library, or codebase they don't know yet — including "how does
  this project work", "walk me through this repo", "explain the architecture", "what are the
  key concepts here", "learn this codebase", "帮我理解这个项目 / 熟悉代码库 / 梳理架构" — even
  when they ask for only one piece (just the concepts, just the data flow, just the schema).
---

# Fast Learning

Turn a repository you have never seen into a model the user can *defend*: vocabulary first,
then how the vocabulary connects, then the structure (architecture / flows / schema / APIs),
then a design judgement (orthogonality), and finally an interview that finds the gaps. Reading
order matters: a diagram whose boxes are words the user cannot define teaches nothing.

## Don't trigger for

| Situation | Use instead |
| --- | --- |
| A bug or regression in a repo the user already knows | A debugging workflow |
| Writing repository-level instruction files | An instruction-authoring workflow |
| Designing a *new* change to the repo | A technical-design workflow |
| Checking an API against a specific design standard | An API-guidelines review |
| Stress-testing the user's own plan (no repo to learn) | A design-review interview |

## Principles

- **Code is the truth, docs are hypotheses.** Read README and the doc site first because they
  give you the *intended* vocabulary, then verify every concept and every arrow against code. When
  they disagree, report the disagreement: that gap is exactly what trips a newcomer.
- **Every claim cites a location** — `path/file.go:123` or a doc URL. A diagram box without a
  citation is a guess; the user will ask "where is that?" and you must already know.
- **Read deep, not wide.** Follow [`references/reading-strategy.md`](references/reading-strategy.md).
  "Good detail" means the full bodies of the wiring, the boundaries, and the hot paths, read by
  you. Open another directory only when a flow, a glossary concept, or an API handler leads you
  there; do not sweep every package, and do not split research one directory per worker — that costs
  more than it teaches and tends to exhaust the session. Stay inside the repository being
  studied: never read sibling checkouts, the module cache, or the user's other projects.
- **Write for a learner.** Tables for inventories, diagrams for structure (≤ 12 nodes each, one
  idea per diagram — conventions in [`references/diagrams.md`](references/diagrams.md)), prose only
  for *why*. Post each finished section into the reply as you go rather than one dump at the end;
  a person absorbs a glossary, then a map, then flows.
- **Ask nothing you can look up.** The only questions for the user are about *their*
  understanding and *their* goals; the codebase answers everything else.

## Workflow

Copy this checklist into your reply and tick items off as you go.

```text
Fast-learning progress: <repo>
- [ ] 0. Locate, inventory, classify (service / library / CLI / mixed)
- [ ] 1. Glossary of critical concepts (README → docs/ → external doc site → code)
- [ ] 2. Concept relationship map + explanation
- [ ] 3. Structure track:
        service  → architecture, data flows, schema, API map, API orthogonality
        library  → interface map, internal flow if stateful, interface orthogonality
- [ ] 4. Assemble and save the report
- [ ] 5. Guided interview (one question at a time) or written question tree
```

### 0. Locate, inventory, classify

Run the bundled inventory (read-only, stdlib Python) from the repo root, or pass the path:

```bash
python3 <skill-dir>/scripts/inventory.py <repo-dir>
```

It prints languages and line counts, manifests, entry points, API / storage / docs signals, the
external URLs in the README, a depth-2 layout, and a `kind_guess` with the signals behind it.
Treat the guess as a hypothesis; confirm it by reading the entry point and the README, then decide:

| Kind | Tell-tale | Track in step 3 |
| --- | --- | --- |
| **Service** | Long-running process, listens on a port or consumes a queue, owns storage | service |
| **Library / SDK / framework** | Imported by other code; no `main`, or `main` only in examples | library |
| **CLI tool** | Runs to completion; commands are the API, files/config are the schema | service track, with commands as the API and on-disk state as the schema |
| **Mixed** (service that ships a client SDK, library with a daemon) | Both sets of signals | both tracks, each scoped to its part |
| **Monorepo** | Several manifests / services | Take the component the user named; if none, list the components in one line and pick the one the README leads with, saying so |

If the current directory is not the repo the user meant (it is a docs repo, a skills repo, or
unrelated), stop and ask for the path or GitHub URL; never learn a repo you have not read. To
clone from a URL, use `gh repo clone` after checking `gh auth status`.

State the result in one line before moving on:
"`<repo>` is a `<kind>` in `<language>`, ~N lines, entry at `<path>`, storage `<what>`, docs at `<url>`."

### 1. Glossary of critical concepts

Sources, in this order, because each narrows the next:

1. **README** in full, then everything under `docs/`, `ARCHITECTURE.md`, `DESIGN.md`, ADRs.
2. **External doc site** — every URL the inventory listed under `doc url`. Fetch the pages that
   explain concepts (look for *concepts*, *architecture*, *design*, *glossary*, *overview*,
   *getting started*, *how it works*) and follow one level of links from those. Skip API
   reference dumps and changelogs. If a fetch fails, say which URL and go on.
3. **Code** — exported type / class / interface names that appear in many files, package and
   directory names, config keys, CLI subcommands, table names, proto messages, enum values,
   error kinds. Read the definition site of each candidate, not just its name.

A concept is *critical* when at least one holds: you cannot narrate the main flow without it; it
names a boundary (a component, a store, a protocol, a lifecycle stage); or the project overloads
an ordinary word (`Node`, `Session`, `Shard`, `Job`, `Context`) with a project-specific meaning.
The overloaded ones matter most — they are where a reader's prior knowledge misleads them.

Output a table, 10–30 rows. Under 8 means you have not read enough; over 40 means ordinary
vocabulary crept in — demote it.

| Concept | Meaning in this project (1–2 sentences) | Defined at | Confusable with |
| --- | --- | --- | --- |

"Defined at" is the type/struct/class declaration or the doc URL. "Confusable with" names the
everyday or other-project meaning the reader should *not* apply, or "—".

### 2. Concept relationship map

Draw one Mermaid `flowchart` whose nodes are glossary concepts and whose edges are labelled
relationships — `owns`, `contains N`, `assigned to 1`, `produces`, `consumes`, `implements`,
`routes to`, `persisted in`, `elected from`. Cardinality and ownership are the point: "a
Cluster has many Shards; each Shard has exactly one master Node" is knowledge, "Cluster — Shard
— Node" is not. Cite where each edge is enforced (the field, the foreign key, the validation).

Then explain the map in prose, walking from the outermost concept inward, one paragraph per level.
Call out relationships that surprised you or that the docs describe differently from the code.

### 3. Structure track

Pick the track from step 0. Both tracks end with an orthogonality analysis; use the rubric in
[`references/orthogonality.md`](references/orthogonality.md) — it defines the concept, gives the six
checks, and a scoring table, so the analysis is evidence rather than an adjective.

#### Service track

1. **Architecture.** Process boundaries first (how many binaries, what talks to what over the
   network), then in-process layers (transport → handler → domain → storage). One `flowchart`
   with a subgraph per process and externals (databases, queues, other services) as distinct
   shapes. Cite the wiring code: `main`, the dependency-injection or router setup.
2. **Critical data flows.** Choose 3–5: the primary write path, the primary read path, the
   background loop (scheduler, reconciler, consumer), startup/bootstrap, and one failure or
   recovery path (election, retry, migration, failover). One `sequenceDiagram` each, participants
   taken from the architecture diagram, every arrow labelled with the function that performs it.
   After each diagram, one sentence on what breaks if that step is skipped — that is what makes
   the step memorable.
3. **Schema.** From migrations, models, or the storage package. One `erDiagram` with keys and
   cardinalities, then analysis: the aggregate root, hot write paths, denormalisations and why,
   soft delete / versioning / optimistic locking, indexes versus the queries seen in the flows.
   For key-value, document, or coordination stores (etcd, Redis, ZooKeeper, RocksDB) the *key
   layout* is the schema: a table of key prefixes → value type → writer → reader, plus the
   consistency mechanism (transaction, CAS, watch, lease). Skip only if the service owns no state,
   and say so.
4. **API map.** Enumerate every endpoint / RPC / command from the router, proto, or command tree,
   grouped by resource. Mark the ones the data flows touch as *key APIs* and describe their
   request/response shape and error semantics.

   | Method + path (or RPC / command) | Purpose | Handler | Entities read / written | Auth |
   | --- | --- | --- | --- | --- |

5. **API orthogonality.** Apply the rubric to the API map.

#### Library track

1. **Interface map.** Start at the package a user imports and work outward: constructors and
   options, the core types, the interfaces the *caller* must implement (extension points) versus
   the ones the library provides, and the lifecycle (`New → Start → use → Close`). One
   `classDiagram` for the core types and their implementations, plus this table:

   | Symbol | Kind (type / interface / func / option) | Role | Implemented by (library / caller) | Defined at |
   | --- | --- | --- | --- | --- |

2. **Usage narrative.** The minimal program a user writes, in the library's language, lifted
   from `examples/`, the README, or the tests, with a comment per line naming the interface it
   touches. If none exists, write it from the constructor's signature and say it is untested.
3. **Internal flow, if the library is stateful.** A library with goroutines / threads, a state
   machine, or background I/O (consensus, connection pools, schedulers) gets one `sequenceDiagram`
   or `stateDiagram` of its main loop — a user cannot reason about the API's guarantees without
   it. A pure-function library skips this and says so.
4. **Interface orthogonality.** Apply the rubric to the interface map.

### 4. Assemble and save the report

Fill in [`references/report-template.md`](references/report-template.md) with the sections above
and save it as `<repo-name>.md` in the current working directory unless the user names another
location. Tell the user the path.

### 5. Guided interview

Now interview the user about the repository one question at a time, following
[`references/grill.md`](references/grill.md): build a question tree from the report's design
decisions, ask **one question at a time**, give your recommended answer with its citation, and
walk each branch until it is resolved. The questions test *understanding and judgement* — "why is
X separate from Y", "what would you expect if Z were removed", "which component changes to add
W" — never facts the code could answer for you. When the user's answer conflicts with the code,
show the code. Track resolved branches in a checklist and finish with an *Open questions* list of
things only the maintainers can answer.

If the run is non-interactive, write the full question tree with
recommended answers into the report's final section instead and say that the session was skipped.

## Reference files

| File | Read it when |
| --- | --- |
| [`references/reading-strategy.md`](references/reading-strategy.md) | Before step 1 — how to read a repo in good detail within budget, including narrowly scoped parallel research |
| [`references/diagrams.md`](references/diagrams.md) | Before drawing any diagram — Mermaid conventions per diagram type |
| [`references/orthogonality.md`](references/orthogonality.md) | Step 3 — definition, six checks, scoring table |
| [`references/report-template.md`](references/report-template.md) | Step 4 — section order and headings |
| [`references/grill.md`](references/grill.md) | Step 5 — building the question tree and running the interview |
