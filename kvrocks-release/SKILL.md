---
name: kvrocks-release
description: Prepare and resume Apache Kvrocks releases with per-version JSON state and human confirmation. Covers proposals, source candidates, Docker readiness, vote and result drafts, publication, the website PR, and the final announcement. Asks for version and mode, reports and confirms the saved step before continuing, and checks resources before creation.
---

# Kvrocks Release

Implement one release step at a time as the release manager supplies it. Defined
steps are (1) the release-proposal discussion, (2) Create source releases and
stage, (3) Build and push Docker images, which monitors the existing tag-triggered
workflow and verifies image readiness, (4) Draft the release vote email, and
(5) Wait for voting and draft the vote result, (6) Publish SVN artifacts and
Docker images, then ask the manager to publish GitHub release notes, and
(7) Create a PR to update website release links, and (8) Ask the release manager
to send the announcement, then finish the process.
Adding instructions does not enter or approve a step for an active release.
Initial SVN artifact uploads, automatic mail sending, and old-release cleanup
remain outside the defined steps. The manager sends the final announcement.

## Required opening question

At the start of every release execution or resumption, ask the release manager
one explicit question: **"Which release version and mode (`dry-run` or `release`)
should I use?"** Wait for their answer before starting release work. If values
were supplied in the initiating request, show them in this opening question for
confirmation. Do not silently choose a mode or reuse a version/mode from an older
run. One answer covers the current run and its follow-up checkpoints; do not ask
again at every tool call or step. Editing or testing the skill itself does not
start a release run and does not require this opening question.

Validate the supplied version and record the answer in that version's JSON
history after reading its existing state. If either answer is missing or unclear,
keep the question pending. The only user-facing choices are **dry-run** and
**release**. For compatibility, the existing JSON schema and procedures call
release mode `live`; map the explicit `release` selection to that stored value.
This mapping never converts saved simulated evidence into actual release evidence.

## Execution mode

- There is **no implicit mode**. Use the answer to the required opening question.
  Read-only GitHub and
  Git queries require the external-operation confirmation below. Local reads and
  draft/status writes are allowed. Do not create or edit a discussion, push a
  branch/tag, create a Gmail draft, send notifications, or mutate remote resources
  in dry-run. A remote email draft is an external write even though it is unsent.
- Keep the release-manager checkpoints in dry-run. Approval of a rehearsal does
  not authorize posting to GitHub. Report simulated creation explicitly and keep
  its discussion URL and creation timestamp null.
- Use release mode (stored as `live`) only after the manager selects it in the
  opening checkpoint. A live record alone is not authorization. Before publishing,
  obtain approval of the concrete proposal in live mode. Reuse that approval if
  already given for the unchanged proposal; do not ask twice.

## Confirm external operations

Before any operation against an external resource, show the exact action,
destination, command/API request or content, inputs, execution mode, and expected
effects, then obtain release-manager confirmation. This includes remote reads
and fetches, GitHub operations, Git pushes, downloads, keyservers, SVN, and
operations that trigger CI or registry publication. An explicit request to read
a specific URL authorizes that read; it does not authorize further operations on
other resources. Local inspection and skill authoring need no extra checkpoint.

Complete local preparation first so the manager reviews a concrete action. Save
the preview and approval in `external_operations` as described in the record
reference. A step-transition confirmation does not approve every external action
inside that step. A clearly enumerated group of reads and outcome-verification
requests may share one confirmation. Reuse approval only for the unchanged scope;
changes to targets, refs, payloads, artifacts, or effects require a new preview.

In dry-run, confirmed external writes are simulated and recorded as such. Never
use the underlying write command, even with its own `--dry-run` flag if it contacts
the remote without approval. Inspect helpers for implicit operations before
running them. If a write outcome is uncertain, record it and reconcile through
approved reads before retrying; do not blindly repeat a possibly completed write.

## Check resources before every creation

