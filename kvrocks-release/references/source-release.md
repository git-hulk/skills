# Create source releases and stage

Follow the [official section](https://kvrocks.apache.org/community/create-a-release/#create-source-releases-and-stage).
Its scope is release-branch preparation, source packaging, build validation, and
pushing the candidate tag. SVN artifact upload is a separate following section;
do not perform it under this step. The user's deadline and confirmation gates
apply before any release preparation even where the guide describes earlier
branch creation. Reading or editing this skill does not start a release step.
Local validation here does not replace [step 4a verification](verify-candidate.md)
of the actual uploaded archive before the vote email.

## Enter and resume

Read `release-state.json`, run `check_state.py`, and complete the step-1
transition checkpoint. Require an elapsed deadline, a complete discussion review
with no unresolved objections, and manager confirmation targeting step 2.
Dry-run needs explicitly authorized sample feedback if no discussion exists;
never manufacture community feedback or skip the waiting period to test step 2.

After confirmation, set `step` to `2`, `status` to `preparing_source_release`, and
initialize `source_release` in the existing state. On resume, preserve completed
work and reconcile local tags, artifacts, and recorded external-operation results
before rerunning anything. Keep step-1 discussion and approval evidence intact.
Run the state checker after entering step 2 and after each saved outcome.

## Prepare a concrete candidate plan

Confirm any unresolved candidate inputs together:

- Release branch and starting SHA. The guide uses `X.Y` for a feature release and
  the existing `X.Y` branch for a patch release. Verify or create it only within
  the approved scope. Propose a separate local `codex/` working branch in an
  isolated clone when needed; do not change the user's active checkout.
- Candidate number, a positive integer, and resulting tag `vVERSION-rcN`. If no
  number was supplied or saved, propose **1** and show `vVERSION-rc1`. Ask the
  release manager whether that RC number is correct as part of this candidate-plan
  confirmation, before packaging or creating a tag. A default is a proposal, not
  approval. Use a supplied or saved number instead of resetting it to 1; reuse
  an explicit confirmation for the unchanged candidate. Always supply `-rc`;
  omitting it creates a final-version tag in the current helper.
- Explicit cherry-pick list or none, and the reviewed patch implementing any
  release exclusions. The proposal cutoff is not proof that HFE exclusions or
  subsequent agreed cherry-picks have been applied. Inspect the release diff and
  verify the agreed scope, including retained metadata changes where applicable.
- Signing-key fingerprint and isolated checkout/artifact locations. Do not
  silently use whichever GPG key happens to be the default.

Preserve the proposed cutoff separately from the final prepared source commit.
Record selected commits, exclusion patch, branch, candidate tag, and signing
fingerprint in `source_release`. Explain changes from the approved proposal and
obtain review for changed scope. GitHub branch/tag inspection needs no operation
confirmation. Clone/fetch, dependency downloads, and any remote branch
creation/push each need a concrete external operation preview and confirmation.
Prefer an isolated local clone from available objects when sufficient. Confirm
the exact upstream URL rather than assuming that a remote named `origin` belongs
to Apache.

## Package and validate locally

Inspect `package_source` in the selected checkout's `x.py`, effective Git hooks,
and signing setup before execution. Before the first run too, inspect the output
paths, release branch, candidate tag, and any existing version commit/artifacts.
Verify and resume matching work; stop for conflicting or unverified contents
instead of allowing the helper to overwrite files or recreate a tag. Record this
resource check in the step state. The inspected implementation during skill
authoring does the following in order:

1. Writes the supplied version to `src/VERSION.txt`.
2. Runs `git commit -a`, which includes all tracked modifications, and creates an
   annotated `vVERSION-rcN` tag.
3. Archives `HEAD` with the prefix `apache-kvrocks-VERSION-src/`.
4. Creates a detached armored GPG signature and SHA-512 checksum.

The command below has **no dry-run option**. Preview its local changes and signer
before any run, and use a clean, isolated checkout containing only reviewed
release changes. Inspect an interrupted run before retrying: the version commit
or tag may already exist. Do not delete or move existing candidate tags to retry.

```bash
./x.py package source -v VERSION -rc N
```

Expected files in that checkout (verify against the inspected helper):

```text
apache-kvrocks-VERSION-src.tar.gz
apache-kvrocks-VERSION-src.tar.gz.asc
apache-kvrocks-VERSION-src.tar.gz.sha512
```

Select the confirmed signing key in an isolated signing configuration, using the
manager's interactive passphrase mechanism if needed. Do not put secret keys or
passphrases in state, commands, or logs. New key generation, keyserver upload, and
changes to ASF KEYS are separate operations requiring instructions and their own
confirmation; they are not implicit prerequisites this step may execute.

Verify the archive checksum, detached signature and signer fingerprint, archive
root/version, LICENSE/NOTICE files, and absence of unexpected generated files.
Extract to a fresh directory and compile **the extracted archive**, using the
repository's build entrypoint (for example `./x.py build --ninja`). Complete
relevant tests and required formatting/lint checks for release changes. Capture
commands, actual results, artifact sizes/hashes, prepared commit, tag object ID,
and peeled tag commit. Ensure the tested source matches the candidate tag. Rebuild
and revalidate if source or artifact bytes change; never mark a planned check as
passed. Inspect build configuration and confirm any dependency downloads first.

In dry-run, preview packaging and signing by default. A local packaging rehearsal
requires the manager to agree to the listed local effects and an isolated test
signer; do not use a production release key for a rehearsal. If actual local
artifacts or build results were not produced, record them as planned/simulated,
never as verified. A simulated staging result cannot be reused as live evidence.

## Preview and confirm the tag push

For a live push, finish successful candidate validation first and set
`source_release_validated`. Prepare a review containing the exact upstream URL,
single tag ref, local tag object ID and peeled commit, artifact manifest, and
build/signature results. For dry-run, show actual evidence if available and label
any unexecuted packaging or validation explicitly as simulated.

Inspect the candidate's `.github/workflows/nightly.yaml` and explain triggered
effects in the same preview. At authoring time, `v2.**` pushes trigger the nightly
workflow, including Docker Hub image/manifest publication. Tag-push approval
must cover those effects too. Do not assume a tag push is only a Git metadata
change. Check the current workflow rather than freezing this behavior forever.

Render an exact command with resolved values before asking for confirmation:

```bash
git push RELEASE_REMOTE_URL refs/tags/vVERSION-rcN:refs/tags/vVERSION-rcN
```

Inspect remote tag existence before requesting push approval. GitHub tag checks
and post-push verification require no separate read confirmation. If the remote
tag already points to the intended object/commit, reconcile recorded evidence;
do not push a duplicate. If it differs, stop for manager resolution. Never use
`--tags`, force-push, push an unreviewed branch, or overwrite a candidate tag.

Save the external operation with status `prepared`, ask the manager to approve
this exact operation, then record the approval. Step-transition approval is not
tag-push approval. In live mode, perform only the confirmed push and verify its
result through read-only GitHub checks. In dry-run, record a simulated push without
contacting the remote or triggering CI. Leave actual remote-result fields null.

Record `source_release_staged` only for a validated candidate with a verified
remote tag, or `dry_run_source_release_staged` for a completed rehearsal of the
checkpoints. Record `source_release.completed_at` at that point and preserve it
when entering step 3. A failed/ambiguous push uses `tag_push_uncertain`; reconcile before
retrying and retain artifacts and the local tag. Record the exact outcome and
next action, then stop. No SVN uploads, GitHub release publication, Docker retags,
votes, or announcements are performed by this step.
The next defined step monitors the existing GHA run and Docker image readiness;
show its scope and obtain manager confirmation before entering it.

## Step-2 state

Keep `source_release` null before entering step 2. Initialize it with the confirmed
values and fill evidence only when obtained. Keep `candidate_number` and
`candidate_tag` null until confirmed; record the proposed default and the manager's
answer in history. An existing confirmation for the same candidate remains valid:

```json
{
  "release_branch": null,
  "base_commit": null,
  "candidate_number": null,
  "candidate_tag": null,
  "cherry_picks": null,
  "exclusion_patch": null,
  "checkout_path": null,
  "signing_fingerprint": null,
  "prepared_commit": null,
  "tag_object": null,
  "artifacts": [],
  "validation": [],
  "tag_push_operation_id": null,
  "remote_tag": null,
  "completed_at": null
}
```

Use artifact entries with path, size, SHA-512, and actual/simulated status;
validation entries with command, result, time, and log path. `remote_tag` contains
verified live `repository` (`apache/kvrocks`), `ref` (`refs/tags/vVERSION-rcN`),
`object`, `commit`, and `verified_at` values only. Store all
approval state in JSON; supporting patches, archives, and logs may be separate
files in the per-version directory. Candidate retries preserve earlier evidence
in history and use a manager-confirmed new RC number instead of overwriting it.
