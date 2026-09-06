---
name: wise-coding
description: >
  Implement a change inside an existing codebase the way its maintainers would have written it:
  read the repo in detail first, reuse its vocabulary instead of inventing concepts, run a grill-me
  style interview when a decision is not obvious from the code, then design and build in
  dependency order — storage schema, service interface and model, HTTP/RPC protocol — keeping
  every exported symbol, parameter, and endpoint to the minimum callers actually use, and adding
  only the few tests that protect behavior and compatibility. Use this whenever the user asks to
  add, implement, build, support, wire up, extend, or expose something in a repo they already
  have — a feature, a field, an endpoint, a table, a CLI flag, a library capability, a refactor —
  even when it sounds small, and especially when it touches a database, a service interface, or
  an API. Also for "写代码 / 实现这个功能 / 加个接口 / 加个字段".
---

# Wise Coding

Code added to a repository is judged by how invisible it is: it reads like the code around it,
uses the words the project already uses, and exposes nothing the rest of the system does not
call. Every exported function, every parameter, every endpoint is a promise you make on the
maintainers' behalf, and promises are cheap to make and expensive to withdraw. So the order of
work is read → name → decide → design each layer → implement it → audit the surface → test the
behavior, and the skill below exists to keep that order under time pressure.

## Don't trigger for

| Situation | Use instead |
| --- | --- |
| Understanding a repo with no change to make | `fast-learning` |
| A change big enough to need an RFC before code (new system, cross-service) | `write-technical-design`, then come back here |
| A bug, panic, or regression | `diagnose` |
| The user explicitly wants a red-green-refactor loop | `tdd` |
| Checking an API against the AfterShip guidelines only | `rest-api-design` (use it *inside* step 5 when the repo follows those guidelines) |

## Principles

- **Vocabulary is inherited.** The repo already has a word for most things you will touch. A
  new concept is a cost every future reader pays; introduce one only when no existing concept fits,
  and when you do, write down why and how it relates to the concepts it sits next to.
- **Package and module layout is designed before files are added.** Understand the repository's
  existing package or module boundaries and dependencies first. Before adding a file, package,
  or module, state where it belongs, what responsibility it owns, and what may depend on it.
- **Packages and modules are orthogonal.** Give each one a distinct responsibility and avoid
  overlapping contracts, circular dependencies, or parallel implementations of the same
  concept. Prefer extending the existing owner over creating a competing boundary.
- **Search before adding shared code.** Search the repository for an existing helper or common
  function with the same responsibility before creating one. Reuse or extend it when it fits,
  and merge overlapping helpers when their semantics and ownership are compatible.
- **Surface area is a contract.** Method parameters, return types, interface methods, and API
  fields are the protocol between you and every caller. Private by default; export only what
  another package or client uses *now*, not what someone might want later.
- **Ask when unsure, look up when possible.** If the code can answer, read it. If only the user
  can — product behavior, naming trade-offs, backward-compatibility policy — interview them one
  question at a time with a recommended answer ([`references/grill.md`](references/grill.md))
  rather than guessing and hoping.
- **Design each layer before implementing it, in dependency order.** Storage shapes the model,
  the model shapes the service, the service shapes the API. Designing the API first and working
  backwards produces a schema bent to fit a URL.
- **Tests protect behavior, not lines.** A test per function is a maintenance tax that catches
  nothing; a test per behavior that must not change is insurance.

## Workflow

Copy this checklist into your reply and tick items as you go. Post each layer's design into the
reply *before* writing its code; the design is what the user reviews, and it is the contract the
next layer depends on.

```text
Wise-coding progress: <change>
- [ ] 0. Read the repo: layers, conventions, and the sibling feature
- [ ] 1. Restate the change in the repo's vocabulary (new concepts justified)
- [ ] 2. Confidence check → grill the user on what the code cannot answer
- [ ] 3. Storage: design schema / key layout → implement store code   (skip if no state)
- [ ] 4. Service: design interface + model → implement                 (skip if no domain logic)
- [ ] 5. API: design HTTP/RPC protocol → implement handlers            (skip if not exposed)
- [ ] 6. Export audit: everything private unless used elsewhere
- [ ] 7. Tests: compatibility first, then critical behavior
- [ ] 8. Verify with the repo's own build / lint / test, then summarize
```

Steps 3–5 are conditional. Say "no storage change" or "not exposed over an API" explicitly
rather than silently skipping, so the reader knows you considered it.

### 0. Read the repo in detail

