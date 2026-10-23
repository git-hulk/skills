---
name: pull-request-writing
description: >
  Write or revise pull request titles and summaries and Git commit messages from the actual
  change and its motivation. Use when the user asks for a PR title, PR
  description, PR summary, commit subject, commit message, or wants existing Git prose made
  clearer. Follow repository-specific templates and conventions when present; otherwise use a
  single message shared by the PR and commit: a subject of at most 70 characters and a body
  wrapped at about 72 characters. Do not use for release notes, changelogs, or general
  documentation.
---

# Pull Request Writing

Turn a change into reviewable prose. A reader should understand what was wrong or missing, why it
matters, and what changed without reconstructing the story from the
diff. Generate text only; do not create commits, push branches, or open or update pull requests
unless the user separately asks for those actions.

## Branch names

When suggesting a branch name or creating one as part of authorized Git operations, use
`<type>/<short-description>`:

- Bug fix: `fix/restore-node-id-on-reload`
- New feature: `feature/add-snapshot-uploads`
- Improvement: `improvement/reduce-snapshot-memory`

Use a concise, lowercase, hyphen-separated description of the actual change. Avoid vague names
such as `update` or `changes`. Do not include tool or agent names such as `codex` or `claude`
anywhere in the branch name, including prefixes like `codex/fix/...` or `claude/feature/...`.
Apply this convention to every branch in a stacked PR workflow.

## Fork branches for authorized Git operations

When the user authorizes branch creation, pushing, or PR publication:

- Create the working branch locally from the intended base, and create or push its remote
  branch only in the user's fork. Never create or push change branches in the upstream
  repository, even when the user has write access there.
- Verify the repository owner, fork relationship, and actual push URL before publishing.
  Do not assume `origin` is the fork or `upstream` is the source; remote names are not evidence.
- Explicitly select the verified fork as the push destination for both initial and subsequent
  pushes. Use the fork's owner and branch as the PR head, and the intended target repository
  and branch as its base; targeting upstream does not make upstream the push destination.
- Apply this rule to every branch in a stacked PR workflow, including `gh stack` submission.
  Check the tool's push destination before submitting; never fall back to publishing branches
  in upstream to work around a tooling limitation.
- If a usable user fork cannot be established, stop before remote branch creation or pushing
  and explain what is missing. Drafting text alone does not authorize these Git operations.

## Principles

- **Evidence before prose.** Read the relevant diff, status, recent history, issue or request,
  tests, and repository templates before writing. Do not invent motivation, impact, compatibility,
  test results, issue links, or implementation details.
- **One message for the PR and commit.** Draft one subject and body. Use the subject as the PR
  title and the exact body as the PR summary, including issue references. Do not
  expand, shorten, or rephrase one independently; apply revisions to both.
- **Keep verification internal.** Do not include checks performed, verification commands, or
  test results in commit messages or PR summaries. Use that evidence only to ground claims.
- **Lead with the outcome.** Titles and subjects name the primary observable change. Describe
  the solution or design in the body without implementation details.
- **Explain cause and effect.** Prefer current behavior → problem or root cause → change →
  resulting behavior. A list of edited files is not a summary.
- **Concrete evidence earns space.** Include a short before/after example, error, or
  scenario when it makes the failure and correction easier to verify.
- **Repository rules come first.** Follow an existing PR template, contribution guide, required
  sections, issue syntax, or commit prefix. Apply the defaults below only where the repository is
  silent.
- **Keep claims proportional.** Say "fixes" only when the evidence establishes the fix; otherwise
  use "addresses", "changes", or "is intended to" and limit claims to the available evidence.

## Gather the change story

Before drafting, determine:

1. The user-visible or maintainer-visible outcome.
2. The previous behavior and why it was insufficient.
3. The root cause, when known and relevant.
4. The solution or design and its observable effect, without implementation details.
5. Compatibility, migration, operational, or performance consequences.
6. The verification actually performed, for grounding claims internally only.
7. Related issue numbers or links supplied by the repository or user.

If the evidence cannot answer a material point, omit it or label it as an assumption. Do not ask
for information that the repository or diff can provide.

## Pull request title

- Aim for 70 characters or fewer unless the repository uses another limit.
- Use sentence case, an active verb, and no trailing period.
- State the outcome precisely: `Prevent duplicate jobs during leader failover` is stronger than
  `Update scheduler files`.
- Use a conventional-commit prefix or component tag only when the repository requires or regularly
  uses one.
- Do not include an issue number when the repository links issues in the summary instead.

## Pull request summary

Use the commit message body verbatim, excluding the subject and its separating blank line.
Preserve wording, paragraph order, headings, line wrapping, and trailers. When a
repository requires a PR template, apply its required sections to the shared body so the commit
and PR remain identical. Do not add empty sections or duplicate the subject in the summary.

Use this default structure for the shared body:

```text
<1-3 sentences describing the motivation, including concise background
context and why the change is needed; include the root cause for bug fixes.>

<Bug fixes only: explain how the bug happened, without a heading or prefix.>

<Describe the solution or design without implementation details.>

<Optional: other things reviewers need to know.>

Assistant-By <MODEL>
```

Start directly with the motivation, without a heading. Motivation and solution are mandatory,
including for commit-only requests. For bug fixes, explain the root cause and previous behavior
in the motivation paragraph. Immediately follow it with an unheaded paragraph explaining the
circumstances or sequence that led to the failure, then describe the corrected behavior in the
solution paragraph. Omit this explanation for other changes. If the root cause or how the bug
arose is not established, say so rather than inventing an explanation or introduction history.
Include issue references or other reviewer context only when material and supported by evidence;
omit the optional paragraph otherwise.

## Commit message

Use this format unless the repository has stricter requirements:

```text
Short summary of the change, 70 characters or fewer

1-3 sentences describing the motivation, including concise background
context and why the change is needed; include the root cause for bug fixes.

<Bug fixes only: explain how the bug happened, without a heading or prefix.>

Describe the solution or design without implementation details.

Optional: other things reviewers need to know.
```

Rules:

- The subject and body are mandatory. The body must include motivation and solution;
  other reviewer context is optional.
- Separate the subject and body with exactly one blank line.
- Write the subject in imperative mood when repository history does not establish another style.
- Do not end the subject with a period.
- Wrap ordinary body prose at about 72 characters. Do not break URLs, code, identifiers, or
  trailers.
- Separate paragraphs with blank lines. When using bullets, indent them consistently and separate
  them with blank lines when that matches the surrounding message style.
- Explain why and behavioral consequences in the body; do not repeat the subject or narrate the
  diff line by line.
- Put issue references, co-author lines, sign-offs, and other required trailers last, preserving
  their exact syntax.

## Output

Return only the artifacts requested. When the user asks for all three, use:

````markdown
## PR title

<shared subject>

## PR summary

<shared body>

## Commit message

```text
<shared subject>

<shared body>
```
````

Before returning, count the PR title and commit subject, check the commit body's wrapping, and
verify every factual claim against the available evidence. When both artifacts are requested,
check that the PR title equals the commit subject and the PR summary equals the commit body
exactly, excluding only the output wrappers.
