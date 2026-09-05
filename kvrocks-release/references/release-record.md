# Release JSON state and discussion template

Use one directory per version:

```text
~/.kvrocks/release-[version]/
  release-state.json    # Authoritative status, decisions, approvals, and history
  discussion-draft.md  # Discussion body only
```

Read and update `release-state.json` on every invocation. Do not embed state in
Markdown or infer status from the discussion draft. Validate
the version against `[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?`
after removing an optional leading `v`; never interpolate arbitrary input into
a path or shell command. Create the release directory only when starting a real
rehearsal or live workflow with a known version. Test fixtures belong in a
temporary folder.

Read the complete existing file before every update. Preserve history and notes;
write via a temporary file in the same directory and an atomic replacement. If
the file changed since it was read, reread and reconcile instead of overwriting.
Do not run concurrent writers for the same release. Do not advance an unfamiliar
schema, step, or status with this skill.

Write a single UTF-8 JSON object, without Markdown headings, comments, or code
fences. Keep its proposal fields consistent with `discussion-draft.md`. Replace
`VERSION` and the mode before saving this initial template as `release-state.json`.
The template's `dry-run` is an example, not a selection: first ask the manager
for both version and mode (`dry-run` or `release`). Keep this filename as the
single authoritative state; a reference to "state.json" does not create a second
status file.

```json
{
  "schema_version": 1,
  "repository": "apache/kvrocks",
  "version": "VERSION",
  "mode": "dry-run",
  "step": 1,
  "status": "awaiting_confirmation",
  "proposed_commit": null,
  "commit_source": null,
  "commit_resolved_at": null,
  "exclusions": null,
  "cherry_pick_deadline": null,
  "cherry_pick_deadline_rule": null,
  "approval": null,
  "discussion": {
    "category": "General",
    "title": "Release Proposal For Apache Kvrocks VERSION",
    "draft_file": "discussion-draft.md",
    "url": null,
    "created_at": null,
    "simulated_at": null
  },
  "discussion_review": null,
  "next_step_confirmation": null,
  "source_release": null,
  "docker": null,
  "candidate_verification": null,
  "email": null,
  "vote": null,
  "result_email": null,
  "publication": null,
  "website": null,
  "announcement": null,
  "external_operations": [],
  "history": [],
  "notes": [],
  "next_action": "Confirm release parameters and review the proposal with the release manager.",
  "updated_at": null
}
```

Field meanings:

- `mode`: `dry-run` or `live`; it describes the saved workflow, not permission
  for the current invocation to publish anything. The user-facing choice
  `release` maps to stored `live`. Ask version/mode at the beginning of each run,
  record the answer in history, and validate saved status before proceeding.
  Then display the saved step/name, status, pending action, mode, and blockers
  and ask whether the manager expects to continue from there. This confirmation
  is separate from mode selection and never approves a remote operation.
  Never infer a release-mode selection from an existing live record. Resolve
  mode mismatches without automatically changing prior evidence or approvals.
- `proposed_commit`: full 40-character hexadecimal SHA; null while unresolved.
  `commit_source`: `apache/kvrocks:unstable` or an explanation of the explicitly
  selected alternative. Record the actual UTC lookup time in `commit_resolved_at`.
- `exclusions`: null means not confirmed; `[]` means the manager explicitly
  confirmed none; otherwise an array of agreed exclusion descriptions.
- `cherry_pick_deadline`: null while unknown, otherwise an RFC 3339 timestamp
  with an explicit offset, preferably UTC, such as `2030-01-02T10:00:00Z`.
  Store the manager's original timezone wording in history when converting it.