Before creating any resource in any step, inspect both the saved JSON outcome
and the actual target. This applies to first attempts as well as retries, even
when the JSON has no resource ID or says the action is pending. Complete remote
checks under the separately confirmed read scope before executing the write.
Local existence checks need no external-operation approval.

- Matching resource: verify its identity and contents, reconcile the saved state,
  and reuse it. Do not create a duplicate or overwrite human changes.
- Absent resource: record verified absence, then obtain the concrete creation
  approval. Mode selection and an existence check do not authorize creation.
- Conflicting resource: show the difference and stop that operation for resolution.
- Unavailable, incomplete, or ambiguous check: record `unverified` and stop before
  creation. A lookup failure is not evidence of absence.

For an intentional update such as moving `latest`, inspect the existing resource
against the approved before-state and confirm the exact change under that step's
procedure. Existing-resource checks never authorize silently overwriting an
immutable version tag, voted artifact, or human-edited draft.

Record the target, identifying inputs, check time, evidence/read operation IDs,
result, and discovered resource IDs in JSON using `resource_check` on the planned
operation or the owning step's state. Recheck on resumption, after an uncertain
write, or when the target or evidence changes; a past absence cannot justify a
new attempt. Preserve previous observations in history.

| Step/resource                                                       | Required check before creation                                                                                                                                            |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Proposal discussion                                                 | Search matching version discussions and inspect any candidate's repository, category, title, and body.                                                                    |
| Source checkout, release branch, candidate tag, archives/signatures | Inspect local paths, Git refs/commits, artifact hashes, and approved remote branch/tag reads before packaging or pushing. Resume matching work instead of overwriting it. |
| Docker workflow and image                                           | Inspect the existing tag-triggered run and image; step 3 never creates or reruns them. Before step-6 promotion, inspect the source digest and both destination tags.      |
| Vote/result Gmail draft                                             | Search/read matching drafts in the confirmed account before the first draft creation too; compare sender, recipients, subject, body, and candidate. Preserve human edits. |
| SVN release directory and GitHub release                            | Check source/destination contents and final tag/release identity; reuse a match. GitHub publication remains the manager's manual action.                                  |
| Website fork, branch, release entry, PR                             | Inspect existing fork/refs, release data, and matching PRs before creating or pushing anything.                                                                           |
| Vote and announcement handoffs                                      | Read saved answers and completion first; do not repeat completed handoffs. Do not reintroduce vote-thread/PMC checks or automatic email sending.                          |

Dry-run rehearses the same decision using approved reads or explicitly authorized
simulated evidence. Label simulations and leave real creation results null.

## Resume before acting

1. Read [the record format](references/release-record.md). Discover existing
   `~/.kvrocks/release-*/release-state.json` files before preparing a proposal.
   Use only the version confirmed in the opening question. Read its JSON state
   in full and its separate `discussion-draft.md` if present. The authoritative
   state file remains `~/.kvrocks/release-VERSION/release-state.json`; do not create
   a second `state.json` with competing status.
   If only a legacy Markdown record exists, migrate it as described in the
   reference before continuing; never maintain status in Markdown.