Follow [`references/reading.md`](references/reading.md). The goal is not a full mental model of
the project (that is `fast-learning`) but three specific things:

1. **The layers and their boundaries** — where transport, domain/service, and storage live,
   and how a request crosses between them (DTO conversions, error mapping, transactions).
2. **The conventions** — naming, file placement, error types, logging, how tests are organised,
   how migrations are numbered, how routes are registered, what the linter enforces.
3. **The sibling feature** — the existing feature most like the one you are adding. Trace it
   through every layer, migration to handler to test. It is your template: the shape of your
   change should be predictable from its shape. If no sibling exists, say so; that is a signal
   the change is bigger than it looks.

Read the sibling's full bodies, not its signatures. Read `CLAUDE.md`, `AGENTS.md`,
`CONTRIBUTING.md`, and the linter config, because they encode rules the code alone does not show.

### 1. Restate the change in the repo's vocabulary

Write a short glossary of the concepts the change touches — existing ones first — then restate the
request using only those concepts. This is where invented words get caught.

| Concept | Meaning in this project | Defined at | Status |
| --- | --- | --- | --- |
| `Feed` | A subscribed source polled by the scheduler | `internal/model/feed.go:21` | existing |
| `mute` | Suppress polling of a feed until a time | — | **new** |

For every **new** row add one sentence each on: *why no existing concept covers it* and *how it
relates to the concepts beside it* ("`mute` is a property of `Feed`, checked by `Scheduler` where
it already checks `disabled`"). Prefer extending an existing concept (a new state of an existing
enum, a new field on an existing entity) over a parallel concept. If you find yourself adding
a second word for something that already has one — `Account` beside `User`, `Repository`
beside `Store` — stop; that is the most common way codebases rot.

### 2. Confidence check

Before writing any design, answer these for yourself:

- Which files change in each layer, and which sibling do they mirror?
- What is the storage representation, and is it compatible with existing rows / keys?
- What are the exact signatures of the new or changed methods?
- What does the user expect for every ambiguous behavior (defaults, validation, what happens to
  existing data, what an invalid state returns)?
- Is there a backward-compatibility constraint (public API, serialized format, wire protocol)?

If any answer is a guess and the code cannot settle it, run the interview in
[`references/grill.md`](references/grill.md): one question per message, each with your
recommended answer and the evidence behind it, walking each branch until resolved. Questions
that the code can answer are not questions for the user.

When nobody can answer (batch run, `-p`, subagent), do not stall: choose the most conservative
option — the one that adds the least surface and changes no existing behavior — write it under
an **Assumptions** heading at the top of your reply, and proceed. An assumption stated once is a
review comment; an assumption buried in code is a bug.

### 3. Storage: design, then implement

Only if the change persists something. Design first, as text in the reply:

