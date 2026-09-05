# Step 4: Draft the release vote email

This is the community vote email following candidate preparation and Docker
readiness in the [release guide](https://kvrocks.apache.org/community/create-a-release/).
If the manager specifies another email purpose, clarify that change before
drafting. This procedure prepares an unsent message only.

## Entry and sender checkpoint

1. Read the per-version JSON and run the state checker. Require completed step 3
   with matching candidate, workflow, and image evidence (authorized fixtures
   for dry-run). Confirm entry to step 4. Record `email.entry_confirmation` with
   `target_step: 4`, the candidate tag and prepared commit; preserve earlier
   approvals and evidence. Defining this step does not approve entering it.
2. Discover Gmail tools through the available connector/tool catalog. If a
   discovery tool exists, search before deciding Gmail is unavailable. A Calendar
   connection, browser login, plugin listing, or cached account address does not
   establish Gmail access. Check both authenticated identity and draft-creation
   capability through the connector when available. Follow the skill's external
   read confirmation rule; the manager's explicit request to check Gmail covers
   that connection/profile check, not reading unrelated mailbox messages.
   Distinguish unavailable tools from a verified disconnected account. Never
   install/connect a plugin, change permissions, or use browser/SMTP/CLI mail
   writes as an automatic substitute. Use the manual fallback when unavailable.
3. Show the observed Gmail account and proposed exact **From address**, including
   any alias, then ask the manager to confirm the sender. If no address is known,
   ask the manager to supply and confirm it. Do not infer it from Git, GPG, or an
   account display name. Do not compose a release-specific subject/body, save a
   connector draft, or mark sender approval before the answer. Record
   `awaiting_email_sender`, with subject, body, and composed time null.
4. Save the confirmed address and `{by, at, mode, address}` in
   `email.sender.confirmation`. If Gmail will be used, verify that the connector
   can actually create a draft with that exact From address. The account's default
   sender is not permission to substitute for a requested Apache alias. If the
   connector cannot select or verify that sender, use manual output with the
   confirmed address. Keep the confirmation when unchanged; a change of sender
   clears content and draft approvals and returns to the sender checkpoint.

Authoring this reusable procedure/template is not composing a release email and
does not require a sender or entry approval.

## Compose and review

After sender confirmation, prepare a plain-text message addressed by default to
`dev@kvrocks.apache.org`, with no Cc/Bcc. Use the actual `source_release.candidate_tag`
(including its leading `v`), version, prepared commit, and verified Docker image
reference and digest. Do not guess a nightly image name from today's date.

Use the guide's vote structure below, filling from the recorded evidence:

```text
Subject: [VOTE] Release Apache Kvrocks VERSION

Hello Apache Kvrocks PMC and Community,

This is a call for a vote to release Apache Kvrocks version VERSION.
The candidate to be voted on is CANDIDATE_TAG.

Release candidate:
VERIFIED_SOURCE_CANDIDATE_URL

Keys to verify the release candidate:
https://downloads.apache.org/kvrocks/KEYS

Git tag:
https://github.com/apache/kvrocks/tree/CANDIDATE_TAG
Commit: PREPARED_COMMIT

Docker image: VERIFIED_IMAGE_REF
Digest: VERIFIED_IMAGE_DIGEST

Please download, verify, and test the release candidate.
The vote will remain open for at least 72 hours.

[ ] +1 approve
[ ] +0 no opinion
[ ] -1 disapprove with the reason

Thank you,
CONFIRMED_SENDER_NAME_OR_ADDRESS
```

Use a signature supplied by the manager or the confirmed address, not an invented
name. Add release notes or claims about validation only when supported by evidence.
The 72-hour vote wording is separate from the cherry-pick deadline; do not set a
vote deadline from draft creation time.

Source tag staging does **not** prove that source artifacts have been uploaded to
Apache dist. Before declaring the email ready for handoff, obtain the actual
candidate directory URL and verify under approved read scope that the archive,
signature, checksum, and KEYS correspond to the candidate and signing key.
Record `email.artifact_review`. This step does not perform an SVN upload.
If evidence or links are missing, a local preview may use explicit
`[SOURCE CANDIDATE URL REQUIRED]` placeholders, with concrete `email.blockers`.
Keep `awaiting_email_review`; do not create a Gmail draft or request sending a
message with unresolved placeholders or unsupported claims. Do not retroactively
mark the source upload complete.

Store From, To, Cc, Bcc, subject, body, and composed time in JSON. Show them **in
full inline** when requesting content approval. A file link or summary does not
replace the preview. Mention the selected method, mode, blockers, and that Gmail
creation saves an unsent draft in the named account. Record approval against the
exact payload hash using `email_payload_sha256` from the checker. Changes to any
header/body require another preview and invalidate content approval. Changed
candidate inputs also require a new step-entry confirmation and refreshed evidence.

## Connector draft or manual handoff

- **Gmail, live:** after sender and complete-content approval, preview the exact
  account-scoped draft lookup/read and obtain read approval. Check for an existing
  draft for this release, candidate, and message purpose before any first creation
  or retry. Compare full sender/recipients/content. Reuse a verified match; preserve
  human edits and resolve differences. If the lookup cannot establish presence or
  absence, stop before creating a remote draft and explain the limitation; use
  the manual fallback only if there is no unresolved earlier draft-write outcome.
  Save the `resource_check`. For verified absence, preview the exact
  available connector draft-create tool and arguments, including account and From,
  and obtain external-write confirmation. This can share the content review when
  the same preview includes all those details. Save an operation with
  `inputs.payload_sha256` and `inputs.account_address`. Invoke only the connector's
  draft-create action; never a send, reply, or send-draft action. Save the returned
  draft ID and account immediately and mark `gmail_draft_created`. A message ID
  alone or successful content preparation is not evidence of draft creation.
- **No usable Gmail connector, live:** display the complete approved subject and
  body with the confirmed sender and recipients, and ask the release manager to
  send it manually. Mark `manual_email_prepared`. This is a handoff, not evidence
  that mail was sent. Do not make installation a prerequisite.
- **Dry-run:** use the same sender and content checkpoints. Prepare local content
  only; an approved Gmail draft operation is `simulated` with result null. Leave
  `email.draft` null and mark `dry_run_email_prepared`. Explain that manual sending
  would be the manager's next action in a live run; do not ask them to send the
  rehearsal. Any sample artifact/image evidence must be explicitly authorized and
  labeled simulated; placeholders still require resolution before completion.
- **Uncertain connector result:** save `email_draft_uncertain` and the operation's
  uncertain result. Reconcile through approved draft reads in that same account
  before retrying. On resume, reuse a confirmed matching draft ID; do not create
  duplicates or overwrite human edits. If reconciliation is unavailable, keep
  the uncertain state and show the local content while explaining a draft may
  already exist. Do not claim a clean manual completion.

Stop after the draft or handoff. Keep send/vote-start timestamps unset. The next
defined step is [the manager vote checkpoint and result drafting](voting.md);
confirm entry and record when the manager sent the vote email. Sending remains
outside this procedure.

For a vote result, reuse this procedure only after the voting procedure's passage
checkpoint, with its result template instead of the opening-vote template. Store
the separate draft in `result_email` with its own `status` and a step-5
`entry_confirmation` dated after passage confirmation. Confirm the sender for
this result message before composing; a prior approval may be reused only if it
explicitly covers the result email too. Record that scope in history. Keep its
external operations at `step: 5`; leave the opening `email` object unchanged.

## Email state

Keep `email: null` before step 4. Initialize this object only after entry approval:

```json
{
  "entry_confirmation": {
    "by": "MANAGER",
    "at": "RFC3339",
    "mode": "dry-run",
    "simulated": true,
    "target_step": 4,
    "candidate_tag": "ACTUAL_CANDIDATE_TAG",
    "prepared_commit": "ACTUAL_PREPARED_COMMIT"
  },
  "connection": {
    "status": "unverified",
    "checked_at": null,
    "account_address": null,
    "can_create_draft": false,
    "verified_from": null
  },
  "sender": { "address": null, "confirmation": null },
  "to": ["dev@kvrocks.apache.org"],
  "cc": [],
  "bcc": [],
  "subject": null,
  "body": null,
  "composed_at": null,
  "artifact_review": null,
  "blockers": [],
  "content_approval": null,
  "method": null,
  "draft_operation_id": null,
  "draft": null,
  "completed_at": null
}
```

Connection status is `connected`, `unavailable`, or `unverified`; record the reason
in history without claiming a missing tool proves the account is disconnected.
Use `method: gmail` only with verified draft support for the selected sender;
otherwise `manual`. An artifact review records `candidate_tag`, `prepared_commit`,
`source_url`, `keys_url`, `checked_at`, `mode`, and `simulated`, with read/fixture
evidence in history and external operations. Content approval stores
`{by, at, mode, payload_sha256}`. A real draft stores
`{id, account_address, from, created_at}`; never populate it with a simulated ID.
The external operation result includes `draft_id` when confirmed successful.

Step-4 statuses are `awaiting_email_sender`, `awaiting_email_review`,
`email_draft_uncertain`, `gmail_draft_created`, `manual_email_prepared`, and
`dry_run_email_prepared`. Preserve all earlier step evidence. Save material
decisions and pending actions in history/next_action; run the checker after saving.
