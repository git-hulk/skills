# The guided interview

A guided interview tests the user's model one question at a time, each with a recommended answer,
exploring the repository instead of asking when the code can answer. Here the plan is someone
else's finished design — the repository — and the interview reveals which parts of the model the
user only *thinks* they hold.

## Build the question tree first

Derive it from the report, before asking anything. Roots are the decisions that shaped the whole
system; branches are the decisions inside each component; leaves are single mechanisms.

| Level | Question shape | Example |
| --- | --- | --- |
| Root | Why this decomposition / storage / consistency model / API style at all? | "Why does the controller keep cluster topology in etcd rather than asking the kvrocks nodes?" |
| Branch | Why is this component separate, and what would merge it cost? | "Why is `Store` an interface with three backends when only etcd is documented?" |
| Leaf | What does this mechanism guarantee, and what would break without it? | "What happens to an in-flight slot migration if the controller leader dies?" |
| Judgement | Where would a specific change land? | "To add per-tenant rate limits, which layer changes and which must not?" |

Good questions have an answer the code supports and that a newcomer would likely get wrong.
Skip questions whose answer is a fact ("what port does it listen on") — look those up yourself.
Skip questions only maintainers can answer; those go straight to *Open questions*.

## Run it

One question per message. Each message contains, in this order:

1. The branch you are on ("Storage → consistency").
2. The question.
3. **Recommended answer** with citations — what you believe and why, in two or three sentences.
4. A prompt to agree, refine, or push back.

Then wait. The user's reply steers:

- **Agrees** → mark the node resolved, go to the next node in that branch, or the next branch.
- **Refines** → update the report section the node came from, then continue.
- **Contradicts the code** → show the code (`file:line`, a short excerpt), ask which reading they
  hold now. Do not move on while the model and the code disagree.
- **Asks a question back** → answer it from the code, then return to the same node.
- **"Quiz me"** → from then on hold the recommended answer until they have answered.

Keep a visible checklist of branches and tick them as they resolve so both of you can see how
much is left. Depth beats breadth: finishing one branch to its leaves teaches more than touching
every root once.

## End

Stop when every branch is resolved or the user stops. Write into the report's *Guided interview*
section the resolved checklist, anything the interview changed in earlier sections, and *Open
questions* for the maintainers. In a non-interactive run, write the whole tree with recommended
answers there instead and say the interactive session was skipped.
