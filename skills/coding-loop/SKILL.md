---
name: coding-loop
description: >
  The entry point for any implementation request: classify the work first — bug fix, small
  feature (≤ 200 changed lines), medium feature (simple scope but > 200 lines), or large
  feature — then route it through the right skills in order: `issue-fixes` for bugs,
  `wise-coding` for small features, `task-breakdown` + `wise-coding` for medium ones, and
  `write-technical-design` → human approval → `task-breakdown` → `wise-coding` for large ones.
  Isolate every implementation in a git worktree, organize dependent PRs with `gh stack`, write
  commit messages and PR prose with `git-writing`, and keep each PR to exactly one thing. Use
  this whenever the user asks to implement, build, fix, or ship a change and the right process
  is not already chosen — especially "implement this feature", "fix this issue", "帮我实现 /
  开发这个需求 / 修这个 bug / 走开发流程".
---

# Coding Loop

Every implementation request deserves a right-sized process. A one-line bug fix routed through
a design review wastes days; a cross-service feature pushed straight into code produces a PR
nobody can review and a design nobody agreed to. This skill exists to make the sizing decision
*first*, explicitly, and then hand the work to the skill built for that size — so the loop is
always: classify → isolate → implement through the routed skill(s) → deliver one reviewable PR
per thing.

## Skills this loop routes to

| Skill | Source |
| --- | --- |
| `wise-coding`, `git-writing` | this repository ([git-hulk/skills](https://github.com/git-hulk/skills)) |
| `issue-fixes`, `task-breakdown`, `write-technical-design` | [AfterShip/skills](https://github.com/AfterShip/skills) |

Install the AfterShip skills alongside this one; the routes below assume all five are
available by name.

## Step 1: Classify the scenario

Before writing any code, scope the change enough to classify it: read the affected code, list
the files and layers it touches, and estimate the size of the diff. Do not guess from the
request's wording alone — "just add a field" can be a 500-line change once storage, service,
and API layers are counted, and a scary-sounding report can be a two-line fix.

| Scenario | Signal | Route |
| --- | --- | --- |
| **Bug fix** | Broken behavior with a correct behavior to restore: a panic, crash, hang, wrong result, regression, pasted stack trace, or issue link | `issue-fixes` |
| **Small feature** | New or changed behavior, estimated diff ≤ 200 lines | `wise-coding` |
| **Medium feature** | Scope is simple and agreed, but the diff exceeds 200 lines | `task-breakdown`, then `wise-coding` per task |
| **Large feature** | New system or component, cross-service change, schema/API/event contract changes, or scope that is not yet agreed | `write-technical-design` → human approval → `task-breakdown`, then `wise-coding` per task |

The 200-line threshold counts meaningful changed lines of code (generated files and lockfiles
excluded); it exists because that is roughly where a single PR stops being reviewable in one
sitting. When an estimate lands near the boundary, prefer the heavier route — splitting work
that turned out small is cheap, while un-splitting a monster PR is not.

If the request mixes scenarios — "fix this bug and also add that option" — split it now: each
piece gets its own classification, its own branch, and its own PR.

## Step 2: Isolate in a worktree

Run every implementation in its own git worktree so the main checkout, and any other work in
flight, stays untouched:

```bash
git worktree add ../<repo>-<topic> -b <branch-name>
```

One worktree per independent piece of work. If the session already runs inside a dedicated
worktree (Claude Code often sets one up), use it instead of nesting another. Remove the
worktree after its PR merges.

## Step 3: Run the route

### Bug fix

Follow `issue-fixes` end to end: reproduce from a minimal input, find the root cause, make the
smallest correct change, add a regression test that anchors the exact symptom, and ship one PR
with the Problem / Reproduction / Fix / Test structure. If the AfterShip `issue-fixes` skill is
not installed, fall back to the equivalent workflow bundled with `wise-coding`
([`skills/wise-coding/references/issue-fixes.md`](../wise-coding/references/issue-fixes.md)).
Resist widening the fix into a refactor — anything discovered along the way becomes its own
classified piece of work.

### Small feature

Follow `wise-coding` directly: read the repo, inherit its vocabulary, interview when a decision
is not answerable from the code, implement in dependency order, and keep the exported surface
minimal. One branch, one PR.

### Medium feature

The scope is understood, so no design document is needed — but the diff is too large for one
review. First run `task-breakdown` to split the work into ordered, independently reviewable
tasks. Then implement each task with `wise-coding`, in dependency order, one branch and one PR
per task.

When the tasks depend on each other, organize the PRs with `gh stack` so each PR's diff shows
only its own task (see the stacked-PR rules in the global instructions — branches must live in
the target repository, and shared-repo branch creation needs authorization *before* the first
PR). Independent tasks land as ordinary parallel PRs; do not stack what has no dependency.

### Large feature

Design before code, because here the expensive mistakes are decisions, not lines:

1. Write the design with `write-technical-design` (Summary / Motivation / Detailed Design /
   Drawbacks / Alternatives / Unresolved Questions).
2. **Stop and request human review of the design. Do not proceed until it is explicitly
   approved** — an unapproved design implemented quickly is still an unapproved design, and
   review feedback is cheapest before any code exists.
3. With the approved design, run `task-breakdown` to propose the change plan as ordered,
   reviewable tasks, and get the plan agreed.
4. Implement each task with `wise-coding`, one PR per task, stacked with `gh stack` when the
   tasks are dependent.
5. If implementation drifts from the design, update the design document rather than letting
   them diverge silently.

## Step 4: Deliver

For every commit and PR in every route, write the prose with `git-writing`: a subject of at
most 70 characters in imperative mood, a body wrapped at ~72 characters explaining what was
wrong or missing and why this change is the answer, and the PR title/summary taken from the
first commit's message. Follow the repository's own PR template when one exists.

## Principles

- **One thing per PR.** One bug, one task, one concern. Never fix two bugs in one PR, and never
  let a feature PR absorb a drive-by fix — a reviewer approving a PR is approving *a* decision,
  and a PR that bundles several forces them to approve all or none. Anything extra you find
  goes into its own classified, branched, and PR'd piece of work.
- **Re-classify when the estimate breaks.** If a "small" feature crosses ~200 lines mid-flight,
  stop and promote it to the medium route: break the remaining work down rather than pushing on
  to a PR too large to review. Likewise, a "bug fix" that reveals a missing capability becomes a
  feature and gets re-classified, not smuggled through the fix.
- **The route is the floor, not the ceiling.** Skipping a step because the schedule is tight is
  how unreviewable PRs and unapproved designs happen; the routes above are already the minimum
  process for each size.
