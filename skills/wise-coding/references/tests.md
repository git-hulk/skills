# Tests and verification

Carry explicit test exclusions forward across turns. Reuse the repository's integration
harness with isolated state when checks mutate data. Preserve existing checks at distinct
integration boundaries. Report material gaps and whether checks ran, were skipped, or used
cached results.

## Features

Do not add test cases when implementing features, including rows in existing table tests or
new golden files. Run the repository's relevant existing tests, build, and lint checks. Update
existing assertions only when the agreed behavior changes and those assertions become stale.
Verify the requested behavior through its real entry point, including registration and wiring
when applicable. Report any verification boundary the checks do not cover.

## Bug fixes

Follow [`issue-fixes.md`](issue-fixes.md) for reproduction and regression testing. Keep the
regression guard to the smallest case that reproduces the reported symptom and fails if the
fix is reverted. Prefer a behavior or public-surface test through the affected entry point.
Use the repository's existing test style and fixtures; extend an existing test when that keeps
the case clearer and smaller.

Assert the result a caller relies on, such as returned output, error, status, or persisted
behavior. Do not add a test per line, branch, function, or private helper. Avoid assertions
about internal calls, mocks used only to observe those calls, and tests that merely restate
DDL or implementation details. Add further cases only when they guard distinct reported bugs.
