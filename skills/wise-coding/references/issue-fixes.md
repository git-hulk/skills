# Issue Fixes

Adapted from [AfterShip/skills](https://github.com/AfterShip/skills/tree/19f3295c93842706b05debdc7a77d938f4870346/skills/issue-fixes)
at revision `19f3295c93842706b05debdc7a77d938f4870346`. This is the issue-fixing path of
[`wise-coding`](../SKILL.md). Apply its vocabulary, layout, reuse, and minimal-surface principles
throughout. Follow this sequence instead of the parent's feature-development checklist.

This reference captures the working pattern used in
[`AfterShip/clickhouse-sql-parser`](https://github.com/AfterShip/clickhouse-sql-parser). See
PRs [#271](https://github.com/AfterShip/clickhouse-sql-parser/pull/271),
[#272](https://github.com/AfterShip/clickhouse-sql-parser/pull/272), and
[#273](https://github.com/AfterShip/clickhouse-sql-parser/pull/273) for the canonical shape,
and [`issue-fixes-examples.md`](issue-fixes-examples.md) for a side-by-side breakdown.

## Scope

For new features and refactors without a correctness component, use the parent workflow.
For diagnosis-only requests, investigate and report the cause without implementing a fix.
For performance regressions, use this flow when a concrete failing case can be reproduced.

## Prerequisites

Use the repository's development and test tools. When reading a GitHub issue or publishing a PR
with `gh`, check `command -v gh && gh auth status` before that operation. Local fixes do not require
GitHub access. If the linked issue cannot be fetched through an available authenticated tool,
ask for the issue body rather than guessing the symptom from its title.

## Workflow

Copy this checklist into your reply and tick items off. The order matters: reproducing before fixing is what keeps the diagnosis honest.

```text
Issue-fix progress:
- [ ] Capture the bug (input, observed behavior, expected behavior)
- [ ] Reproduce locally with the smallest possible input
- [ ] Root-cause: name the mechanism, not just the symptom
- [ ] Write the minimal fix
- [ ] Add a regression test that anchors the exact symptom
- [ ] Sanity-check: would the test fail if the fix were reverted? If not, return to step 5
- [ ] Run the repository's relevant checks and report results
- [ ] When requested, commit and publish the PR using the four-section template
```

### 1. Capture the bug

Get from the user (or the linked issue):

- The failing input(s).
- The observed behavior (hang, panic, wrong output, etc.) with the exact error if any.
- The expected behavior, when non-obvious.

If the report is vague (a screenshot, a one-line "doesn't work"), ask before guessing. A
reproduction the maintainer can't run is worse than no reproduction.

### 2. Reproduce

Write a tiny program or test that triggers the symptom. Keep it the *minimum* — strip
whitespace, comments, unrelated tokens, anything not required to reproduce. Examples from
the reference PRs:

```go
parser.NewParser("/* unterminated").ParseStmts() // hangs forever
parser.NewParser("CREATE--").ParseStmts()        // panic: index out of range
parser.NewParser("ALTER ").ParseStmts()          // panic: nil pointer dereference
```

If the bug is a hang, drive the reproduction inside a goroutine guarded by a timeout
(`time.After(5 * time.Second)`) so the test suite itself can't be DoS'd while you debug.

**If it won't reproduce**, do not proceed to a fix — a patch you can't verify is a guess. Work
through the divergence in this order, then report which one it was: wrong version or branch
(inspect the reported commit in an isolated checkout if needed), missing build tags or env, a platform- or
arch-specific path, or an incomplete input (ask the user for the full failing case). If none
of those explain it, stop and tell the user what you tried and what you need from them.

### 3. Root-cause

Read the offending code carefully. State, in one sentence, *why* the symptom happens. Some
recurring shapes (use these as starting hypotheses, not conclusions):

- **Loop never terminates** — the loop's exit condition checks one variable while the body
  advances a different one.
- **Index out of range at EOF** — code indexes `input[i]` while `i` can equal
  `len(input)`. Clamp the upper bound.
- **Nil dereference on EOF** — code calls `.last().Field` where `last()` returns `nil` when
  there's no current token. Introduce a nil-safe accessor.
- **Off-by-one at a boundary** — a boundary token is included/excluded inconsistently with
  the surrounding code.

Don't ship until you can name the cause, not just the symptom. If you find yourself writing
"this also seems to fix...", that's a signal you don't fully understand either bug.

### 4. Fix

Change the smallest set of lines that addresses the root cause. Two patterns from the
reference PRs:

- **Single-site bug** → single-line change (PRs #271 and #273 are both 1-line fixes).
- **Same bug across many call sites** → introduce one small helper, migrate only the failing
  sites, and *explicitly leave the provably-safe sites untouched* (PR #272 calls out that
  ~50 success-path uses are intentionally not changed).

"Minimal" means *smallest reasonable change*, not *fewest lines*. A 5-line helper that
replaces 11 broken call sites is more minimal than nil-checking 11 places inline. Past ~50
lines for a single-symptom bug, re-check the scope — you are probably fixing two things.

### 5. Regression test

Add a test that:

- Uses the **exact** reproduction inputs from step 2 (no paraphrasing).
- Asserts the new correct behavior — no hang, proper error returned, correct output.
- Would fail if the fix were reverted. Mentally revert the diff and walk through the test
  — if it still passes, the test doesn't anchor the bug.

For **hang-class** bugs, run the lexer/parser in a goroutine and `t.Fatalf` on timeout. The
test suite must fail *fast* on regression, not hang.

For **panic-class** bugs, prefer extending an existing `Test*_InvalidSyntax` table over
inventing a new test function — that's the prevailing pattern in the reference codebase and
keeps the diff focused.

### 6. Verify and deliver

Run the relevant repository tests, build, and lint checks. Report the original symptom, root cause,
fix, regression guard, and actual check results. Do not claim a test ran if it was only reviewed.

Commit, push, or open a PR when the user's request includes those actions. Follow the repository's
branch and PR workflow, including stacked PRs where required. Otherwise finish with the verified
local fix and summary. If publication fails, preserve completed work and report the failing step.

**Branch name** — follow the user or repository convention. Otherwise use
`fix/<short-kebab-slug>`. The slug names the *bug*, not the fix:

- `fix/lexer-unterminated-comment-hang`
- `fix/wraperror-index-out-of-range`

**Commit subject** — imperative, ≤ 70 characters, names what's fixed:

- `Fix infinite loop on unterminated block comment`
- `Fix index-out-of-range panic in wrapError at EOF`

**Commit body** — separate the subject with a blank line and wrap prose at about 72 characters.
Use 2–3 paragraphs that walk through: the bug (with a code reference), the
fix in one sentence, the test and how it guards. Same content as the PR body but tighter —
the PR carries the polished version.

**PR title** — same as the commit subject, optionally with a parenthetical impact tag like
`(DoS hang)` when it sharpens the urgency.

**PR body** — use the four-section template below.

**If a git or `gh` publishing step fails**, report what succeeded and what remains:

| Failure | Action |
| --- | --- |
| `gh auth status` not logged in | Ask the user to run `gh auth login`. Do not attempt an unauthenticated push |
| Branch name already exists | Append a short disambiguator (`fix/<slug>-2`) rather than force-updating someone else's branch |
| Push rejected (non-fast-forward) | Rebase onto the updated base and re-run the test suite before pushing again — never `push --force` to a shared branch |
| Push rejected (protected branch / no write access) | Stop and report. Ask whether to push to a fork instead |
| PR submission fails | Report the error, pushed branch if any, and remaining submission step |

## PR description template

Use these four headings in this order unless the target repository requires its own template:

1. `## Problem` — the wrong condition and the mechanism, named function/file, user-visible impact
2. `## Reproduction` — the smallest failing input, in a fenced block, with the observed result
3. `## Fix` — one or two sentences; call out related-but-safe code you deliberately left alone
4. `## Test` — the test name, what it asserts, and the regression guard

Read [`issue-fixes-pr-template.md`](issue-fixes-pr-template.md) before writing the body — it has
the annotated template with per-section guidance and a worked example based on PR #271. Keep
each section tight; only Problem grows when the bug genuinely needs explanation.

## Anti-patterns

- **Drive-by cleanup.** Renaming variables, reformatting, or fixing nearby issues "while
  you're there" buries the actual fix and complicates review. Open a separate PR for the
  cleanup when requested.
- **Test that doesn't anchor the bug.** A test exercising adjacent code that wouldn't fail
  without the fix is not a regression test — it's coverage padding. Verify by mentally
  reverting the diff.
- **Padded reproduction.** A 200-line SQL string when 14 characters trigger the bug. Reduce
  until removing any further would mask the bug.
- **Defensive scope-creep.** Adding nil checks in 50 callers when only 3 hit the failure
  path. Fix at the boundary that's actually broken.
- **Renaming the bug in the title.** Use the failure mode the user/issue reported, not your
  internal diagnosis. The PR title should match what someone bisecting would grep for.
- **Skipping the why.** "Fix bug" / "Refactor consumeMultiLineComment" tells the reviewer
  nothing. Name the failure mode and the mechanism.
