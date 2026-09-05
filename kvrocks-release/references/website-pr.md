# Step 7: Create a PR to update website release links

The [release guide](https://kvrocks.apache.org/community/create-a-release/#update-website-links)
points to `src/components/Releases/index.tsx` in **`apache/kvrocks-website`**.
This is a separate repository from `apache/kvrocks`. Read this procedure when
entering or resuming step 7; authoring it does not advance a release.

## Enter and inspect

1. Read the complete release JSON and run the checker. Require completed step 6,
   including the manager's GitHub release-note confirmation, in the current mode.
   Show the release version, final tag/commit, published artifact evidence, website
   repository, and mode, then confirm entry. Preserve all previous approvals and
   `publication`; save `website.previous_status` and `website.entry_confirmation`.
   Set `step: 7`, `status: preparing_website_pr` only after this confirmation.
2. Inspect an available website checkout locally, including its instructions,
   remotes, worktree status, release data, build scripts, and workflows. Local
   inspection does not establish the current upstream branch or file contents.
   Prepare and confirm remote reads/fetches of the exact website repository,
   default branch, release data, existing matching PRs, and final public links.
   A failed duplicate lookup does not establish that no PR exists.
3. Use an isolated checkout/worktree based on the verified upstream base SHA.
   Keep other user changes intact. Record the base repository/branch/SHA and the
   intended head repository/branch. Use `codex/release-VERSION-website` unless the
   manager specifies a name. Reuse an existing matching branch or PR on resume.
   A fork must be identified and its creation separately confirmed if necessary;
   do not silently create a fork, push to an unrelated remote, or push to `main`.

In dry-run, approved remote reads may run, or explicitly authorized local fixtures
may supply simulated evidence. Keep fork creation, pushes, and PR creation
simulated. No remote-capable command is run solely to test its dry-run flag.

## Prepare the change and verify it

The inspected release-data format has a `versions` array with `{version, vtag}`
entries. For a modern release, both values are `VERSION` without a leading `v`.
The rendering helper adds `v` to the GitHub tag link itself. Inspect the actual
file before editing; do not add an RC, double the `v` prefix, or mistake the
controller's `kvrocks-controller.tsx` for the Kvrocks release data.

Add exactly one entry in the current descending release order, preserving older
versions, incubating suffixes, and the rendering code. If the same release already
exists with correct links, do not create an empty or duplicate PR. Resume its
existing PR, or record a verified `website_already_updated` outcome if the change
is already on the base branch. Resolve a conflicting entry with the manager.

Derive and review all four generated links from the actual renderer. The inspected
format produces:

```text
https://www.apache.org/dyn/closer.lua/kvrocks/VERSION/apache-kvrocks-VERSION-src.tar.gz
https://downloads.apache.org/kvrocks/VERSION/apache-kvrocks-VERSION-src.tar.gz.sha512
https://downloads.apache.org/kvrocks/VERSION/apache-kvrocks-VERSION-src.tar.gz.asc
https://github.com/apache/kvrocks/releases/tag/vVERSION
```

Use the published archive basename and final tag from the release record. Under
approved reads, check that the public links resolve to this release; successful
SVN promotion alone does not prove the download mirrors have synchronized. If
unavailable or mismatched, preserve the patch and record the blocker. A dry-run
may use explicitly authorized simulated link results; never claim live checks.

Format the touched file according to repository instructions, inspect the scoped
diff, and run the applicable local checks. The inspected checkout provides
`yarn typecheck` and `yarn build`; verify current scripts/runtime requirements
before using them. Inspect scripts for external effects. Dependency downloads
need a confirmed operation; prefer available dependencies. Save check commands,
results, and times; report failures or unavailable checks instead of claiming
success. Do not run a deploy script. For this data entry, verify the resulting
row and four links; do not add tests that only duplicate the entry's literal text.

## Confirm push and PR creation

Finish local preparation before asking for external-write approval. Save the
patch, local website commit, and PR content in the version's state directory.
Use a focused commit such as `docs(releases): add Apache Kvrocks VERSION`.
Show the complete diff, validation results, base/head repositories and branches,
exact website commit SHA, mode, PR title, full body, and draft/ready choice.
The website commit is different from the voted Kvrocks source commit.

Example title: `docs: add Apache Kvrocks VERSION release links`. The body should
state that the release becomes available on the releases page, link to the final
GitHub release, and list the actual validation. Do not claim the PR is merged or
the website is deployed. Create a ready-for-review PR by default; retain any
manager-selected draft setting in the approved payload.

Preview the push destination/refspec and exact new commit, plus the PR API/CLI
request. The two writes may share one explicitly enumerated approval, but each
gets its own operation record and outcome. Include workflow effects: the inspected
website workflow builds PRs and deploys a push to `main` to `asf-site`; recheck the
current workflow when preparing a live operation. Do not enable auto-merge,
request reviewers, post comments, merge, or deploy as part of this step.

After live push approval, push only the prepared website branch and verify its
remote SHA under the approved read scope. After PR approval, create the PR with
explicit base/head and the reviewed title/body. Prefer a structured connector
request; with `gh pr create`, use a local `--body-file` and explicit `--repo`,
`--base`, and `--head` to avoid implicit pushes or the wrong repository. Save the
returned PR URL/number and verify repository, head SHA, base, and payload.

On resume, keep a verified push and continue the uncompleted PR operation. If a
push or create response is ambiguous, record `website_push_uncertain` or
`website_pr_uncertain` and reconcile through approved reads before retrying.
Reuse an existing matching PR instead of opening another. Changed diff, commits,
destinations, or PR content require review of the changed scope; PR-body-only
changes do not invalidate an unchanged push approval.

In dry-run, save the approved local patch and PR text, simulate both operations,
leave the real `pr` null, and use `dry_run_website_pr_prepared`. Do not manufacture
a GitHub URL. In live mode, use `website_pr_created` after verified creation or
resumption of a matching PR. Show the PR link and pending human review, then
confirm entry to [the final announcement handoff](announcement.md).
PR creation is the end of this step, not evidence of merge or deployment.

## JSON state

Keep `website` null before entry. On entry, initialize:

```json
{
  "previous_status": "ACTUAL_STEP_6_OUTCOME",
  "repository": "apache/kvrocks-website",
  "file": "src/components/Releases/index.tsx",
  "entry_confirmation": {
    "by": "MANAGER",
    "at": "RFC3339",
    "mode": "dry-run",
    "simulated": true,
    "target_step": 7,
    "version": "VERSION",
    "publication_sha256": "HASH_OF_COMPLETED_PUBLICATION_OBJECT"
  },
  "checkout_path": null,
  "plan": null,
  "push_operation_id": null,
  "pr_operation_id": null,
  "pr": null,
  "existing_update": null,
  "completed_at": null
}
```

Bind entry using `publication_plan_sha256(state["publication"])` from the checker.
Top-level statuses are `preparing_website_pr`, `awaiting_website_pr_review`,
`website_pr_blocked`, `website_push_uncertain`, `website_pr_uncertain`,
`website_pr_created`, `dry_run_website_pr_prepared`, and `website_already_updated`.

- `plan` stores `mode`, `simulated`, `prepared_at`, `evidence_source` for fixtures,
  `base_branch`, `base_commit`, `head_repository`, `head_branch`, `head_commit`,
  `files`, full `diff`, `title`, `body`, `draft` (boolean), `links` (archive,
  checksum, signature, github), `link_check` (`status`, `at`, `mode`, `simulated`),
  `checks` (command, status, at), and `blockers`. The website `head_commit` is the
  local commit containing the reviewed patch; use real local evidence when
  available, and clearly label authorized simulated preparation.
- Push operations bind `inputs.payload_sha256` to `website_push_sha256(plan)`;
  PR operations bind it to `website_pr_sha256(plan)`. Record the exact request,
  target repository, approval `{by, at, mode}`, and mode as usual. Live push
  results contain `repository`, `branch`, `commit`, `verified_at`. PR results
  contain `repository`, `number`, `url`, `base_branch`, `head_repository`,
  `head_branch`, `head_commit`, `title`, `body`, `draft`, and `verified_at`.
  Store the PR result in both `website.pr` and the operation result. Existing
  PRs use an approved `kind: read` operation for matching-PR verification; the
  verified push evidence can also come from an approved read.
- Completed dry-run operations are `simulated` with null remote results. Live
  operations are `succeeded`. Preserve partial receipts/history immediately;
  do not mark the step complete from an unverified or uncertain response.
- `existing_update`, used only when the base branch already contains the correct
  entry, records `repository`, `base_branch`, `base_commit`, `version`, `file`,
  `links`, `verified_at`, `mode`, `simulated`, and `operation_id` pointing to the
  approved read. Live verification uses actual results; a dry-run existing-entry
  outcome must be labeled simulated. No push or PR operation is needed.

Set `completed_at` only for a verified live outcome or completed simulation. Save
the pending action and every material decision in the same per-version JSON.
The read-only checker validates consistency; it cannot prove a remote operation
or human approval happened and never creates a PR.