- `cherry_pick_deadline_rule`: null for a fixed deadline. For an approved duration
  after creation, use `{"anchor": "discussion_created_at", "offset_seconds": 259200}`
  for three days (72 hours), or the duration the manager supplies. This is not a
  global default. Keep `cherry_pick_deadline` null until creation, then set it to
  `discussion.created_at + offset_seconds` in live mode or
  `discussion.simulated_at + offset_seconds` in dry-run, calculated in UTC.
  Persist the resulting absolute deadline before entering a waiting status.
  Never calculate it from the current time on resume. Older records missing the
  rule field use their existing absolute deadline unchanged.
- `approval`: null until the manager approves the complete proposal, otherwise
  `{"by": "manager identity as supplied", "at": "RFC 3339 instant", "mode": "dry-run"}`
  (or `live`). Use `release manager (current user)` if no name was supplied.
  Record what was approved in history. Never invent approval from silence.
- `discussion.url` and `created_at`: actual GitHub results only. For dry-run,
  keep both null and set `simulated_at` when creation is simulated.
- `discussion.draft_file`: `discussion-draft.md`, relative to the release
  directory. Store only the proposed discussion body there. Review changes to
  that body under the same confirmation rules as the JSON proposal fields.
- `discussion_review`: null until checked, otherwise record `checked_at`,
  `mode`, `source` (discussion URL or explicitly authorized sample), `simulated`
  (boolean), `result` (`no_unresolved_objections`, `unresolved_objections`, or
  `unverified`), and `summary` with links to relevant feedback and resolutions.
  Only a complete review after the deadline can establish no unresolved
  objections. Do not mark a missing or unread discussion as clear.
- `next_step_confirmation`: null until the manager confirms proceeding after
  seeing the objection review, otherwise record `by`, `at`, `mode`, `simulated`,
  `review_checked_at`, and `next_step` describing the exact approved transition.
  Set `target_step` to `2` when entering Create source releases and stage.
  This is separate from proposal creation `approval`. Invalidate it on new
  objections or material changes and preserve the old confirmation in history.
  Simulated reviews and confirmations cannot authorize a live next step.
- When refreshing unchanged discussion feedback, preserve the approved review's
  `checked_at` and record `last_verified_at`. New objections or material changes
  replace the review snapshot and invalidate its transition confirmation.
- `source_release`: null before step 2; then use the candidate/evidence object in
  [the source-release procedure](source-release.md). Its local artifact/log paths
  do not imply that anything has been uploaded.
- `docker`: null before step 3; then use the run, watch scope, entry confirmation,
  and image evidence in [the Docker readiness procedure](docker-readiness.md).
  Keep the original `next_step_confirmation` for step 2; record step-3 confirmation
  in `docker.entry_confirmation` so earlier approval evidence is not overwritten.
- `candidate_verification`: null before step 4a; then use the uploaded-byte
  manifest, approved reads, checklist evidence, blockers, and completion in
  [the verification procedure](verify-candidate.md). Add as null to older records
  without changing their saved step. Missing evidence at email or later requires
  reconciliation before continuing; never fabricate past successful checks.
- `email`: null through step 4a; then use the sender, content, entry confirmation,
  and Gmail draft/manual handoff evidence in [the email procedure](vote-email.md).
  Store subject and body in this JSON object. An optional plain-text export is
  message content only, never a second status record. Sender confirmation must
  precede composition; content approval and a saved draft never imply sending.
  Older records missing this field mean step 4 has not started; add it as null.
- `vote` and `result_email`: null before step 5. See [the voting procedure](voting.md)
  for the recorded vote start, separate 72-hour deadline, manager's outcome
  confirmation, and separate result draft. Preserve the opening `email`.
  The manager supplies missing start information and determines whether it passed;
  the skill does not inspect the thread, tally votes, or verify PMC membership.
  Add missing fields as null without advancing older records.
- `external_operations`: an array of the concrete operation previews, approvals,
  and outcomes described below. Older records without it start with an empty
  array; never invent historical approvals.
