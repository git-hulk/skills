# Skills

Reusable, repository-focused workflows for coding assistants. Each skill is self-contained and
combines a focused `SKILL.md` entry point with the references, scripts, and evaluations needed
for its workflow.

## Available skills

### [Fast Learning](fast-learning/SKILL.md)

Build a defensible mental model of an unfamiliar repository before making changes. The workflow
covers:

- The project's critical vocabulary and how its concepts relate
- Architecture and important data flows
- Database schemas or key layouts for stateful services
- API maps for services and public interface maps for libraries
- Orthogonality analysis and a guided interview to test understanding

The generated report is saved as `<repo-name>.md` in the current working directory unless another
location is requested.

### [Git Writing](git-writing/SKILL.md)

Write factual, reviewable pull request titles and summaries and Git commit messages. The workflow
derives the change story from repository evidence, explains cause and effect, follows local
templates, and keeps commit subjects and bodies within conventional length limits.

### [Wise Coding](wise-coding/SKILL.md)

Implement changes as if they were written by the repository's maintainers. The workflow emphasizes:

- Reading the relevant layers and a sibling feature before implementation
- Reusing the repository's vocabulary, helpers, and conventions
- Designing orthogonal package or module boundaries before adding files
- Designing storage, service, and API layers in dependency order
- Keeping public contracts and exported surface area minimal
- Testing compatibility and critical behavior instead of implementation details

## Using a skill

Copy or link the complete skill directory into the location supported by your coding assistant,
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
<skill-name>/
├── SKILL.md       # Purpose, trigger description, principles, and workflow
├── evals/         # Example tasks used to evaluate the skill
├── references/    # Detailed guidance loaded when relevant
└── scripts/       # Optional deterministic helpers
```

Not every skill needs every optional directory.

## License

Licensed under the [Apache License 2.0](LICENSE).
