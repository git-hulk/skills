# Go Review Standards

## First-Version Standard

Use the [Uber Go Style Guide](https://github.com/uber-go/guide/blob/master/style.md) as the default
coding standard. This first-version checklist was checked against the upstream guide on
2026-09-08; it is a focused review baseline, not a complete copy or an upstream version number.
Read the relevant linked section when its exceptions or details matter.

Explicit user/repository rules and the target version's semantics take precedence. Preserve
documented deviations; do not spread a review into unrelated legacy cleanup. Report standards
violations separately in meaning from bugs, following the finding contract in `SKILL.md`.

## Uber Checklist

- [Interfaces](https://github.com/uber-go/guide/blob/master/style.md#pointers-to-interfaces): pass interface values, not interface pointers; verify intended implementations at compile time.
- [Ownership](https://github.com/uber-go/guide/blob/master/style.md#copy-slices-and-maps-at-boundaries): copy mutable slices/maps at boundaries that retain or expose internal state.
- [Cleanup](https://github.com/uber-go/guide/blob/master/style.md#defer-to-clean-up): use `defer` for cleanup; keep [mutexes](https://github.com/uber-go/guide/blob/master/style.md#zero-value-mutexes-are-valid) as non-embedded fields.
- [Errors](https://github.com/uber-go/guide/blob/master/style.md#handle-errors-once): handle each error once; return context instead of logging and returning the same failure. Handle failed assertions; avoid recoverable-error panics.
- [Dependencies](https://github.com/uber-go/guide/blob/master/style.md#avoid-mutable-globals): inject dependencies instead of mutable globals; avoid `init()` except documented exceptions; keep process exits in `main`.
- [Goroutines](https://github.com/uber-go/guide/blob/master/style.md#dont-fire-and-forget-goroutines): establish shutdown and waiting, or a bounded completion condition; do not launch goroutines in `init()`.
- [APIs](https://github.com/uber-go/guide/blob/master/style.md#avoid-embedding-types-in-public-structs): avoid public struct embedding; use explicit serialization tags and `time` types for time values.
- [Style](https://github.com/uber-go/guide/blob/master/style.md#style): separate standard-library imports, reduce nesting, use named struct fields, and favor clear local naming.

Do not install Uber-specific dependencies or introduce functional options solely to satisfy this
reference. Check the existing API and dependency policy before proposing such changes. Formatting
findings should cite a definite rule, not a personal preference, and should not repeat lint output.

## Establish the Version and Contract

Inspect the owning module's `go.mod`, applicable `go.work`, build tags, toolchain, CI platforms,
and lint configuration. A newer installed compiler alone does not establish the package's
language version. Apply the standard and precedence above; the language specification and relevant
package contracts govern correctness. Do not require API modernization outside the patch.

## Review Questions

| Area | Check when affected | Evidence needed before reporting |
| --- | --- | --- |
| Errors | Lost errors, shadowed `err`, incorrect wrapping, changed `errors.Is`/`As` behavior, typed-nil interfaces | A caller or branch that misinterprets the result |
| Context | Propagated deadlines and cancellation, cancel-function ownership, detached work | A path that outlives its required lifetime or loses request metadata |
| Goroutines | Exit conditions, blocked sends/receives, shutdown ordering, joining work | A reachable schedule that leaks, deadlocks, panics, or races |
| Synchronization | Shared maps and slices, copied used mutexes, atomic/lock protocols, wait-group ordering | Actual concurrent access and the missing synchronization relationship |
| Ownership | Slice backing-array aliases, buffer reuse, retained pointers, pooled objects | A consumer that observes later mutation or uses returned storage too long |
| Resources | File/body closure, loop-scoped `defer`, transaction commit/rollback, iterator errors | The failing or repeated path and its leak, lost error, or incomplete operation |
| Boundaries | Nil versus empty encoding, omitted fields, numeric conversion, UTF-8 byte/rune assumptions | A wire contract, stored value, or supported input that changes behavior |
| API changes | Interfaces, receiver changes, zero-value behavior, error contracts | A supported consumer broken by the changed public surface |

Do not infer a race solely from a shared value: inspect ownership and synchronization. Likewise,
discarding a cleanup error is not automatically a bug; explain why that error affects the result.
For channel closure, identify the sender/closer ownership before recommending who should close it.

## Version-Sensitive Traps

- Loop variables declared by the loop have per-iteration semantics under Go 1.22+ language
  semantics. Do not report the historical closure-capture bug without checking the effective
  language version and declaration form. Assignment to an existing variable still reuses it.
  See [the Go team's loop-variable explanation](https://go.dev/blog/loopvar-preview).
  This version check also applies to older loop-capture advice in Uber's parallel-test examples.
- Timer behavior, standard-library APIs, and build-constraint semantics can depend on version or
  runtime settings. Check the matching release/package documentation before asserting a defect.
- Nil and empty slices can differ at serialization boundaries even when their lengths match;
  determine whether the consumer distinguishes `null`, `[]`, and omitted fields.

## Focused Verification

Use the repository's existing test commands. Typical targeted checks, with real package paths:

```sh
go test ./path/to/package -run TestRelevant -count=1
go vet ./path/to/package
go test -race ./path/to/package -run TestRelevant -count=1
```

Run race checks for concurrent behavior when the platform and toolchain support them; a clean
run covers only executed paths. Use broader package tests for exported-contract changes. Inspect
build tags, integration dependencies, and test side effects before running unfamiliar suites.
Read formatter/linter configuration rather than running formatting commands that rewrite files.

## Primary Sources

- [Go specification](https://go.dev/ref/spec): language rules; consult version history as needed.
- [Go memory model](https://go.dev/ref/mem): synchronization and happens-before relationships.
- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments): review conventions, not all
  mandatory correctness rules; supplementary to the Uber baseline.
- [Standard library](https://pkg.go.dev/std): check the documentation for the selected version.
- [Race detector](https://go.dev/doc/articles/race_detector): usage and limitations.
