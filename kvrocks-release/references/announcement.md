# Step 8: Hand off the announcement and finish

This is the final step. Follow the recipients and sender requirement in the
[announcement section of the release guide](https://kvrocks.apache.org/community/create-a-release/#send-the-announcement):
the release manager sends to `dev@kvrocks.apache.org`, Cc `announce@apache.org`,
from an `@apache.org` address.

## Enter and hand off

Read the full release JSON and run the checker. Require a completed website PR
step (`website_pr_created`, `dry_run_website_pr_prepared`, or
`website_already_updated`) and its preserved publication evidence. A created PR
does not mean merged or deployed; describe its actual state without adding an
automatic merge or deployment action. Show the version, final release tag/link,
website outcome, mode, and final manual action, then confirm entry to step 8.

Save `announcement.previous_status` and a separate `entry_confirmation` bound to
the version and completed website state. Set `step: 8` and
`preparing_announcement_handoff`. Keep earlier emails, approvals, and publication
results intact.

In live mode, ask the release manager in this conversation:

> Please send the Apache Kvrocks VERSION release announcement to
> dev@kvrocks.apache.org and Cc announce@apache.org using your Apache email
> address. Include the final GitHub release notes and public download links.
> Please confirm here once you have sent it.

Replace VERSION and show the concrete final release-note and download links from
the saved release evidence. This text is an instruction to the manager, not an
email draft. Use links already verified in the earlier steps; if their status is
uncertain, explain it and resolve the specific issue before requesting a send.
New GitHub status checks need no approval; other external verification still
requires its concrete approved read scope under `SKILL.md`.

Do not send an email, create a Gmail draft, or contact anyone else as part of this
handoff. If the manager asks for help drafting, first confirm the exact From
address, then show the subject, full headers/body, and real release links for
review under the existing email rules. Do not assume the connected Gmail account
is the Apache sender or invent release highlights. Sending remains manual.

For dry-run, explicitly replace the live request with a **simulated announcement
handoff** showing the same recipients and sender requirement. Ask the manager to
acknowledge the rehearsal only; do not ask them to send a real announcement.

## Record completion and offer local cleanup

Save the complete handoff and `awaiting_announcement_sent`. Asking, preparing a
draft, silence, or an unclear answer does not mean sent. The manager's explicit
report that they sent this announcement is sufficient in live mode; do not
require a mailbox lookup, archive URL, or exact send time. Record the confirmation
time and any voluntarily supplied sending evidence, identifying it as
manager-reported. In dry-run, accept an explicit rehearsal acknowledgment only.

After that confirmation, set `release_complete` in live mode or
`dry_run_release_complete` in dry-run, record `announcement.completed_at`, clear
`next_action` to null, and append the terminal decision to history. The requested
process is done. Report completion in the recorded mode, then follow
[the optional local artifact cleanup offer](local-cleanup.md): inspect and show
the exact removal list and ask the manager before deleting anything. Keep the
release terminal while cleanup is pending or declined. Dry-run simulates removal.
On later invocations, validate and report the terminal state and saved cleanup
outcome without repeating the announcement or a completed/declined cleanup offer.
Do not add merge/deployment, announcement monitoring, or other release steps.

## JSON state

Keep `announcement` null before entry. On entry use:

```json
{
  "previous_status": "ACTUAL_STEP_7_OUTCOME",
  "entry_confirmation": {
    "by": "MANAGER",
    "at": "RFC3339",
    "mode": "dry-run",
    "simulated": true,
    "target_step": 8,
    "version": "VERSION",
    "website_sha256": "HASH_OF_COMPLETED_WEBSITE_OBJECT"
  },
  "handoff": null,
  "send_confirmation": null,
  "completed_at": null
}
```

Use `publication_plan_sha256(state["website"])` to bind entry. `handoff` stores
`at`, `mode`, `simulated`, `version`, `to: ["dev@kvrocks.apache.org"]`,
`cc: ["announce@apache.org"]`, `from_domain: "apache.org"`, the four release
`links` from `website.plan.links` or `website.existing_update.links`, and the full
handoff `content`. Keep email content separate if the manager later requests it.

`send_confirmation` records `by`, `at`, `mode`, `simulated`, `version`,
`handoff_sha256` (using `publication_plan_sha256(handoff)`), and `outcome`:
`sent` in live mode or `simulated` in dry-run. Optional `sent_at` and `message_url`
default to null; use actual manager-supplied evidence only in live mode. Dry-run
keeps both null. `completed_at` follows the manager's confirmation time.

Preserve superseded handoffs and confirmations in history. A changed version,
recipient, release link, or handoff invalidates its previous confirmation. The
checker validates the record without sending or inspecting email; it cannot
independently prove delivery.
