---
name: git-writing
description: >
  Write or revise pull request titles and summaries and Git commit messages from the actual
  change, its motivation, and its verification. Use when the user asks for a PR title, PR
  description, PR summary, commit subject, commit message, or wants existing Git prose made
  clearer. Follow repository-specific templates and conventions when present; otherwise use a
  single message shared by the PR and commit: a subject of at most 70 characters and a body
  wrapped at about 72 characters. Do not use for release notes, changelogs, or general
  documentation.
---

# Git Writing

Turn a change into reviewable prose. A reader should understand what was wrong or missing, why it
matters, what changed, and how the result was verified without reconstructing the story from the
diff. Generate text only; do not create commits, push branches, or open or update pull requests
unless the user separately asks for those actions.

## Principles

- **Evidence before prose.** Read the relevant diff, status, recent history, issue or request,
  tests, and repository templates before writing. Do not invent motivation, impact, compatibility,
  test results, issue links, or implementation details.
- **One message for the PR and commit.** Draft one subject and body. Use the subject as the PR
  title and the exact body as the PR summary, including verification and issue references. Do not
  expand, shorten, or rephrase one independently; apply revisions to both.
- **Lead with the outcome.** Titles and subjects name the primary observable change. Put supporting
  implementation details in the body rather than joining several changes into the first line.
- **Explain cause and effect.** Prefer current behavior → problem or root cause → change →
  resulting behavior. A list of edited files is not a summary.
- **Concrete evidence earns space.** Include a short before/after example, command output, error, or
  scenario when it makes the failure and correction easier to verify.
- **Repository rules come first.** Follow an existing PR template, contribution guide, required
  sections, issue syntax, or commit prefix. Apply the defaults below only where the repository is
  silent.
- **Keep claims proportional.** Say "fixes" only when the evidence establishes the fix; otherwise
  use "addresses", "changes", or "is intended to" and name what was actually verified.

## Gather the change story

Before drafting, determine:

1. The user-visible or maintainer-visible outcome.
2. The previous behavior and why it was insufficient.
3. The root cause, when known and relevant.
4. The smallest accurate description of the implementation.
5. Compatibility, migration, operational, or performance consequences.
6. The verification actually performed.
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
Preserve wording, paragraph order, headings, line wrapping, verification, and trailers. When a
repository requires a PR template, apply its required sections to the shared body so the commit
and PR remain identical. Do not add empty sections or duplicate the subject in the summary.

Use this default structure for the shared body:

```text
<Concise summary in commit-message style: explain what changed and why.
Wrap prose at about 72 characters, separating paragraphs with blank lines.>

Before applying this PR:

<Describe the current behavior and the conditions that trigger the bug.>

After this PR:

<Describe the corrected behavior under the same conditions.>

Other important things to notice:

<Include relevant verification, compatibility or migration consequences,
operational caveats, and issue references.>
```

Start directly with the summary, without a heading. Include `Before applying this PR:` and
`After this PR:` only for bug fixes; omit both for other changes. Use concrete examples or short
code blocks when they clarify the behavior. Keep other important reviewer context in the final
`Other important things to notice:` section; omit it when there is nothing material to add.
If both artifacts are requested, write a concise shared body; a commit-only request may still
use a subject alone.

## Commit message

Use this format unless the repository has stricter requirements:

```text
Short summary of the change, 70 characters or fewer

More detailed explanatory text when necessary, wrapped at about 72
characters. Explain the reason for the change and any behavior that is
not obvious from the subject.

Further paragraphs follow after blank lines.

  - Bullets are acceptable when they make distinct points clearer.

  - Keep the indentation and spacing consistent.
```

Rules:

- The subject is mandatory; the body is optional.
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
