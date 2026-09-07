# Step 5: Wait 72 hours and ask the release manager

The release manager determines whether the vote passed. Do not inspect the
mailing-list thread, poll the archive, count ballots, or verify PMC membership.
The earlier voting rule (three binding PMC +1 votes and no veto) is for the
manager to assess; an independent agent verification is not required.

## Record the start and wait

1. Read the per-version JSON and run the checker. Require completed step 4 in its
   recorded mode and confirm entry to step 5. Preserve the opening `email` and
   its outcome in `vote.proposal_email_status`; save the new entry confirmation
   with `target_step: 5`, candidate tag, and prepared commit.
2. Use an already recorded actual vote start time, or ask the release manager
   when the opening vote email was sent, including timezone. Record `started_at`
   and its source in `start_record`. A manager-supplied timestamp is sufficient;
   no archive lookup is needed. A draft, handoff, or "sent" without a usable
   timestamp does not start the clock. Use `awaiting_vote_start` while missing.
3. Set `minimum_end_at = started_at + 259200 seconds` (72 hours). If a longer
   voting period was announced and recorded, honor `announced_end_at` as well.
   Keep these instants separate from the cherry-pick deadline and preserve them
   on resume. In dry-run, use a manager-supplied or explicitly authorized simulated
   start time and label the start and all answers simulated.
4. Before the deadline, retain `waiting_for_votes`, report the deadline/remaining
   wait, and stop. Do not ask for a final outcome early or proceed based on an
   early "passed" answer; preserve that message in history and ask after the
   deadline. Do not keep the task open for 72 hours. Authoring this procedure does
   not schedule a reminder; use the app's automation tool only if the manager
   actually asks for a later check or reminder.

## Ask whether the vote passed

At or after the deadline, use `awaiting_vote_outcome`. Show the version/candidate,
recorded start time, elapsed deadline, and mode, and state the proposed next step:
draft an unsent vote-result email. Ask the release manager whether the vote passed.

- **Yes:** record `outcome_confirmation.passed: true` with the manager, current
  time, mode/simulation marker, candidate, start, and effective deadline. Record
  `passed_at` as the time this post-deadline answer was recorded and use
  `vote_passed` or `dry_run_vote_passed`. The answer to this checkpoint also
  permits entry to the stated result-drafting step; do not ask a second vote-result
  confirmation. Continue with the separate sender checkpoint before composing.
- **No / not yet:** record `passed: false` and `vote_not_passed`. Keep the next
  step blocked. Preserve any explanation or instructions and wait for the
  manager's later update; do not infer failure, cancellation, or permission to
  restart a candidate from this answer alone.
- **Unclear / no answer:** keep the outcome null and `awaiting_vote_outcome`.
  Silence or elapsed time is not a positive answer.

Reuse the manager's unchanged answer on resume. A later correction, changed
candidate, start time, deadline, or execution mode invalidates that answer and
dependent result-draft approval. Preserve superseded answers and drafts in history
before clearing active passage/result claims. Do not delete or change a remote
draft automatically. Optional thread links, counts, or voter names supplied by
the manager are context, not mandatory inputs or prompts for external verification.

## Draft the result after confirmation

Use [the email procedure](vote-email.md) for sender confirmation, full inline
content review, Gmail draft support, external draft approval, uncertain outcomes,
and manual fallback. Store a separate `result_email`, with its own status and
step-5 entry confirmation based on the manager's positive answer. Do not overwrite
the opening email. Confirm the sender before writing the result subject/body.

After sender confirmation, adapt this minimal template:

```text
Subject: [RESULT][VOTE] Release Apache Kvrocks VERSION

Hello Apache Kvrocks PMC and Community,

The vote to release Apache Kvrocks VERSION, candidate CANDIDATE_TAG, has passed.
The vote opened at START_TIME_WITH_TIMEZONE and remained open for at least 72 hours.

Thank you to everyone who reviewed and tested the candidate.

CONFIRMED_SENDER_NAME_OR_ADDRESS
```

Add counts, voter names, resolutions, or a thread link only if supplied and
confirmed by the manager; omit missing details instead of inventing them or
requiring a tally. Do not claim to have checked the thread. Keep any optional
connector reply linkage in the reviewed payload; no thread lookup is required
to create a standalone draft.

Keep `drafting_vote_result` while reviewing the sender/content or reconciling an
uncertain draft write. After the approved unsent draft or manual handoff, use
`vote_result_prepared` or `dry_run_vote_result_prepared`. Dry-run writes stay local.
Stop after this handoff. Confirm entry before starting
[step 6 publication](publication.md); sending mail remains a separate action.

## JSON state and older records

Keep `vote` and `result_email` null before step 5. After entry approval, use:

```json
{
  "outcome_source": "release_manager",
  "proposal_email_status": "ACTUAL_STEP_4_OUTCOME",
  "entry_confirmation": {
    "by": "MANAGER",
    "at": "RFC3339",
    "mode": "dry-run",
    "simulated": true,
    "target_step": 5,
    "candidate_tag": "CANDIDATE_TAG",
    "prepared_commit": "FULL_SHA"
  },
  "started_at": null,
  "start_record": null,
  "minimum_end_at": null,
  "announced_end_at": null,
  "outcome_confirmation": null,
  "passed_at": null
}
```

`start_record` records `source` (`release_manager` or `prior_record`), `by`, `at`,
`mode`, `simulated`, and optional source details. A prior actual start timestamp
can be retained without reopening its archive source; never turn draft creation
time into a vote start. `outcome_confirmation` records `by`, `at`, `mode`,
`simulated`, `passed` (boolean), `candidate_tag`, `prepared_commit`, `started_at`,
and `deadline` (the effective deadline). Set `passed_at` only for a positive answer
after the deadline; it records manager confirmation, not independent verification.
Bind a result draft to `vote_snapshot_sha256(vote)` in
`result_email.vote_snapshot_sha256` so a changed answer invalidates it.

For an older automatic-review record, preserve its thread, ballots, reviews,
watch fields, and former passage/result approvals in history. Retain an existing
actual start/deadline using `start_record.source: prior_record`; do not reset the
clock. Switch `outcome_source` to `release_manager` and clear active automated
passage/result claims. After the deadline, ask the manager for the outcome;
automated tally evidence cannot stand in for their answer. Remove the obsolete
active `thread`, `review`, `result_confirmation`, and watch fields after preserving
them. Records before step 5 need no migration or new confirmations.

The checker reports `vote_evaluation` for the time/manager-answer gate and never
looks up votes or PMC members. Its exit code still describes the cherry-pick
time gate; inspect the saved status and vote gate before taking the next step.