2. For an existing record, run the read-only helper from this skill directory:

   ```bash
   python3 scripts/check_state.py ~/.kvrocks/release-VERSION/release-state.json
   ```

   Before continuing, follow the **expected-step checkpoint** below. Report the
   saved mode, status, cutoff commit, and deadline. Preserve the draft,
   decisions, and history. Missing, malformed, or incompatible state must be
   resolved before advancing; do not silently reset it or create a duplicate.
   **In release mode, this state check is mandatory before any release action.**
   Confirm the saved step, pending action, approvals, deadlines, and external
   outcomes; continue from that status rather than restarting at step 1. Resolve
   a requested/saved mode mismatch before proceeding. A dry-run record cannot
   authorize release-mode work; preserve its history and use the existing explicit
   mode-transition procedure. A dry-run inspection of live state remains read-only.
   If no JSON exists, report that there is no saved status, check for legacy state
   locally and confirm this uninitialized status at the expected-step checkpoint.
   Then check existing release resources under approved reads and reconcile any found
   work before initializing a genuinely new step-1 record. Never assume a missing
   local file means the release resources do not exist.
   For saved step-2 state, resume via [the source-release procedure](references/source-release.md).
   For step 3, use [the Docker readiness procedure](references/docker-readiness.md).
   For step 4, use [the email drafting procedure](references/vote-email.md).
   For step 5, use [the voting procedure](references/voting.md).
   For step 6, use [the publication procedure](references/publication.md).
   For step 7, use [the website PR procedure](references/website-pr.md).
   For step 8, use [the final announcement handoff](references/announcement.md).
   If the validated status is `release_complete` or `dry_run_release_complete`,
   report the recorded completion and end this invocation. Do not repeat the
   announcement handoff, reopen earlier steps, or start additional release work.
   Preserve the saved step/status; do not apply the step-1 transitions below.

3. A recorded discussion URL means resume that discussion. Inspect it read-only
   and reconcile material differences with the manager. If a previous publication
   outcome is uncertain, inspect GitHub before any retry. Never recreate a
   discussion simply because the previous task was interrupted.
4. If waiting and the deadline has not arrived, save any relevant status updates,
   report the exact deadline and remaining wait, then end this invocation. Do
   not start the next step, sleep until the deadline, or schedule work unasked.
5. For a step-1 waiting record whose deadline has elapsed, record
   `deadline_elapsed`. This only clears the
   time gate: follow the discussion review and transition checkpoint below before
   entering the next step. A dry-run record remains a rehearsal after its deadline
   and cannot serve as evidence that a real community cherry-pick period occurred.

## Expected-step checkpoint on loading

After the opening version/mode answer, read the selected version's local state
and run its checker. **Tell the release manager where the workflow currently
stands and ask whether that is expected before continuing.** This applies to
both dry-run and release mode on each new execution/resumption. A version/mode
answer alone does not confirm the saved step.

Show the version, selected and saved mode if different, state-file path, saved
step number and name, exact status, pending action, and any unmet deadline,
approval, or known blocker. For step 1, include the saved discussion title and
full body inline, consistent with the proposal confirmation rule. If the record
is missing, say "No saved step; initialization is pending"; if invalid, say the
step is unverified and show the validation error. Do not invent a current step.

Ask: **"The saved release is at step N — STEP_NAME, with status STATUS. Is this
the expected step to continue from?"** Substitute the actual values, or adapt
the question to a missing/invalid record. Wait for an explicit answer before
release preparation, external lookups, resource creation, or step advancement.
Local state inspection and recording the checkpoint are allowed while waiting.

Record the displayed snapshot and manager's answer in JSON history as described
in the record reference. If it is unexpected, ask what the manager expected and
reconcile the state and resource evidence under the existing read-approval rules.
Do not reset, rewind, or skip steps merely to match an expected position. Missing
or invalid records still need reconciliation; a positive answer cannot validate
bad evidence, bypass a deadline, approve a transition, or authorize external writes.

Reuse this checkpoint answer within the current run while the displayed state
is unchanged. If reconciliation changes the step or status, show the correction
and confirm it before proceeding. Earlier proposal, transition, and operation
approvals remain intact when their scope is unchanged. For a terminal record,
report step 8 and the recorded completion, confirm that this is expected, and
stop; confirmation does not restart the completed process. Skill authoring or
isolated tests do not invoke this live workflow checkpoint.

## Step 1: prepare the discussion