- **SQL**: the DDL of the migration (columns, types, nullability, defaults, indexes) and the
  queries the service will need. Check the migration convention (numbered files, an array of
  functions, an ORM's auto-migration) and append, never edit an applied migration. State what
  existing rows get as a value.
- **Key-value / document / coordination stores**: the key layout — prefix, value type, writer,
  reader — and the consistency mechanism (transaction, CAS, lease, watch) the sibling uses.
- **In-memory or file state**: the struct/field and who owns its lifetime.

Ask of the design: does the hot query in the service layer have the index it needs? Does a
default exist so that old data behaves as before? Is the representation the smallest that
supports the behavior (a nullable timestamp beats a boolean plus a timestamp)?

Then implement the store code in the store's own style: same query builder or raw SQL, same
error wrapping, same transaction helper. Store methods take and return the store's types; do
not let transport structs leak downward.

### 4. Service interface and model: design, then implement

Design the model change and the service signatures as code blocks in the reply before touching
files. For each new or changed method write the signature and one line on what it guarantees:

```go
// MuteFeed suppresses scheduling of feed until `until`; zero time clears the mute.
// Returns ErrFeedNotFound if the feed does not belong to userID.
func (s *Service) MuteFeed(ctx context.Context, userID, feedID int64, until time.Time) error
```

Rules that keep this layer honest:

- **Fewest methods that express the behavior.** One `MuteFeed(until)` where zero clears, not
  `MuteFeed` + `UnmuteFeed` + `IsMuted` + `GetMuteUntil`. Add the second method when a caller
  exists for it.
- **Parameters are the caller's vocabulary, not yours.** Accept identifiers and domain values;
  do not accept a whole request struct so you can pull two fields from it. Do not accept a
  boolean that selects between two behaviors — that is two methods or an enum.
- **Return what the caller needs, typed.** Not `(map[string]any, error)`; not the raw storage
  row if the API only needs three fields.
- **Errors are part of the signature.** Reuse the repo's sentinel errors or error types. A new
  error kind is a new concept (step 1 applies).
- **Model fields follow the sibling.** Same naming convention, same JSON / DB tags, same
  placement in the struct, same validation location.

Implement only after the signatures are written down. If implementing changes your mind about a
signature, update the design block in the reply and say why.

### 5. API protocol: design, then implement

Only if the change is exposed over HTTP, gRPC, GraphQL, CLI, or an SDK. Design the protocol as a
table in the reply before writing a handler:

| Method + path (or RPC / command) | Request | Response | Errors | Auth |
| --- | --- | --- | --- | --- |
| `PUT /v1/feeds/{feedID}` (existing) | body gains `mute_until: RFC3339 \| null` | feed object gains `mute_until` | 400 invalid time; 404 unknown feed | as existing |

Prefer extending an existing endpoint over adding one, when the sibling would have. Match the
repo's envelope, naming case, error body, status-code table, pagination, and versioning by
reading the sibling handler — not from memory of some other project. If the repo follows the
AfterShip guidelines, run `rest-api-design` on the proposed table now, before implementing.

The handler is a thin adapter: decode and validate the request, call the service, map the error,
encode the response. Business logic that appears in a handler belongs in step 4. Proto or
OpenAPI files, if the repo keeps them, change in this step and generated code is regenerated
with the repo's command, not hand-edited.

### 6. Export audit

Read every diff hunk with one question: *who calls this?* Apply
[`references/export-surface.md`](references/export-surface.md):

- Anything not referenced from another package, module, or client becomes private. "It might
  be useful" is not a caller.
- Every new small helper (a few lines, one call site) is inlined at its call site. A helper
  earns a name when it is called from two or more places *or* names a domain concept the
  glossary already has. A function whose body is a single call to another function is a smell.
- Every new parameter, option, flag, and field has a caller that passes a non-default value in
  this change. Otherwise remove it.
- Interface methods added: is every implementer updated, and did a caller need the method?
- Exported constants, error variables, and types created just for the tests: make them private
  and test through the public behavior instead.

List what remains exported in the summary. If the list is longer than the sibling's, explain
each extra item.

### 7. Tests

Follow [`references/tests.md`](references/tests.md). Write tests in the order of what they
protect:

1. **Compatibility** — the contract a future change could break without noticing: the API
   request/response shape (a golden or table test on the JSON), the migration applied to a
   database that already has rows, the serialized or wire format, the public behavior of an
   exported interface. One test per contract.
2. **Critical implementation** — the logic that would fail in a *subtle* way: the state
   transition, the query with the tricky predicate, the boundary (zero value, expiry, ownership
   check). One test per risk, not per branch.
3. **Nothing else.** No test for a getter, a constructor, a private helper, or a path that
   simply delegates. No mocking of internal collaborators to observe calls.

Tests go where the repo puts them, use the repo's fixtures and assertion style, and read like
specifications: `TestMutedFeedIsSkippedByScheduler`, not `TestMuteFeed`. A typical change adds
two to six tests. Ten or more means you are testing paths, not behavior.

### 8. Verify and summarize

Run what the repo runs — `Makefile` targets, the CI workflow's commands, the linter — and
report results verbatim, including failures you could not fix. Then end with:

```markdown
## Summary
**Assumptions** (if any): …
**Concepts**: existing concepts reused; new concepts and why.
**Changed by layer**: storage → service/model → API, each with files.
**Exported surface added**: <symbol> — used by <caller>. (Should be short.)
**Tests added**: <name> — protects <contract or behavior>.
**Verification**: commands run and their result.
**Open questions**: what only the user or maintainers can settle.
```

## Reference files

| File | Read it when |
| --- | --- |
| [`references/reading.md`](references/reading.md) | Step 0 — reading for a change: layers, conventions, sibling trace, subagent brief |
| [`references/grill.md`](references/grill.md) | Step 2 — building the question tree and running the interview |
| [`references/export-surface.md`](references/export-surface.md) | Steps 4 and 6 — minimal-export rules, helper test, per-language visibility mechanics |
| [`references/tests.md`](references/tests.md) | Step 7 — choosing the few tests that matter, with examples |