- `publication`: null before step 6; use [the publication procedure](publication.md)
  for entry approval, separate SVN/Docker plans and outcomes, and the manager's
  GitHub release-note handoff/confirmation. Add missing fields as null without
  advancing older records. Preserve step 5 in `publication.previous_status`.
- `website`: null before step 7; use [the website PR procedure](website-pr.md)
  for publication-bound entry approval, the separate website checkout, reviewed
  diff/links/PR payload, and push/PR outcomes. Preserve completed step 6 in
  `website.previous_status`. Add missing fields as null without advancing a record.
- `announcement`: null before step 8; use [the final announcement handoff](announcement.md)
  for the manager's manual send and terminal completion. Preserve the website
  outcome in `announcement.previous_status`. Add missing fields as null without
  advancing older records. The announcement handoff is not an email draft.
- Older records without `discussion_review` or `next_step_confirmation` mean
  **not reviewed / not confirmed**. Add missing fields as null on the next save
  while preserving existing state and history.
- `history`: append an object for each material decision with `at` (UTC time),
  `by` (actor when known), `mode`, and `details`. Preserve previous approvals
  when superseded. `notes`: an array of context strings. `next_action`: the
  pending action or blocker. These belong in JSON, not Markdown sections.
- For each loading checkpoint, append a history event with
  `checkpoint: "expected_step"`, `at`, `by`, `mode`, the displayed `snapshot`
  (`version`, `selected_mode`, `saved_mode`, `step`, `step_name`, `status`,
  `next_action`, `record_updated_at`, and blockers), and `expected` (null while
  awaiting an answer, then true or false only from the manager's explicit answer).
  Preserve the pending event and append the answered event with `question_at`
  pointing to its timestamp. Include the manager's correction in `details` when
  unexpected. Record unknown step/status as null for missing or invalid state;
  never overwrite an unreadable record merely to log the checkpoint. Resolve it
  first, then preserve the conversation's checkpoint history in the repaired JSON.
  An earlier run's answer does not replace the new loading checkpoint.
- All non-null timestamps include a timezone; set `updated_at` on every save.

Statuses and transitions:

| Status                     | Meaning / permitted next action                                                                                                                                                                                         |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `awaiting_confirmation`    | Inputs or complete proposal approval are missing; collect or review them. Also retain this status for an approved draft whose publication is blocked, explaining the blocker in `next_action`.                          |
| `dry_run_waiting`          | Approved proposal saved, simulated creation only; wait until the recorded deadline.                                                                                                                                     |
| `waiting_for_cherry_picks` | Real discussion created or verified and recorded; wait until the deadline.                                                                                                                                              |
| `publication_uncertain`    | A live creation attempt has an ambiguous result; inspect GitHub and reconcile before any retry or advancement.                                                                                                          |
| `deadline_elapsed`         | The waiting period ended. Review discussion objections, then obtain explicit manager confirmation of a defined next step. Keep step 1 until the transition is confirmed. Mode and discussion evidence remain unchanged. |

Step 2 uses these statuses with `step: 2`, retaining the step-1 evidence:

| Status                          | Meaning / permitted next action                                                                                                        |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `preparing_source_release`      | Prepare the confirmed candidate in an isolated checkout; persist each completed local action.                                          |
| `source_release_validated`      | Actual local artifact checks passed; prepare the exact tag-push preview.                                                               |
| `tag_push_uncertain`            | A tag push failed or its result is unclear; reconcile through approved remote reads before retrying.                                   |
| `source_release_staged`         | A live candidate passed validation and its remote tag was verified; stop for the next instruction.                                     |
| `dry_run_source_release_staged` | External-operation checkpoints were rehearsed without a real push; distinguish actual local validation from simulated checks and stop. |

Never enter step 2 with an unelapsed deadline, missing/unclear objection review,
or missing transition confirmation. In dry-run, review and confirmation evidence
for a simulated discussion must also be explicitly marked simulated.

Step 3 uses `step: 3` and retains completed source-staging evidence:

| Status                 | Meaning / permitted next action                                                                                                                             |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `waiting_for_docker`   | The matching workflow or image is not ready; continue reads within the approved watch window or save a pending action.                                      |
| `docker_blocked`       | Workflow failure, cancellation, required intervention, access failure, or conflicting image evidence requires review. Never rerun or publish automatically. |
| `docker_ready`         | The candidate workflow and all required jobs succeeded; the published registry digest and expected platforms were verified.                                 |
| `dry_run_docker_ready` | Authorized fixtures passed the readiness checks; no real image publication is implied.                                                                      |

Persist run ID and attempt, statuses, job outcomes, image reference/digest,
platforms, check/completion times, and polling approval in JSON. On a new attempt,
preserve prior evidence in history and clear the previous publication/image
observations and completion time before monitoring it. Expiration of a watch
window alone does not mean failure or readiness.

Step 4 retains numeric `step: 4` and completed Docker readiness evidence. It has
two explicit phases so earlier step numbers remain stable. Phase **4a: Verify
the uploaded release candidate** uses:

| Status                                | Meaning / permitted next action                                                                        |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `verifying_uploaded_candidate`        | Resume approved downloads and outstanding checklist checks; email remains null.                        |
| `candidate_verification_blocked`      | Resolve missing uploads, failed/incomplete checks, or evidence conflicts before email drafting.        |
| `uploaded_candidate_verified`         | All checks passed on the staged bytes in release mode; show evidence and confirm entry to 4b.          |
| `dry_run_uploaded_candidate_verified` | Authorized fixture checks passed; confirm the simulated transition without claiming real verification. |

Store this status inside `candidate_verification` too, retaining its completed
status after advancing. Its entry confirmation targets step 4 and phase
`verify_uploaded_candidate`. See [the verification procedure](verify-candidate.md)
for the manifest, approvals, signer, checklist, and invalidation rules.

Phase **4b: Draft the release vote email** requires completed 4a verification:

| Status                   | Meaning / permitted next action                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------ |
| `awaiting_email_sender`  | Confirm the exact From address before composing any subject or body.                                   |
| `awaiting_email_review`  | Show full headers and content for approval; resolve missing artifact evidence and other blockers.      |
| `email_draft_uncertain`  | A live Gmail draft request has an ambiguous outcome; reconcile before retrying.                        |
| `gmail_draft_created`    | Live connector returned a draft ID for the confirmed sender and approved message; mail remains unsent. |
| `manual_email_prepared`  | Live message is ready for the release manager to send manually; no send is implied.                    |
| `dry_run_email_prepared` | Local message and handoff were rehearsed; no Gmail draft was created and no real send is requested.    |

Entry confirmation belongs in `email.entry_confirmation`, targeting step 4 and
binding the candidate tag, prepared commit, and `verification_sha256` computed
with `publication_plan_sha256(candidate_verification)`. Keep subject/body/composed time
null before sender confirmation. See [the email procedure](vote-email.md) for
payload approval, artifact checks, connection state, and duplicate prevention.

Step 5 uses `step: 5` with completed opening-email evidence:

| Status                         | Meaning / permitted next action                                                               |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| `awaiting_vote_start`          | Ask the release manager for the vote's start time when none is recorded.                      |
| `waiting_for_votes`            | Wait until at least 72 hours after the recorded vote start.                                   |
| `awaiting_vote_outcome`        | The deadline elapsed; ask the manager whether the vote passed before entering the next step.  |
| `vote_not_passed`              | The manager answered no/not yet; wait for their later update without advancing.               |
| `vote_passed`                  | The manager confirmed passage after the deadline; proceed to the stated result-drafting step. |
| `dry_run_vote_passed`          | The manager confirmed simulated passage after the rehearsal deadline.                         |
| `drafting_vote_result`         | Confirm result sender/content and prepare an unsent draft; resolve any uncertain draft write. |
| `vote_result_prepared`         | Live result draft or manual handoff is complete; it remains unsent.                           |
| `dry_run_vote_result_prepared` | Result-email handoff rehearsed locally; no remote draft or real send requested.               |

`result_email.status` uses the email status vocabulary while the top-level status
tracks step 5. Passage requires a positive manager answer recorded at or after
the vote deadline. `vote.outcome_source` is `release_manager`; record the answer
in `vote.outcome_confirmation`, bound to the candidate, mode, start, and deadline.
No thread or tally evidence is required. Preserve superseded answers and dependent
result drafts in history before clearing their active claims. See [the voting
procedure](voting.md) for the schema and migration of old automated-review records.

Step 6 uses `step: 6`, preserving the manager-confirmed passed vote and result draft:

| Status                          | Meaning / permitted next action                                                                                               |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `preparing_publication`         | Entry confirmed; prepare the exact publication plans and approved verification reads.                                         |
| `publishing_release`            | Execute only individually approved live operations or simulate them in dry-run; save each outcome.                            |
| `publication_blocked`           | Resolve conflicting/missing artifacts, access, or other identified blockers without destructive retries.                      |
| `release_publication_uncertain` | Reconcile an ambiguous SVN/registry write through approved reads before retrying.                                             |
| `awaiting_github_release_notes` | SVN and both Docker tags are complete; the manager has been asked to publish GitHub notes or acknowledge the dry-run handoff. |
| `publication_complete`          | SVN/Docker results are verified and the manager reported the matching GitHub release URL, tag, and commit.                    |
| `dry_run_publication_complete`  | Publication and the manual handoff were rehearsed; no real publication is implied.                                            |

Record SVN and each Docker target independently so partial success survives
resumption. These statuses do not authorize later release steps. See
[publication](publication.md) for plan hashes, operation approvals, and results.

Step 7 uses `step: 7` after completed publication and GitHub release notes:

| Status                        | Meaning / permitted next action                                                                          |
| ----------------------------- | -------------------------------------------------------------------------------------------------------- |
| `preparing_website_pr`        | Entry confirmed; inspect the separate website repository and prepare the release-data change.            |
| `awaiting_website_pr_review`  | Show the full diff, validation, branch destinations, and PR title/body for concrete operation approval.  |
| `website_pr_blocked`          | Resolve missing or conflicting release links, failed checks, or unavailable repository access.           |
| `website_push_uncertain`      | Reconcile the website branch's remote SHA before retrying a push.                                        |
| `website_pr_uncertain`        | Search and inspect matching PRs under approved reads before repeating creation.                          |
| `website_pr_created`          | The matching live PR and branch were verified; stop for human review. No merge or deployment is implied. |
| `dry_run_website_pr_prepared` | Approved website patch, push, and PR creation were rehearsed locally; no real PR URL.                    |
| `website_already_updated`     | Approved verification found this release already correctly listed on the base branch; avoid an empty PR. |

See [the website PR procedure](website-pr.md) for the schema and payload hashes.
Record pushes and PR creation separately so a successful push is preserved if PR
creation needs reconciliation. A PR does not authorize merge, deploy, or announcement.

Step 8 is the final step and uses `step: 8` after completed website work:

| Status                           | Meaning / permitted next action                                                                             |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `preparing_announcement_handoff` | Final-step entry confirmed; prepare the concrete manual handoff.                                            |
| `awaiting_announcement_sent`     | The manager was asked to send the announcement, or acknowledge the dry-run handoff; wait for their answer.  |
| `release_complete`               | The manager confirmed sending this release's announcement; the process is done.                             |
| `dry_run_release_complete`       | The manager acknowledged the simulated final handoff; the rehearsal is done and no real sending is claimed. |

An announcement request or draft alone is not completion. Store the manager's
answer, mode, time, and handoff hash; an archive URL and exact send time are
optional. Set `announcement.completed_at` and `next_action: null` only at terminal
completion. On resumption, validate and report the completed mode without
repeating announcements or adding later steps.

Changes before discussion publication reset approval and status to `awaiting_confirmation`.
Log any previously simulated outcome and clear its active `simulated_at` when
revising a rehearsal. For a published discussion, preserve its URL and creation
time, reconcile the published content read-only, and ask for instructions before
making a material revision. Do not reset it into a new proposal automatically.
At `now >= cherry_pick_deadline`, a waiting record may become `deadline_elapsed`;
never use that status to bypass missing approval or discussion evidence.
Keep `deadline_elapsed` while reviewing objections or awaiting transition
confirmation, and describe the blocker in `next_action`. Log the review and the
manager's decision in `history`. An elapsed deadline alone never permits advancement.

## External-operation records

Append a concrete record before requesting approval, using a unique `id`:

```json
{
  "id": "OPERATION_ID",
  "step": 2,
  "mode": "dry-run",
  "kind": "write",
  "action": "ACTION_DESCRIPTION",
  "target": "EXACT_REMOTE_URL_AND_RESOURCE",
  "request": {},
  "inputs": {},
  "effects": [],
  "resource_check": null,
  "approval": null,
  "status": "prepared",
  "result": null
}
```

Replace every placeholder before confirmation. `request` contains the exact
command argument array and working directory or API method/arguments/body.
`inputs` includes the selected refs, immutable commit/tag IDs, and artifact hashes
where relevant. `effects` includes triggered CI and registry publication, not
only the immediate Git or API effect. For discussion creation, display its full
title and body inline as well as recording them here.

Before any new creation, populate `resource_check` on the operation (or in its
owning step object for local resources). Include `target`, identifying `inputs`,
`checked_at`, `mode`, `simulated`, `source`, `read_operation_ids`, `result`
(`absent`, `matching`, `conflicting`, or `unverified`), `resource_ids`, and a
`summary` of compared identity/content. A matching result calls for verified reuse;
only verified absence permits proposing creation. Conflicting/unverified results
block creation. Remote checks require approved reads, and simulated checks never
establish live absence. Prior step-specific evidence can supply this check without
duplicating a read when its scope is unchanged and it is still current.
Older completed operations need no fabricated historical checks; inspect their
actual resources on resume before any further creation or retry.

After confirmation, set `approval` to `{by, at, mode}` with actual values and
`status` to `approved`. Record actual outcomes as `succeeded`, `failed`, or
`uncertain`; confirmed dry-run writes become `simulated` with actual remote
results left null. A remote read may actually succeed in dry-run when its scope
was explicitly approved. Keep prior records immutable after an outcome; create
a new preview and approval when scope changes. Reconcile uncertain outcomes
before retrying. Persist every material update in `history` too.

An operation record or step-level confirmation alone never grants permission:
the manager must have confirmed the exact preview in the conversation. Carry
valid unchanged approvals across resumptions without asking twice.

## Legacy Markdown records

If `~/.kvrocks/release-[version].md` exists and the JSON state does not, read the
entire legacy file and migrate it locally before resuming. Extract the existing
state object into `release-[version]/release-state.json`, preserve all fields,
and copy the discussion body into `discussion-draft.md`. Convert the old history,
notes, and next action into their JSON fields, preserving original text and using
null for unknown historical timestamps or actors. Add missing optional fields
without inventing approvals or resetting status or deadlines.

Run the checker on the new JSON state and verify the draft and history were
preserved. Exit `1` is a valid blocked record; exit `2` requires fixing migration
before continuing. Keep the legacy file as an archive; after migration, only the
JSON file is authoritative and receives status updates. If both formats already
exist, read the JSON state first and reconcile any conflicting information rather
than overwrite it from the legacy file. The checker accepts plain JSON only.

## Discussion template

Adapt this template using confirmed inputs. Omit unsupported claims about elapsed
time since the last release or specific features. The example is in the General
category: [Apache Kvrocks discussion #3520](https://github.com/apache/kvrocks/discussions/3520).

Store the title `Release Proposal For Apache Kvrocks VERSION` in
`discussion.title`. Save the following body in `discussion-draft.md`:

```markdown
Hello everyone,

I'd like to propose Apache Kvrocks VERSION for our next release.

The proposed cutoff on the unstable branch is
[FULL_SHA](https://github.com/apache/kvrocks/commit/FULL_SHA).
Commits through this point are proposed for inclusion, subject to the exclusions below.

Exclusions: CONFIRMED_NONE_OR_LIST_WITH_SCOPE.

Please suggest any additional commits to cherry-pick before DEADLINE_WITH_TIMEZONE.
The cherry-pick window closes at that time; later commits will not be accepted
for this release.

Feedback on this proposal is welcome.
Release process: https://kvrocks.apache.org/community/create-a-release

cc @apache/kvrocks-committers
```

If an alternative cutoff is selected, adjust the branch wording to match verified
facts. Show the team mention as part of the reviewed body; it is plain text in
dry-run and can notify people only when the approved live discussion is posted.
Use the same precise deadline in the draft and state, expressed in UTC if useful.
For an approved creation-relative rule, replace the deadline sentence with the
exact duration, for example: "Please suggest any additional commits to cherry-pick
within three days (72 hours) after this discussion is created." Keep this wording
in the approved body and record the derived absolute deadline in JSON after
creation; do not predict a creation timestamp or silently edit the approved body.

## Checking the record

From the skill directory, run:

```bash
python3 scripts/check_state.py ~/.kvrocks/release-VERSION/release-state.json
```

This helper only reads the record and the current clock; it never writes files,
contacts GitHub, or authorizes a later step. Exit codes: `0` means the time gate
elapsed, `1` means waiting or unresolved input, and `2` means missing or invalid
state. Exit `0` does not check community feedback or authorize a transition:
the agent must actually complete the objection review and manager confirmation
checkpoint. For step-2 records the helper also checks the saved transition
evidence. For step 3 it checks source-staging/entry evidence and consistency of
recorded readiness results. Exit `0` still means the deadline gate elapsed, not
that Docker is ready. For step 4a it validates recorded verification entry,
uploaded/prepared hash agreement, signer identity, all seven check results, and
the download approval scope. For step 4b and later it requires that evidence and
its hash binding to the email. It also checks sender-before-content
ordering, content approval, and consistency of saved draft/handoff evidence.
It cannot prove that a remote verification or human approval actually happened.
For step 5, inspect `vote_evaluation`: it validates the independent vote clock and
the manager's post-deadline answer. It never determines the outcome by tallying
votes. Exit `0` still does not imply that the vote has passed.
The helper never queries GHA, the registry, or Gmail and does not
approve external operations; the agent must perform the confirmed checks.
For step 6 it also checks the prior vote/result gate, publication entry, plan and
operation bindings, saved SVN/Docker outcomes, and manual GitHub confirmation.
It cannot prove remote publication from JSON alone. Exit `0` still indicates
only that the cherry-pick time gate elapsed, not permission to publish.
For step 7 it also checks prior publication completion, website entry approval,
the reviewed final-release links and PR payload, and saved push/PR outcomes.
It does not contact GitHub, perform website checks, or create/merge a PR.
For step 8 it validates prior website completion, the final handoff, and the
manager's send report or simulation acknowledgment. It never reads or sends
email. The terminal statuses mean this requested process is finished; inspect
the status and reason rather than treating the exit code as an instruction to act.
Inspect the JSON result and its reason; do not retry a blocked check as if it were
a transient tool error. The helper returns the complete stored state.

Run its isolated regression tests with
`python3 -m unittest discover -s scripts -p 'test_*.py'` when changing the helper.