Follow the shape of [discussion #3520](https://github.com/apache/kvrocks/discussions/3520):
a proposal in **General** with a version, commit cutoff, exclusions, and an exact
cherry-pick deadline. Do not inherit its version, commit, excluded feature, or
dates. Use the template in [the record reference](references/release-record.md).

1. After confirming the remote lookup under the external-operation rule, resolve
   the default proposed release commit from the current **upstream**
   `apache/kvrocks` `unstable` branch, using a read-only GitHub API or:

   ```bash
   git ls-remote https://github.com/apache/kvrocks.git refs/heads/unstable
   ```

   Record the full SHA and UTC lookup time. Do not use a possibly stale local
   branch, a fork, or `HEAD` as the default. If lookup fails, report the failure
   and ask for a verifiable commit; never manufacture a current default. Resolve
   a manager-specified alternative to a full commit SHA in `apache/kvrocks`.

2. Prepare as much of the local proposal as available information allows. Display
   the discussion title and full body inline in the same message that requests
   confirmation, including during dry-run and initial input collection. Mark
   missing values clearly, such as `[VERSION REQUIRED]`, `[EXCLUSIONS REQUIRED]`,
   and `[DEADLINE WITH TIMEZONE REQUIRED]`. Keep approval null while required
   inputs are missing. Ask the release manager to confirm these together,
   showing the resolved SHA in the discussion preview:
   - Release version, without a leading `v` in the release directory name.
   - Anything to exclude: record an explicit list or explicit **none**. Silence
     does not mean none. Keep any agreed scope details for exclusions.
   - Proposed release commit ID, defaulting to the upstream SHA just resolved.
   - Cherry-pick deadline: either a date/time with timezone or an explicit
     duration after discussion creation. No default duration has been specified;
     ask rather than assume one from the example. For a creation-relative rule,
     record the anchor and duration now and derive the absolute UTC deadline
     from actual creation time (simulated creation time in dry-run) afterward.
     Do not start that clock at draft preparation or confirmation time.
3. Once the version is known, create or update
   `~/.kvrocks/release-[version]/release-state.json`, including partial inputs and
   `awaiting_confirmation` status. Validate the version before using it in a path
   (see the record reference). Persist after each material decision and before
   ending a turn. Do not start a version-specific record while merely authoring
   this skill without an actual release version. Save the discussion body in
   `discussion-draft.md` beside the JSON file; keep all status, approvals,
   deadlines, history, notes, and the next action in the JSON state.
4. Show the concrete destination, category, title, full discussion body, full SHA,
   exclusions, exact deadline or creation-relative rule, and execution mode in
   the confirmation message.
   Once all inputs are available, display the complete proposal with no remaining
   placeholders. A parameter list, summary, or file link does not replace the
   inline title and body. Require release-manager
   confirmation of all required values and this proposal before simulating or
   performing creation. Previously supplied explicit confirmations count; ask
   only about unresolved or changed details. When requesting confirmation of a
   revision, display the entire revised discussion again. Keep `approval` null
   until complete.
5. Pin the confirmed SHA. A newer upstream tip does not silently change the
   proposal. Changes to the version, exclusions, SHA, deadline, destination,
   category, or draft invalidate approval and require review of the changed
   proposal. Log the change. A different version belongs in its own record.

## Step 1: record the outcome and stop

Before completing step 1, require a future, timezone-aware deadline or an approved
positive duration after creation, and complete manager approval for the effective
mode. The preview may state the approved duration relative to discussion creation;
it must contain no unresolved placeholders. Once approved, record creation time
once and derive `cherry_pick_deadline` from it if a rule is set. This deterministic
calculation needs no additional approval and must not reset on resume.
In dry-run, save the exact approved proposal, `approval`,
`discussion.simulated_at`, the absolute deadline, and `dry_run_waiting` status.
Leave `discussion.url` and `discussion.created_at` null. State that the discussion
was **not posted** and name the local record and deadline.

For an explicitly authorized live run:

1. Search existing `apache/kvrocks` discussions for the same release first. If a
   matching discussion exists, inspect and resume it; do not post another.
   If duplicate checking fails, stop before publishing.
2. Verify the repository and General category through read-only GitHub metadata.
   Create the approved discussion through an available GitHub capability only
   after the approval above. Do not substitute a GitHub issue or comment. If
   creation is unavailable, keep the approved draft and report the blocker.
3. Persist the returned URL, actual creation time, the absolute deadline derived
   from that timestamp if a creation-relative rule was approved, and
   `waiting_for_cherry_picks` status immediately. If the request result is
   ambiguous, save `publication_uncertain` and reconcile before retrying.

When switching a rehearsal to live, preserve the rehearsal history, verify a
future deadline or review the duration rule, review the live proposal, and obtain
live approval. Derive any relative deadline from the new live creation time.
When viewing
an existing live release in dry-run, keep its live record intact; report a
read-only preview instead of converting it into a simulated release.

Run `scripts/check_state.py` after each saved outcome and on every resumption.
Compare absolute UTC instants, not date strings. If the current time is before
the deadline, the next step is blocked even if asked to continue. At or after the
deadline, perform the checkpoint below. Neither a timer nor an elapsed deadline
authorizes new release work.

## Before entering the next step

1. After the cherry-pick deadline, read the current proposal discussion and all
   comments and nested replies, including every page of results. Check for
   unresolved objections to proceeding with this release. Record
   `discussion_review` with the check time, source, outcome, and a summary with
   links to any objections and their resolutions.
2. If an objection remains unresolved, keep the release at step 1 and show it to
   the release manager for resolution. If the discussion cannot be read completely
   or a comment's meaning is unclear, record an unverified review and resolve the
   uncertainty first. An unread or partially read discussion is not evidence of
   no objections. Recheck after a resolution; do not dismiss objections yourself.
3. If there are no unresolved objections, show the release manager the review
   summary, current discussion title and full body, discussion link, elapsed
   deadline, execution mode, and proposed next step.
   **Ask for explicit confirmation before entering that step.** Proposal
   creation approval, community silence, and a generic earlier request to
   continue do not replace this confirmation after the review. If the next step
   has not been defined, ask the manager to define and confirm it first.
4. Persist `next_step_confirmation` separately from the original proposal
   `approval`, including who confirmed, when, the mode, the reviewed feedback,
   and the agreed next step. Keep it null until the manager confirms. On resume,
   refresh the discussion before advancing; new objections or material changes
   to the proposal or next step invalidate the transition confirmation. Reuse an
   existing confirmation only for the unchanged, reviewed transition.
5. In dry-run, an unpublished proposal has no discussion feedback to review.
   Record the review as unverified and stop at this checkpoint. To rehearse it,
   use explicitly supplied or authorized sample feedback, label the review and
   confirmation as simulated, and obtain the same manager confirmation for the
   simulated next step. Simulated evidence never satisfies a live transition.

Only enter a defined next step once the deadline has elapsed, the discussion has
no unresolved objections, and the release manager has confirmed that transition.
Keep these results and the pending action in the per-version release record.

## Step 2: Create source releases and stage

Read [the source-release procedure](references/source-release.md) before starting
step 2 or resuming its work. It covers release-branch preparation, source
packaging/signing, validation, and a separately confirmed candidate-tag push.
First complete the preceding deadline, objection-review, and transition
confirmation checkpoint; set `next_step_confirmation.target_step` to `2`.
Defining this procedure or preparing the skill cannot bypass that checkpoint.

Persist candidate inputs, artifact evidence, validation results, and each external
operation in the same per-version JSON file. Stop after step 2 and obtain the
manager's instructions and confirmation before a later release step.

## Step 3: Build and push Docker images

Follow [the Docker readiness procedure](references/docker-readiness.md). This
step observes the workflow already triggered by the approved candidate-tag push;
it does not manually build/push images or start/rerun workflows. After step 2
finishes, confirm entry to step 3 and the concrete external read operations.
Keep the original step-2 transition approval intact and record this confirmation
in `docker.entry_confirmation`.

Wait for the matching candidate's workflow and required jobs to succeed, then
verify the published image reference, digest, and platforms. Persist run identity,
attempt, progress, image evidence, and the next action in `release-state.json`.
Use bounded polling under one confirmed scope instead of asking on every poll.
Failure, cancellation, a missing run, or an unavailable image must not be reported
as ready. Stop after readiness and obtain confirmation before the next release step.

## Step 4: Draft the release vote email

Follow [the email drafting procedure](references/vote-email.md). Confirm entry
after Docker readiness and save `email.entry_confirmation` separately. Check
whether a Gmail connector is available and can create drafts for the intended
account. **Confirm the exact From address with the release manager before
composing the subject or body**, including for the manual fallback and dry-run.

After sender confirmation, show the complete From, To, Cc/Bcc, subject, and body
for review. In live mode, create only the confirmed Gmail draft through the
connector if supported; otherwise provide the subject and body and ask the
manager to send them manually once all release links are verified. Dry-run
prepares local content and simulates any approved draft creation; it never
creates a remote draft or requests a real send. Persist the sender approval,
reviewed content, connector result or manual handoff, and pending action in JSON.
Drafting does not start the vote clock or authorize sending or the next step.

## Step 5: Wait for voting and draft the vote result

Follow [the voting procedure](references/voting.md). Confirm entry after the vote
email draft/handoff. Use the recorded vote start time or ask the release manager
when the vote email was sent; a draft alone does not start the clock.
Wait at least 72 hours, then **ask the release manager whether the vote passed**
before entering the next step. Do not inspect the vote thread, count ballots, or
verify PMC membership; the release manager determines the outcome.

Save the manager's answer, identity, time, candidate, and mode in JSON. A missing,
unclear, early, or negative answer cannot authorize advancement. A positive answer
after the deadline permits the stated next step, drafting the result email,
without another vote-result confirmation. Reuse the sender/content/draft
checkpoints for `result_email`, preserving the opening email and dry-run mode.

## Step 6: Publish artifacts and images, then hand off GitHub release notes

Follow [the publication procedure](references/publication.md). Require the
manager-confirmed passed vote after its deadline, completed result draft/handoff,
and confirmation of entry to step 6. Preserve all earlier evidence. Show and
confirm each external operation before execution: move the voted SVN artifacts
to the release directory, then promote the verified candidate Docker digest to
the version tag and `latest`. Persist each outcome independently and reconcile
uncertain or already-completed operations before any retry.

After artifact and image publication, ask the release manager to publish the
GitHub release notes for the voted commit and record their completion report.
The skill does not publish the GitHub release. Dry-run simulates the publication
and manual handoff without requesting a real publication. Confirm entry before
continuing to step 7.

## Step 7: Create a PR to update website links

Follow [the website PR procedure](references/website-pr.md) after completed
publication and the manager's GitHub release-note confirmation. Confirm entry,
then prepare the release-data change in the separate `apache/kvrocks-website`
repository. Validate the generated download and release-note links. Show the
complete diff, checks, target branches, and PR title/body before asking for the
external push and PR-creation approvals. Persist each result for resumption.

Dry-run keeps the patch and PR content local and simulates approved writes with
no real PR URL. After the PR outcome is recorded, confirm entry to the final
announcement handoff. PR creation does not authorize merging or deployment.

## Step 8: Ask the release manager to send the announcement and finish

Follow [the final announcement handoff](references/announcement.md). After
completed step 7 and entry confirmation, ask the manager to send the release
announcement to `dev@kvrocks.apache.org`, Cc `announce@apache.org`, using an
`@apache.org` sender. This is a manual handoff; the skill does not send mail.
If asked to help draft it, confirm the exact sender before composing content.

Record the handoff and wait for the manager to confirm sending. Their completion
report is sufficient; do not inspect their mailbox or require an archive URL.
Then save `release_complete` and the completion time in JSON. In dry-run, ask
only for acknowledgment of the simulated handoff, keep actual sending evidence
null, and finish with `dry_run_release_complete`. This is the last step.
