# Step 4a: Verify the uploaded release candidate

This required checkpoint follows Docker readiness and precedes vote-email
drafting. Follow the [Kvrocks candidate verification checklist](https://kvrocks.apache.org/community/verify-a-release-candidate/).
The release manager must ensure every checklist item is covered. Successful local
packaging, a pushed tag, working links, or a ready Docker image alone do not verify
the uploaded source archive.

## Entry and resource confirmation

Read the saved JSON and run the checker. Require completed step 3 for this
candidate. Show the candidate tag, prepared commit, mode, proposed verification
work, and pending staging URL; ask the manager to confirm entry. Record
`candidate_verification.entry_confirmation` and set `step: 4`, status
`verifying_uploaded_candidate`. Keep `email` null. Persisted step numbers stay
unchanged: verification is **4a**, and email drafting is **4b**. Report the phase
name and exact saved status at the expected-step checkpoint on every resumption.

Obtain the actual uploaded candidate directory from saved evidence or the manager.
Initial SVN upload remains a manual prerequisite outside this procedure. If it
has not happened, record `candidate_verification_blocked` and ask the manager to
complete it. Do not upload, invent a successful upload, or assume a directory
layout: the verification guide's VERSION-RC example can differ from the release
guide's VERSION directory. Use the confirmed actual Apache dist staging URL.

Before external operations, preview and confirm the concrete requests, URLs,
mode, local destinations, and effects. A transition approval is not download
approval. First confirm directory/revision discovery reads; then use the observed
revision in the exact artifact/KEYS download preview. Record each approval and
outcome in `external_operations`. An enumerated batch may cover the SVN checkout
at that revision, all three files, KEYS, and subsequent identity rechecks. Request
new approval if scope changes. Do not silently contact a keyserver or fetch build
dependencies outside the approved scope.

Inspect saved outcomes, local destination paths, and the remote inventory before
creating the verification workspace or downloading. Save `resource_check` and
reuse a matching workspace only after proving its downloaded bytes and revision
match; resolve conflicts without overwriting evidence. Use a fresh isolated
directory for a new attempt, separate from the packaging checkout.

## Verify the downloaded bytes

1. **Downloads:** record the actual staging URL and positive SVN revision. Fetch
   `apache-kvrocks-VERSION-src.tar.gz`, its `.asc`, and its `.sha512`, plus
   `https://downloads.apache.org/kvrocks/KEYS`, under the approved read scope.
   Check every command's exit status and each expected file's presence/content.
   Reject error pages and unexpected/missing files. Record SHA-512 for all three
   downloaded files and compare with the prepared source artifact manifest.
   A discrepancy blocks the vote; do not replace the expected hashes just to pass.
2. **Checksums:** validate the checksum entry's exact archive filename and digest,
   then run `shasum -a 512 -c ARCHIVE.sha512` in the download directory. Reject
   unexpected entries or paths. Record the result and log independently of other
   checks.
3. **Signatures:** import the downloaded KEYS into an isolated temporary
   `GNUPGHOME`, then run `gpg --verify ARCHIVE.asc ARCHIVE`. Check the exit status
   and full signing/primary-key fingerprint against the manager-confirmed
   `source_release.signing_fingerprint`; resolve a signing subkey to that primary
   key. Record both fingerprints when applicable. Do not assign ultimate trust
   or modify the manager's normal keyring. A valid signature with an unexpected
   key fails this checkpoint. Do not use a shell wrapper whose final successful
   command can hide a previous signature/checksum failure.
4. **Archive:** inspect member paths before extraction, reject escaping paths or
   links, and extract into the isolated workspace. Check source archive naming,
   internal release version and expected source layout. Confirm correspondence
   with the prepared commit and exclusions using the matching prepared artifact
   hashes and source evidence. Record what was inspected, not just "looks good".
5. **LICENSE and NOTICE:** inspect these files in the downloaded archive for
   correctness and consistency with the candidate repository and bundled content.
   Record findings and file paths. Presence alone is insufficient.
6. **License headers:** inspect applicable source headers, documenting any valid
   exclusions such as generated or third-party files. Use the project's applicable
   checks where available and record the review's scope and outcome. Do not mark
   an unperformed manual review as passing.
7. **Build:** build from the extracted downloaded source using its documented
   command (normally `./x.py build`). Record command, environment, exit status,
   and log path. Inspect the helper for implicit dependency/network operations and
   confirm those before running. A build of the original Git checkout is not
   evidence that the uploaded source builds. Run additional tests when needed to
   resolve a concrete concern, recording their results separately.

These seven items cover the source-only candidate supported by this skill. If
the staging inventory contains additional packages, stop and extend the manifest
and applicable verification scope with the manager; do not silently ignore them
or claim the whole candidate passed after checking only the source archive.

Save each result as it finishes. Any failure, unavailable prerequisite, missing
file, incomplete review, or uncertain command outcome keeps verification blocked
with a concrete `blockers` entry and `completed_at: null`. Resume only the missing
or failed work when candidate identity and prior evidence remain unchanged. Never
draft/create the vote email or request sending while this gate is unresolved.

## Completion, dry-run, and invalidation

In release mode, all seven checks must actually pass on the staged bytes. Set
`uploaded_candidate_verified` and its completion timestamp only then. Show the
manager the URL/revision, candidate, file hashes, signer, check results, and logs,
and ask for confirmation to enter **4b: Draft the release vote email**. Save that
separate confirmation in `email.entry_confirmation`, binding it to
`publication_plan_sha256(candidate_verification)` as `verification_sha256`.
Then follow the [sender and content checkpoints](vote-email.md). Verification
approval never confirms an email sender, creates a Gmail draft, or sends mail.

Dry-run retains the same checkpoints. Preview verification commands and use
explicitly authorized local fixtures by default. Record `simulated_pass` results,
the fixture source, simulated read scope, and
`dry_run_uploaded_candidate_verified`. No real release verification, remote write,
or email send is implied. A fixture cannot satisfy a release-mode gate. Actual
optional reads or local builds in dry-run need their proper approval/evidence;
keep those observations in history without converting the simulated gate to live.

On resume and before handing off the vote email, recheck the staged identity under
approved reads. If the URL, revision, tag, commit, signing key, or artifact bytes
change, preserve prior evidence in history and invalidate verification plus any
dependent email entry/content approval. Rerun the relevant verification on the new
candidate and obtain fresh transition approval. Do not silently update or resend
an existing draft. If a vote email was already sent, stop for the manager's
candidate/revote decision; never rewrite historical evidence to make it current.

## JSON record

Keep `candidate_verification: null` before step 4a. Initialize it only after entry
confirmation. Pending fields may be null; completion requires all evidence below:

```json
{
  "status": "verifying_uploaded_candidate",
  "mode": "dry-run",
  "simulated": true,
  "entry_confirmation": {
    "by": "MANAGER",
    "at": "RFC3339",
    "mode": "dry-run",
    "simulated": true,
    "target_step": 4,
    "phase": "verify_uploaded_candidate",
    "candidate_tag": "CONFIRMED_TAG",
    "prepared_commit": "CONFIRMED_FULL_SHA"
  },
  "source_url": null,
  "source_revision": null,
  "keys_url": "https://downloads.apache.org/kvrocks/KEYS",
  "signing_fingerprint": null,
  "files": [],
  "resource_check": null,
  "read_operation_ids": [],
  "evidence_source": null,
  "checks": {},
  "blockers": [],
  "completed_at": null
}
```

`files` contains the three `{name, sha512}` entries, including hashes of signature
and checksum files, matching `source_release.artifacts`. `checks` has exactly
`downloads`, `checksums`, `signatures`, `archive`, `license_notice`,
`license_headers`, and `build`. Each stores `{result, at, command_or_review,
evidence}`; evidence identifies the actual log/review findings, and may be extended
with exit code, environment, reviewer, fingerprints, or other supporting details.
Live success is `passed`; rehearsal success is `simulated_pass`.

`read_operation_ids` references the approved completed batch that downloaded the
candidate and KEYS (or simulated it). Its `step` is 4, `kind` is `read`, and
`inputs` contains exactly `{source_url, source_revision, keys_url}`; the operation
preview enumerates concrete commands, local paths and effects. Keep preliminary
discovery and extra build-dependency reads as separate external operations.

For older records, add this field as null without changing numeric steps or
fabricating verification. Records already at email or later with missing evidence
are blocked for reconciliation before further work. Preserve previously sent mail
and completed outcomes; do not repeat them. Existing successful checks may be
reconciled only from genuine recorded evidence for these exact uploaded bytes,
with the manager confirming the corrected current status.
