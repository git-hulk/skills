# Skills

Reusable, repository-focused workflows for coding assistants. Each skill is self-contained and
combines a focused `SKILL.md` entry point with the references, scripts, and evaluations needed
for its workflow.

## Available skills

### [Coding Loop](skills/coding-loop/SKILL.md)

The entry point for implementation requests. Classifies the work first — bug fix, small feature
(≤ 200 changed lines), medium feature (simple scope but > 200 lines), or large feature — then
routes it through the right skills: `issue-fixes` for bugs, `wise-coding` for small features,
`task-breakdown` plus `wise-coding` for medium ones, and `write-technical-design` with human
approval before breakdown and implementation for large ones. `wise-coding` and `git-writing`
live in this repository; `issue-fixes`, `task-breakdown`, and `write-technical-design` come from
[AfterShip/skills](https://github.com/AfterShip/skills). Every implementation runs in an
isolated git worktree, dependent PRs are organized with `gh stack`, commit and PR prose comes
from `git-writing`, and each PR does exactly one thing.

### [Wise Code Review](skills/wise-code-review/SKILL.md)

Review diffs for actionable bugs and regressions using targeted searches, focused reads, and
verified findings. Uses Uber's Go Style Guide, Google's C++ Style Guide, and Roblox's Lua Style
Guide for language-standard compliance, with version-aware correctness and lifecycle checks.
Reviews are read-only unless changes are requested.

### [Fast Learning](skills/fast-learning/SKILL.md)

Build a defensible mental model of an unfamiliar repository before making changes. The workflow
covers:

- The project's critical vocabulary and how its concepts relate
- Architecture and important data flows
- Database schemas or key layouts for stateful services
- API maps for services and public interface maps for libraries
- Orthogonality analysis and a guided interview to test understanding

The generated report is saved as `<repo-name>.md` in the current working directory unless another
location is requested.

### [Git Writing](skills/git-writing/SKILL.md)

Write factual, reviewable pull request titles and summaries and Git commit messages. The workflow
derives the change story from repository evidence, explains cause and effect, follows local
templates, and keeps commit subjects and bodies within conventional length limits.

### [Wise Coding](skills/wise-coding/SKILL.md)

Implement changes as if they were written by the repository's maintainers. The workflow emphasizes:

- Reading the relevant layers and a sibling feature before implementation
- Reusing the repository's vocabulary, helpers, and conventions
- Designing orthogonal package or module boundaries before adding files
- Designing storage, service, and API layers in dependency order
- Keeping public contracts and exported surface area minimal
- Testing compatibility and critical behavior instead of implementation details

For bug fixes, Wise Coding follows its [Issue Fixes reference](skills/wise-coding/references/issue-fixes.md)
workflow: reproduce the failure, identify its cause, make the smallest fix, and verify a regression
test. When a PR is requested, it uses a Problem / Reproduction / Fix / Test summary.

## Using a skill

Copy or link the complete skill directory from `skills/` into the location supported by your coding assistant,
then invoke the skill by name or make a request that matches its description. Keep the directory
intact so relative links from `SKILL.md` continue to resolve.

Example requests:

```text
Use fast-learning to help me understand this repository.

Use git-writing to draft the PR title, summary, and commit message for this change.

Use wise-coding to add this feature while following the repository's existing design.
```

## Repository layout

```text
skills/<skill-name>/
├── SKILL.md       # Purpose, trigger description, principles, and workflow
├── evals/         # Example tasks used to evaluate the skill
├── references/    # Detailed guidance loaded when relevant
└── scripts/       # Optional deterministic helpers
```

Not every skill needs every optional directory.

## License

Licensed under the [Apache License 2.0](LICENSE).
