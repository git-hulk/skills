# The grill session

The `grill-me` skill interviews the user about a plan one question at a time, each with a
recommended answer, exploring the codebase instead of asking whenever the code can answer. Here
the plan is *your* implementation design and the user is the one with the missing facts:
product intent, naming taste, compatibility policy, what to do with existing data. The interview
exists so that those facts are decided by the person who owns them, before the code exists.

## When to grill

Run it when step 2's confidence check leaves a question the code cannot settle. Do not run it for
things you can look up (where the router is, what the error type is called). Do not run it when
every answer is already clear from the request plus the sibling — an unnecessary interview is
as annoying as a wrong guess.

Check the working decision record and prior user instructions first. A new turn or "continue"
does not reopen settled choices. If new evidence creates a real conflict, explain it and ask
only about the affected decision. An approved design can differ from existing code because
changing that behavior is the task.

## Build the question tree first

Roots are decisions that change the shape of the whole change; branches are per-layer choices;
leaves are single behaviors. Derive them from your draft design, not from a generic checklist.

| Level | Question shape | Example |
| --- | --- | --- |
| Root | Is this a new concept or a state of an existing one? | "Is a muted feed a new status alongside `disabled`, or a separate `mute_until` timestamp that leaves status alone?" |
| Branch | Which existing mechanism carries it? | "Should the API expose this on the existing feed update endpoint, or as a dedicated action like `/feeds/{id}/mute`?" |
| Leaf | What happens at the edge? | "When `mute_until` is in the past, should the API reject it or treat it as unmute?" |
| Compatibility | Who could break? | "Do old clients that omit `mute_until` on PUT clear the mute or leave it untouched?" |

Good questions have two or more defensible answers *and* the code would look different under
each. Skip questions whose answer would not change a line.

## Run it

One question per message, containing in this order:

1. The branch you are on ("Storage → representation").
2. The question.
3. **Recommended answer** — what you would do and the evidence (sibling code, `file:line`,
   guideline) behind it, two or three sentences. Prefer the answer that adds the least surface
   and changes no existing behavior.
4. A prompt to agree, refine, or choose otherwise.

Then wait. The user's reply steers:

- **Agrees** → resolve the node, update the design block in the reply, move on.
- **Refines** → update the design, re-check dependent nodes (a storage change can invalidate an
  API answer), continue.
- **Conflicts with an established constraint** → show the constraint and consequence. Ask only
  if the user's instructions do not already resolve the tradeoff; a difference from the sibling
  alone is not a reason to ask again.
- **Asks a question back** → answer from the code, return to the same node.
- **"Just do it"** → proceed within the authorized scope using reasonable implementation
  choices and state material assumptions. This does not grant permission for unrelated actions.
- **"Continue"** → resume the next unfinished step using settled decisions and authorization;
  do not restart the interview or treat it as approval for unrelated scope.

Track unresolved branches and share those that affect progress. Resolve roots before leaves;
a root reversal throws away leaf answers.

## When nobody can answer

In batch runs or delegated work without a user to answer, preserve agreed decisions and choose
the most conservative implementation within scope. Report only material assumptions and their
effect; do not turn a missing reply into authorization for an action that requires approval.
