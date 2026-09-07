# Examples — real issue-fix PRs

Three reference PRs from `AfterShip/clickhouse-sql-parser` showing the pattern in different
shapes. Read these when you want to see the template applied to a real bug before writing
your own PR.

## [PR #271 — Fix infinite loop on unterminated block comment](https://github.com/AfterShip/clickhouse-sql-parser/pull/271)

**Bug class**: DoS hang — loop never terminates.

**Diff size**: 1 line in `lexer.go`, 33-line test in `lexer_test.go`.

**Key moves**:

- Single-line code change: swap `!l.isEOF()` for `l.peekOk(i)`. The fix is one character
  away from the bug.
- Regression test runs the lexer in a goroutine with `time.After(5 * time.Second)` and
  `t.Fatalf` on timeout, so a regression fails the binary in 5 seconds instead of hanging
  it forever.
- Reproduction includes a note about which `/*` inputs *don't* trigger (just `/*` on its
  own is safe). That aside both sharpens the diagnosis and pre-empts a reviewer "but what
  about..." question.

**What to copy**: the hang-test goroutine pattern, the discipline of a 1-line fix, the
"adjacent input that doesn't trigger" aside in the Reproduction.

## [PR #272 — Fix nil-pointer dereference when formatting errors at EOF](https://github.com/AfterShip/clickhouse-sql-parser/pull/272)

**Bug class**: nil-deref panic on EOF.

**Diff size**: add `lastTokenString()` helper; migrate 11 unguarded call sites. The ~50
success-path uses are explicitly left untouched.

**Key moves**:

- The fix introduces a small helper rather than nil-checking every caller — *minimal*
  doesn't mean *fewest lines*, it means *smallest reasonable change*. Adding 50 inline
  guards would have been a worse fix.
- The PR explicitly calls out which call sites are *not* changed and why ("provably
  non-nil after a successful match"), so reviewers don't wonder.
- Test extends the existing `TestParser_InvalidSyntax` table with three reproduction
  inputs — using the established test scaffolding instead of inventing a new test
  function.

**What to copy**: the "introduce a helper rather than scatter guards" pattern when a single
bug has many call sites, and the discipline of naming what you intentionally *didn't*
touch.

## [PR #273 — Fix index-out-of-range panic in wrapError at EOF](https://github.com/AfterShip/clickhouse-sql-parser/pull/273)

**Bug class**: index-out-of-range panic.

**Diff size**: 1 line — clamp the loop's upper bound to `len(p.lexer.input)`.

**Key moves**:

- The Problem section quotes the exact offending loop inline, so the reader doesn't have
  to open the source file to follow along.
- The Reproduction (`CREATE--`) is 8 characters. The hang/panic happens because the
  trailing `--` comment leaves the lexer position past end of input — the Reproduction
  also explains *why* those 8 characters are enough.
- Test extends the existing `TestParser_InvalidSyntax` table, following the same shape as
  PR #272.

**What to copy**: quoting the offending source inline in the Problem section, and the
1-line fix discipline.

## Pattern summary across the three PRs

| Aspect            | #271                          | #272                                | #273                              |
| ----------------- | ----------------------------- | ----------------------------------- | --------------------------------- |
| Bug class         | DoS hang                      | Nil-deref panic                     | Index OOB panic                   |
| Source diff       | 1 line                        | Helper + 11 call sites              | 1 line                            |
| Test pattern      | New test, goroutine + timeout | Extend `TestParser_InvalidSyntax`   | Extend `TestParser_InvalidSyntax` |
| Reproduction size | 2 short lines                 | 3 short lines                       | 1 line, 8 chars                   |
| Restraint signal  | Note about safe `/*` input    | Explicit "left ~50 sites untouched" | Quoted offending loop             |

The thread connecting all three: **the diff should be the smallest change that fixes the
named bug, the test should reproduce the exact reported symptom, and the PR description
should let a reviewer approve without opening the source file**.
