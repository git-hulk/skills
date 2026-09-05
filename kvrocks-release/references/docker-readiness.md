# Build and push Docker images

This is a monitoring step for the workflow triggered by the RC tag in step 2,
as described in the [release guide](https://kvrocks.apache.org/community/create-a-release/#build-and-push-docker-images).
Observe GitHub Actions and verify the resulting Docker image. Do not dispatch,
rerun, cancel, build, push, or retag anything under this step. Those mutations
require separate instructions and a concrete confirmation.

## Enter and select the correct run

Read the release state and run the checker. Require completed step-2 staging:
`source_release_staged` with verified live tag evidence, or
`dry_run_source_release_staged` for a rehearsal. Resolve an uncertain tag push
before starting this step. Preserve the source candidate, prepared commit,
completion time, and original transition confirmation.

Show the manager the candidate tag, prepared commit, workflow, intended monitoring
operations, and execution mode, then confirm entry. Record that confirmation in
`docker.entry_confirmation`, binding it to the tag and commit. Set `step` to `3`
and `status` to `waiting_for_docker`. This entry confirmation only authorizes
external reads if their concrete scope was also displayed and confirmed.

Inspect the workflow from the candidate's source locally. At authoring time it is
`.github/workflows/nightly.yaml`, named Nightly. A `v2.**` tag push runs matrix
builds for `linux/amd64` and `linux/arm64`, then a merge job publishes the manifest.
Derive required jobs and platforms from the actual candidate workflow, and save
them; do not assume this matrix remains fixed forever.

Preview and confirm a read-only discovery request scoped to `apache/kvrocks`,
the workflow, candidate tag, prepared commit SHA, and the `push` event. For example,
resolve these placeholders before confirmation:

```bash
gh run list --repo apache/kvrocks --workflow nightly.yaml --branch CANDIDATE_TAG --commit PREPARED_SHA --event push --json databaseId,attempt,headBranch,headSha,event,status,conclusion,url,workflowName
```

Use an available GitHub read capability instead if appropriate. Match the exact
repository, workflow identity/path, tag ref, commit, and event, not simply the
newest run or a green run on `unstable`. If listing metadata does not establish
the tag, inspect authorized run/event details rather than guess. If multiple
candidate runs remain ambiguous, show them for manager selection.

Save the selected run ID, URL, attempt, workflow identity, head tag, head SHA, and
event. A missing run remains `waiting_for_docker`; it does not justify triggering
a workflow. Report an absent/disabled workflow or access problem as a blocker
when the available evidence establishes it.

## Wait within a confirmed scope

Before polling, show the exact run, job/log reads, interval, maximum watch duration,
and any registry reads already resolvable. A proposed default is polling every
30 seconds for up to 30 minutes; the manager can choose another bounded window.
Record the approval as an `external_operations` entry and its ID in
`docker.watch_operation_id`. Reuse approval throughout the unchanged window.
Keep individual waits at most 60 seconds so new user input can interrupt them.

Typical read after the run and attempt are known:

```bash
gh run view RUN_ID --repo apache/kvrocks --attempt ATTEMPT --json databaseId,attempt,headBranch,headSha,event,status,conclusion,jobs,url
```

Check run status, conclusion, and every required build and publication job. A
successful matrix build alone is insufficient while the merge job is pending.
Do not rely solely on `gh run view --exit-status`: a nonterminal run can still
produce a zero exit code. Inspect the returned status and conclusion explicitly.

- Queued, waiting, pending, or running: persist progress and wait again within
  the approved window. Report meaningful changes without repeating every poll.
- Completed with all required jobs successful: proceed to image verification.
- Failed, cancelled, timed out, skipped, neutral, or awaiting intervention:
  record `docker_blocked`, link the run and affected jobs, and summarize the
  reason using approved log reads. Do not rerun or modify the workflow.
- Polling window expires or rate limits/access errors prevent reads: save the
  last observation and pending action. An elapsed watch window is not a workflow
  failure or image readiness. Resume under valid approval or confirm a new window.

Pin the run and attempt together. If someone starts a new attempt, preserve the
previous attempt in history, verify the new attempt still matches the candidate,
and observe it only within the approved scope. Never use success from an older
attempt to report a newer running attempt as ready. A changed candidate tag/SHA
invalidates this monitor and requires a new entry confirmation.

Do not create a recurring automation merely while authoring or running this skill.
During an active monitoring invocation, use bounded waits and save progress before
ending the turn. Background monitoring needs an explicit scheduling request and
must preserve the confirmed read scope and notify only on meaningful changes.

## Verify the image and record readiness

Get the exact published image reference and multi-platform manifest digest from
the successful run's publication outputs/logs. Do not calculate a nightly date
from the current clock, assume a short SHA length, or substitute `latest`.

Show the discovered registry/repository, exact image reference/digest, and planned
read-only manifest inspection, then confirm that read unless already covered by
the approved scope. For example:

```bash
docker buildx imagetools inspect EXACT_PUBLISHED_IMAGE_REF
```

Inspect only; do not pull/run the image or invoke `imagetools create`. Verify the
registry reference resolves to the published digest and contains every expected
platform. A successful GHA run with a missing image or manifest is not ready;
remain waiting for a transient propagation delay within an approved window, or
record a blocker when the registry response establishes a mismatch or error.

Set `docker_ready` only after the matching workflow and all required jobs have
succeeded and the registry manifest is verified. Record the run/attempt/link,
published reference, digest, platforms, verification time, and completion time.
Report those results and stop for the next step's confirmation.
The next checkpoint is [step 4a: verify the uploaded candidate](verify-candidate.md),
before any vote-email drafting. A ready Docker image does not verify source uploads.

In dry-run, a simulated tag push creates no real workflow. Use explicitly
authorized local run/job/manifest fixtures to rehearse waiting, failure, and
readiness; mark the evidence simulated and retain the fixture source. Do not
borrow another release's successful run. Use `dry_run_docker_ready` only for a
completed simulated readiness check, never claim a real image was published.

## Docker state

Keep `docker` null before entering step 3. Initialize:

```json
{
  "entry_confirmation": null,
  "workflow_path": ".github/workflows/nightly.yaml",
  "expected_platforms": [],
  "watch_operation_id": null,
  "watch_until": null,
  "poll_interval_seconds": 30,
  "last_checked_at": null,
  "simulated": false,
  "evidence_source": null,
  "run": null,
  "image": null,
  "completed_at": null
}
```

`entry_confirmation` records `by`, `at`, `mode`, `simulated`, `target_step: 3`,
`candidate_tag`, and `prepared_commit`. Set `docker.simulated` to true and
`evidence_source` to the authorized fixture for a rehearsal. Preserve
`next_step_confirmation` as the original step-2 approval.

`run` records `id`, `attempt`, `url`, `repository`, `workflow_path`, `head_branch`
(candidate tag), `head_sha`, `event`, `status`, `conclusion`, and `jobs` (the
complete required job set, each with ID/name/status/conclusion). Add
`published_image` and `published_digest` from successful publication outputs.
`image` records `ref`, `digest`, `platforms`, and `verified_at` from the registry
inspection or explicitly simulated fixture. Keep unavailable values null and
record blockers in `next_action`; do not fabricate successful observations.
