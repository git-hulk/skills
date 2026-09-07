# Offer local artifact cleanup after completion

After recording `release_complete` or `dry_run_release_complete`, ask the release
manager whether to remove this version's local artifacts. This is optional local
housekeeping after the release process; keep `step: 8`, the terminal status, and
`next_action: null`. Declining or postponing cleanup does not undo completion.
Defining this procedure is not approval to delete anything now.

## Prepare the exact removal list

Read the full release state and any saved `local_cleanup` first. Use recorded
`source_release.artifacts[].path` and `candidate_verification.local_artifacts[].path`
to locate only this release's generated files: tarballs, detached signatures,
checksum files, downloaded copies, and disposable extracted/build output.
Inspect each path locally before proposing it. Resolve missing or ambiguous
ownership with the manager; never infer targets from a broad wildcard or just a
version-like filename. Report absent artifacts as already absent, not deleted.

Show the exact absolute paths, what each contains, and the total size where
available. For a directory, inventory its contents and confirm that it contains
only the proposed disposable output. Retain `release-state.json`, history,
approvals, verification/build logs, discussion and email drafts, source patches,
signing keys, and unrelated files. Do not remove a whole release directory,
working checkout, shared cache, or anything outside the reviewed list. Never
follow symlinks to delete their targets. Preserve artifact hashes and original
paths in the release record even after removal.

With that concrete list displayed, ask:

> The release process is complete. May I remove the listed local artifacts for
> VERSION? The release state, drafts, and verification logs will be retained.

Show the exact deletion command/API and explain that removal deletes these local
copies. Wait for explicit approval of this list. Earlier release approvals and
the request to add this cleanup offer do not approve deletion. If there are no
eligible artifacts, report that and record `nothing_to_remove` without an empty
permission request.

## Execute or keep the files

- **Approved, release mode:** save approval against the exact plan, recheck that
  file identities and directory contents still match, then remove only those
  approved local paths. Use explicit path arguments, never broad recursive globs.
  If anything changed, stop and show a revised list for approval. Verify local
  absence and record the outcome per path. No remote resources are involved.
- **Declined:** record `declined` and retain the files. Do not ask again on later
  invocations unless the manager reopens cleanup.
- **No answer:** record `awaiting_confirmation` and retain everything. Resume
  this pending offer after the normal expected-step checkpoint; do not restart
  the release or assume silence grants approval.
- **Dry-run:** show and confirm the same removal plan as a simulation, then mark
  `simulated`; do not execute deletion or claim files were removed. Actual cleanup
  of rehearsal files requires a separate explicit request and concrete approval.
- **Partial failure or uncertain result:** record `partial` and each observed
  result. Inspect remaining paths before retrying, preserving successful outcomes.
  Unchanged approval can cover the remaining unchanged paths; changed scope needs
  fresh approval. Never repeat removal against a recreated or changed resource.

Keep `local_cleanup: null` until this post-completion offer is prepared. Then
record `{status, mode, plan, approval, results, completed_at}` in the same per-version
JSON. `plan` contains version, inspection time, exact paths, kinds, sizes/hashes or
directory inventories, retained paths, and the concrete command/API preview.
`approval` is null until confirmed, then stores `{by, at, mode, plan_sha256}` using
`publication_plan_sha256(plan)`. Each result records path, observation time,
outcome (`removed`, `already_absent`, `failed`, or `simulated`) and any error.
Use status `removed` only after all approved targets are verified absent; preserve
the original release completion timestamp. Append decisions and outcomes to
history. The state checker reports this optional object but does not authorize
or execute deletion; the agent must perform the confirmation and identity checks.

On terminal resumption, report the saved cleanup outcome. Do not repeat declined,
simulated, removed, or nothing-to-remove offers. If the field is absent/null on an
older completed record, prepare the offer once; never fabricate a past decision.
