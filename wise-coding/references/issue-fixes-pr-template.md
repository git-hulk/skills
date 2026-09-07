# PR template — issue fixes

Use this when drafting a fix PR. Keep these four sections unless the target repository requires
its own template. The worked example describes the source PR; use the actual target diff and
test results for a new PR. Follow the target repository's branch convention.

## Contents

- [Template](#template)
- [Worked example — PR #271](#worked-example--pr-271)
- [What this example is doing well](#what-this-example-is-doing-well)
- [Commit message shape](#commit-message-shape)

## Template

````markdown
## Problem

<One paragraph describing the bug. Cover:
- which function / file / behavior is broken,
- the mechanism — *why* it's broken, not just *that* it's broken,
- the user-visible impact (hang, panic, wrong output, security issue).
Quote the offending source if it makes the explanation concrete — a 5-line snippet beats a
file:line reference for a reviewer skimming on a phone.>

## Reproduction

```<language>
<smallest standalone code that triggers the bug>
// observed behavior, e.g. // panic: runtime error: index out of range
```

<Optional: one line on adjacent inputs that *don't* trigger, if it sharpens the diagnosis.>

## Fix

<One or two sentences. Name the change. If you deliberately did *not* touch related code,
say so and why it's safe.>

## Test

<Name the test function. Say what it asserts and any guard you put in (timeout for hangs,
table extension for panics, golden output for misparses). State that it would have caught
the regression — would-fail-without-fix is the bar.>
````

## Worked example — PR #271

> **Title**: Fix infinite loop (DoS hang) on unterminated block comment
> **Branch**: `fix/lexer-unterminated-comment-hang`

````markdown
## Problem

`consumeMultiLineComment` loops on `!l.isEOF()`, which tests `l.current`, but only advances
a **local** index `i`. When a block comment is never closed, `l.current` never moves, so
`isEOF()` never becomes true and the lexer spins forever — a denial-of-service **hang** on
malformed input.

## Reproduction

```go
parser.NewParser("/* unterminated").ParseStmts() // hangs forever
parser.NewParser("SELECT 1 /* x").ParseStmts()   // hangs forever
```

(The exact 2-byte input `/*` is safe because `skipN(2)` already leaves `current` at EOF,
but any content after the opener triggers the hang.)

## Fix

Loop on `l.peekOk(i)` instead, so the loop tracks the local index and terminates at end of
input. When no closing `*/` is found, the remainder is consumed as comment — matching
`consumeSingleLineComment`'s behaviour.

## Test

`TestConsumeUnterminatedComment` drains the lexer in a goroutine guarded by a timeout, so
a regression fails fast instead of hanging the test binary.
````

## What this example is doing well

- **Problem** names the function (`consumeMultiLineComment`), the wrong condition
  (`!l.isEOF()`), the *mechanism* (local `i` vs `l.current` drift), and the *impact* ("DoS
  hang"). A reviewer learns the whole bug in four lines.
- **Reproduction** is two lines. The aside about the safe `/*` input shows the author
  thought through the boundary — and pre-empts a reviewer question.
- **Fix** is one sentence. It names the new check (`l.peekOk(i)`) and ties the new
  behavior to a sibling function (`consumeSingleLineComment`) so the reviewer can confirm
  consistency without reading the diff.
- **Test** explains *how* it guards (goroutine + timeout), not just "added a test". The
  guard is the interesting part — without it, a regression would re-DoS the test binary.

## Commit message shape

The commit body is a tighter version of the PR body — same content, less polish, no
markdown headings. Keep the subject at most 70 characters, separate it from the body with a
blank line, and wrap body prose at about 72 characters. Add attribution trailers only when
provided or required by the repository. A good shape:

```text
<one-line subject — same as PR title>

<paragraph 1: the bug — function name, wrong condition, mechanism, impact>

<paragraph 2: the fix in one or two sentences>

<paragraph 3: what the test does and how it guards>
```

Example (PR #271's actual commit body, lightly annotated):

```text
Fix infinite loop on unterminated block comment

`consumeMultiLineComment` looped on `!l.isEOF()` (which checks `l.current`)
while only advancing the local index `i`, so on an unclosed comment like
`/* unterminated` the lexer spun forever — a DoS hang.

Loop on `l.peekOk(i)` instead so it terminates at end of input.

Add TestConsumeUnterminatedComment to reproduce: it drains the lexer in a
goroutine with a timeout, so a regression fails fast instead of hanging.
```
