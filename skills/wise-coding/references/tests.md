# Choosing the few tests that matter

A test is worth writing when a future change could break something *and nobody would notice
without the test*. Tests that fail whenever the implementation is refactored, but pass when the
behavior is wrong, are worse than none: they train people to update tests without reading them.
So the unit of testing is a behavior a caller relies on, not a function.

## Two kinds of tests worth adding

### 1. Compatibility tests

These pin a contract that is easy to break silently:

| Contract | Test shape |
| --- | --- |
| API request / response shape | Table or golden test: given this request, the JSON body and status are exactly this. Includes the *absence* of fields you decided not to expose. |
| Schema migration | Apply the migration to a database holding pre-change rows; assert the default value and that the old read path still works. |
| Serialized / wire format | Round-trip: encode → decode → equal; and decode a fixture captured *before* the change. |
| Parser or formatter | Input → AST → `String()` → same input (or a testdata golden file, if that is the repo's convention). |
| Public interface behavior | Call through the exported method exactly as a user would; assert the documented guarantee (idempotency, error kind, ordering). |

One test per contract. If the repo has a golden-file mechanism (`testdata/`, snapshots), add a
case there rather than a new test function — that is where the maintainers will look.

### 2. Critical-implementation tests

These cover logic that would fail *subtly* — pass most inputs, fail one:

- A state transition and its guard ("migration rejected while cluster is read-only").
- A predicate with a boundary ("mute expiring exactly now is treated as expired").
- An ownership or authorization check ("user A cannot mute user B's feed").
- A query with a non-trivial `WHERE` or a join the sibling did not have.

One test per risk. Pick the input that would be wrong under the most likely bug, not one input
per branch.

## What not to add

- A test for each new function. Constructors, getters, setters, and delegating methods have no
  behavior of their own.
- A test that asserts a private function was called, or mocks an internal collaborator to
  observe the call. That tests the implementation's shape.
- A test that reaches around the interface (queries the database directly to check what a
  service method wrote) when the interface can show the same thing.
- A test whose only purpose is to lift coverage on a path with no risk.

## Placement and style

- Same directory and file naming as the sibling's tests; same fixtures, helpers, and assertion
  library. If the repo uses table tests, add rows; if it uses testdata files, add a file.
- Name the behavior: `TestMutedFeedIsSkippedByScheduler`, `test_migration_rejected_when_readonly`,
  `it('leaves mute unchanged when PUT omits mute_until')`.
- Integration tests that need a real database or service: reuse the repo's harness (docker
  compose, test container, build tag). Do not introduce a second harness.

## Sanity check before finishing

Count the tests you added. Two to six is typical for a feature that spans storage, service, and
API. If you have ten, list what each protects; any two that would both fail under the same bug
are one test. If you have zero, you have either a pure refactor with existing coverage (say so)
or a contract nobody is protecting.
