# Step 6: Publish SVN artifacts and Docker images; hand off GitHub release notes

Follow the official [SVN publication](https://kvrocks.apache.org/community/create-a-release/#publish-artifacts-to-svn-release-branch)
and [Docker publication](https://kvrocks.apache.org/community/create-a-release/#publish-docker-images)
sections. External operations follow `SKILL.md`: GitHub status checks need no
approval; SVN and registry reads and writes retain their concrete confirmation
requirements. Authoring this procedure never advances an active release.

## Entry and preparation

Read the complete JSON state and run the checker. Require completed step 5 in
the current mode: the manager confirmed passage after at least 72 hours and the
result email draft/manual handoff is complete. Do not inspect the vote thread or
recount votes. Show the version, voted candidate tag and prepared commit, saved
vote decision, intended SVN/Docker destinations, and mode; confirm entry to step 6. This entry confirmation does not approve its external operations.

Save `publication.previous_status`, a separate `publication.entry_confirmation`,
and `step: 6`, `status: preparing_publication`. Bind entry to the candidate, vote
snapshot, and Docker digest. Preserve the opening/result emails and earlier
approvals. Do not rebuild, repackage, or re-sign the voted candidate. Missing
staging evidence must be supplied or verified, never manufactured from local paths.

In dry-run, prepare exact commands locally and simulate approved writes. Use
explicitly authorized fixtures for simulated external evidence. Keep real
publication results and GitHub URLs null; do not run SVN moves, registry writes,
or remote-capable commands just because they offer a `--dry-run` flag.

## Publish the SVN artifacts

1. Prepare and confirm reads of the exact source directory from the opening
   email's `artifact_review.source_url` and destination
   `https://dist.apache.org/repos/dist/release/kvrocks/VERSION`. Inspect a fixed
   repository revision and verify the complete directory contains exactly the
   voted archive, detached signature, and checksum file:
   `apache-kvrocks-VERSION-src.tar.gz`, `.tar.gz.asc`, and `.tar.gz.sha512`.
   Compare SHA-512 of each file with `source_release.artifacts`, retaining the
   earlier signature/checksum validation. Record the revision, filenames, hashes,
   destination existence, and check time in the plan. Include precise list/info
   and file-download requests in the read preview; downloads are external reads.
2. If the release destination exists, compare its complete contents to the voted
   manifest. A matching destination is `already_published` after approved
   verification; do not move again. Conflicting contents block publication.
   If the source is missing, reconcile the destination before doing anything
   else. Never recreate or silently delete either directory.
3. For an absent destination, preview the move, including its deletion of the
   staging path and creation of a public release directory. The guide uses
   `svn mv SRC DST -m "Release VERSION"`. Use this revision-guarded equivalent:

   ```text
   svnmucc --revision REVIEWED_REVISION --message "Release VERSION" mv https://dist.apache.org/repos/dist/dev/kvrocks/VERSION https://dist.apache.org/repos/dist/release/kvrocks/VERSION
   ```

   Substitute exact values and save an argument array, not a shell string with
   unresolved variables. `svn move -r` does not pin the move; `svnmucc --revision`
   supplies a baseline and rejects a source changed since review. Recheck and
   reapprove changed evidence after such a conflict. A normal URL-to-URL move can
   nest the source inside an existing destination, so never blindly retry it.

4. After concrete live approval, execute only that move. Save the returned
   revision immediately, then use approved outcome reads to verify destination
   bytes and source disappearance. Keep an interrupted or ambiguous result
   `uncertain` until reconciled. If permissions prevent publication, give the
   reviewed command to the release manager to arrange execution by a PMC member;
   do not change permissions or mark the handoff as successful publication.

## Publish Docker images

After SVN publication is verified or simulated, use the **recorded candidate
digest** from step 3. Do not choose today's nightly tag, rebuild an image, or
dispatch/rerun GitHub Actions. Under approved reads, verify that source manifest
and the recorded required platforms still exist, and inspect both target tags.
Record each target's current digest, or a verified absence, before its write.

Preview and confirm these two concrete operations separately or as an enumerated
batch, replacing every placeholder:

```text
docker buildx imagetools create --tag apache/kvrocks:VERSION apache/kvrocks@sha256:APPROVED_DIGEST
docker buildx imagetools create --tag apache/kvrocks:latest apache/kvrocks@sha256:APPROVED_DIGEST
```

This promotes the existing multi-platform image index. Show the old and new
digests and explicitly include the change to `latest` in approval. If a version
tag exists with a different digest, stop and resolve the conflict; do not
overwrite it. If `latest` points to a newer release, resolve that specific change
with the manager before publication. A target already matching the approved
digest and platforms is `already_published` after approved reads and needs no
write. Changes since preview require reconciliation and renewed approval.

Record each target independently. After each live write, verify its exact digest
and expected platforms through the approved reads. A command's success alone is
insufficient. On partial success, retain the successful target and resume only
the remaining work. Never automatically undo publication, overwrite version
tags, remove old releases, or retry an uncertain write without reconciliation.

## Ask the manager to publish GitHub release notes

Once SVN and both Docker targets are complete, show a concrete handoff in this
conversation: repository `apache/kvrocks`, release title `Apache Kvrocks VERSION`,
final tag `vVERSION`, exact voted `prepared_commit`, candidate tag, public SVN URL,
Docker tags/digest, agreed exclusions, and any prepared release-note content or
existing draft URL. Use only verified or manager-supplied highlights. In live
mode, ask the release manager to publish the release notes on GitHub and report
the resulting URL, tag, and target commit. No GitHub release creation, edits,
tag pushes, or messages to other people are performed by this skill.

Tell the manager to target the voted commit explicitly when creating the final
tag; GitHub's default branch may have moved. An existing final tag must resolve
to that commit. Creating the tag may trigger the repository's tag workflow and
additional nightly image publication. These effects belong in the handoff.

Set `awaiting_github_release_notes` after the handoff. Asking is not completion.
Record the manager's publication confirmation and URL before marking
`publication_complete`; identify this as manager-reported evidence. In dry-run,
show a **simulated handoff**, ask only for acknowledgment of that rehearsal, and
use `dry_run_publication_complete` after it. Never ask for real publication or
claim a real release URL during the rehearsal. Stop for entry confirmation to
[step 7, the website PR](website-pr.md). The final announcement is a later manual
handoff; cleanup remains outside the defined process.

## JSON fields and resumption

Keep `publication` null before entry. On entry, initialize:

```json
{
  "previous_status": "ACTUAL_STEP_5_OUTCOME",
  "entry_confirmation": {
    "by": "MANAGER",
    "at": "RFC3339",
    "mode": "dry-run",
    "simulated": true,
    "target_step": 6,
    "candidate_tag": "VOTED_CANDIDATE_TAG",
    "prepared_commit": "VOTED_FULL_SHA",
    "vote_snapshot_sha256": "CURRENT_VOTE_SNAPSHOT_HASH",
    "docker_digest": "sha256:APPROVED_DIGEST"
  },
  "svn": {
    "status": "pending",
    "plan": null,
    "operation_id": null,
    "result": null,
    "completed_at": null
  },
  "docker": {
    "targets": [
      {
        "ref": "apache/kvrocks:VERSION",
        "status": "pending",
        "plan": null,
        "operation_id": null,
        "result": null,
        "completed_at": null
      },
      {
        "ref": "apache/kvrocks:latest",
        "status": "pending",
        "plan": null,
        "operation_id": null,
        "result": null,
        "completed_at": null
      }
    ]
  },
  "github_release_notes": {
    "status": "pending",
    "handoff": null,
    "confirmation": null
  },
  "completed_at": null
}
```

Top-level statuses: `preparing_publication`, `publishing_release`,
`publication_blocked`, `release_publication_uncertain`,
`awaiting_github_release_notes`, `publication_complete`,
`dry_run_publication_complete`. Component statuses: `pending`, `blocked`,
`uncertain`, `published`, `already_published`, `simulated`.

- All plans record `checked_at`, `mode`, `simulated`; simulated plans also cite
  the authorized `evidence_source`. SVN plans add `source_url`, `destination_url`,
  positive integer `source_revision`, `files` (objects with `name` and `sha512`),
  and `destination_before` (`absent` or `matching`). Docker plans add `source_ref`
  pinned by digest, `target_ref`, and `previous_digest` (null means verified absent).
- For each approved operation, bind `external_operations[].inputs.plan_sha256`
  using `publication_plan_sha256(plan)` from the checker. Writes save the exact
  `request.argv` shown above, target the SVN destination or Docker target, and
  use `kind: write`. Already-published verification instead uses `kind: read`
  with its exact verification request. Record all ordinary read approvals too.
  Persist raw write receipts and partial observations in operation history as
  they arrive; set the component complete only after verification.
- Live completed components point to a `succeeded` operation and retain the
  verified `result` in both the component and operation. SVN results include
  `revision`, `files`, `source_absent`, `verified_at`; Docker results include
  `ref`, `digest`, `platforms`, `verified_at`. `published` SVN requires source
  disappearance; `already_published` does not authorize deleting a residual dev
  directory. Dry-run components use `simulated` operations and null results.
  Set each `completed_at` after its approval and verification/simulation.
  An already-approved read can establish an existing matching destination;
  reuse it without an extra confirmation or duplicate verification request.
- GitHub notes use `pending`, `awaiting_manager`, `published`, or `simulated`.
  `handoff` stores full `content`, `at`, `mode`, `simulated`, `tag`, and `commit`.
  `confirmation` is null until the manager reports completion (or acknowledges
  the rehearsal); then record `by`, `at`, `mode`, `simulated`, `completed: true`,
  `tag`, `commit`, and `url` (actual GitHub release URL in live mode, null in
  dry-run). The final `publication.completed_at` follows this confirmation.

Preserve completed actions on resume. Read before every save and write JSON
atomically. Changed candidate, vote outcome, manifest, or operation plan
invalidates dependent approval; preserve former evidence in history and stop to
reconcile any already-public resources. The checker validates consistency only:
it neither performs external verification nor grants approval to publish.
