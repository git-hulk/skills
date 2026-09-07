# Report template

Save as `<repo-name>.md` in the current working directory unless told otherwise. Keep the heading
names so reports from different repos are comparable. Drop a section only when the track says to,
and leave a one-line note saying why (e.g. "No schema: the service is stateless, see `main.go:40`").

```markdown
# <repo name> — codebase tour

Repo: <remote URL> @ <short sha> (<date>) · Kind: <service | library | CLI | mixed> · Language: <lang>, ~<N>k lines
Docs read: <README, docs/, external URLs fetched>
Read depth: <everything | wiring + hot paths + fan-out over N packages | subsystem X only>

## 1. Critical concepts

| Concept | Meaning in this project | Defined at | Confusable with |
| --- | --- | --- | --- |

## 2. How the concepts relate

<mermaid flowchart>

<prose walk, outermost inward; surprises and doc/code disagreements>

## 3. Architecture            (service / CLI track)
<mermaid flowchart with subgraphs> — wiring at <file:line>
<one paragraph per process / layer>

## 4. Critical data flows     (service / CLI track)
### 4.1 <flow name>
<mermaid sequenceDiagram>
Breaks if skipped: <sentence>
### 4.2 …

## 5. Schema                  (service / CLI track)
<mermaid erDiagram, or key-layout table>
<analysis: aggregate root, hot writes, denormalisation, locking, indexes vs queries>

## 6. API map                 (service / CLI track)
| Method + path | Purpose | Handler | Entities read / written | Auth |
Key APIs: <request / response shape, error semantics, per key API>

## 3. Interface map           (library track)
<mermaid classDiagram>
| Symbol | Kind | Role | Implemented by | Defined at |
### Usage narrative
<minimal program, one comment per line>
### Internal flow
<sequenceDiagram / stateDiagram, or "pure functions, none">

## 7. Orthogonality
<scoring table>
Verdict · Non-orthogonal spots · Deliberate trade-offs

## 8. Guided interview
Resolved branches: <checklist>
Open questions (maintainers only): <list>
— or, when non-interactive —
Question tree with recommended answers: <list>

## Appendix: where to look next
<the 5–10 files a newcomer should read first, in order, with one line each>
```
