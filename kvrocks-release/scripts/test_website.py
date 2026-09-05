import copy
import json
import unittest

import test_publication as fixtures
from check_state import (
    WEBSITE_FILE,
    WEBSITE_REPOSITORY,
    inspect_record,
    instant,
    publication_plan_sha256,
    website_pr_sha256,
    website_push_sha256,
    website_release_links,
)


class WebsiteTest(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PublicationTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.now = instant("2030-01-05T12:00:00Z")

    def check(self, state):
        self.path.write_text(json.dumps(state))
        before = self.path.read_bytes()
        result = inspect_record(self.path, self.now)
        self.assertEqual(before, self.path.read_bytes())
        return result

    def state(self, mode="dry-run", prepared=False, complete=False):
        state = self.fixture.handoff(mode, complete=True)
        website = {
            "previous_status": state["status"],
            "repository": WEBSITE_REPOSITORY,
            "file": WEBSITE_FILE,
            "entry_confirmation": dict(
                self.fixture.confirmation(mode, "2030-01-05T11:10:00Z"),
                target_step=7,
                version="9.9.0",
                publication_sha256=publication_plan_sha256(state["publication"]),
            ),
            "checkout_path": None,
            "plan": None,
            "push_operation_id": None,
            "pr_operation_id": None,
            "pr": None,
            "existing_update": None,
            "completed_at": None,
        }
        state.update(step=7, status="preparing_website_pr", website=website)
        if not prepared:
            return state
        plan = {
            "mode": mode,
            "simulated": mode == "dry-run",
            "prepared_at": "2030-01-05T11:20:00Z",
            "evidence_source": "Authorized isolated website fixture"
            if mode == "dry-run"
            else None,
            "base_branch": "main",
            "base_commit": "d" * 40,
            "head_repository": "test-manager/kvrocks-website",
            "head_branch": "codex/release-9.9.0-website",
            "head_commit": "e" * 40,
            "files": [WEBSITE_FILE],
            "diff": f"diff --git a/{WEBSITE_FILE} b/{WEBSITE_FILE}\n--- a/{WEBSITE_FILE}\n+++ b/{WEBSITE_FILE}\n@@ -1 +1,2 @@\n const versions = [\n+    {{version: '9.9.0', vtag: '9.9.0'}},\n",
            "title": "docs: add Apache Kvrocks 9.9.0 release links",
            "body": "Adds the published 9.9.0 release to the release table. Validation: typecheck and build passed.",
            "draft": False,
            "links": website_release_links("9.9.0"),
            "link_check": {
                "status": "passed",
                "at": "2030-01-05T11:18:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
            },
            "checks": [
                {"command": command, "status": "passed", "at": "2030-01-05T11:19:00Z"}
                for command in ("yarn typecheck", "yarn build")
            ],
            "blockers": [],
        }
        website["plan"] = plan
        state["status"] = "awaiting_website_pr_review"
        if not complete:
            return state
        website.update(
            push_operation_id="website-push",
            pr_operation_id="website-pr",
            completed_at="2030-01-05T11:25:00Z",
        )
        push_result = {
            "repository": plan["head_repository"],
            "branch": plan["head_branch"],
            "commit": plan["head_commit"],
            "verified_at": "2030-01-05T11:22:00Z",
        }
        pr_result = {
            key: plan[key]
            for key in (
                "base_branch",
                "head_repository",
                "head_branch",
                "head_commit",
                "title",
                "body",
                "draft",
            )
        }
        pr_result.update(
            repository=WEBSITE_REPOSITORY,
            number=99999,
            url=f"https://github.com/{WEBSITE_REPOSITORY}/pull/99999",
            verified_at="2030-01-05T11:24:00Z",
        )
        for op_id, target, payload_hash, result in (
            (
                "website-push",
                plan["head_repository"],
                website_push_sha256(plan),
                push_result,
            ),
            ("website-pr", WEBSITE_REPOSITORY, website_pr_sha256(plan), pr_result),
        ):
            state["external_operations"].append(
                {
                    "id": op_id,
                    "step": 7,
                    "mode": mode,
                    "kind": "write",
                    "target": target,
                    "request": {"fixture_operation": op_id},
                    "inputs": {"payload_sha256": payload_hash},
                    "approval": self.fixture.confirmation(mode, "2030-01-05T11:21:00Z"),
                    "status": "simulated" if mode == "dry-run" else "succeeded",
                    "result": None if mode == "dry-run" else copy.deepcopy(result),
                }
            )
        if mode == "live":
            website["pr"] = pr_result
        state["status"] = (
            "dry_run_website_pr_prepared" if mode == "dry-run" else "website_pr_created"
        )
        return state

    def test_entry_preserves_publication_and_needs_no_remote_mutation(self):
        state = self.state()
        self.assertEqual(self.check(state)["vote_evaluation"]["gate"], "passed")
        self.assertIsNone(state["website"]["plan"])

    def test_cannot_skip_publication_or_manual_github_notes_confirmation(self):
        for variant in ("incomplete", "notes", "entry", "clock", "snapshot"):
            with self.subTest(variant=variant):
                state = self.state()
                if variant == "incomplete":
                    state["website"]["previous_status"] = "publishing_release"
                elif variant == "notes":
                    state["publication"]["github_release_notes"]["confirmation"] = None
                elif variant == "entry":
                    state["website"]["entry_confirmation"]["target_step"] = 6
                elif variant == "clock":
                    state["website"]["entry_confirmation"]["at"] = (
                        "2030-01-05T11:05:00Z"
                    )
                else:
                    state["website"]["entry_confirmation"]["publication_sha256"] = (
                        "0" * 64
                    )
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_website_repository_file_final_links_and_feature_branch_are_bound(self):
        for variant in ("repo", "file", "rc", "prefix", "branch"):
            with self.subTest(variant=variant):
                state = self.state(prepared=True)
                website = state["website"]
                if variant == "repo":
                    website["repository"] = "apache/kvrocks"
                elif variant == "file":
                    website["plan"]["files"] = [
                        "src/components/Releases/kvrocks-controller.tsx"
                    ]
                elif variant == "rc":
                    website["plan"]["links"]["archive"] += "-rc1"
                elif variant == "prefix":
                    website["plan"]["links"]["github"] = (
                        "https://github.com/apache/kvrocks/releases/tag/vv9.9.0"
                    )
                else:
                    website["plan"]["head_branch"] = "main"
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_prepared_pr_requires_separate_push_and_pr_approvals(self):
        state = self.state(prepared=True)
        self.check(state)
        state["status"] = "dry_run_website_pr_prepared"
        with self.assertRaises(ValueError):
            self.check(state)
        for index in (-1, -2):
            state = self.state(prepared=True, complete=True)
            state["external_operations"][index]["approval"] = None
            with self.assertRaises(ValueError):
                self.check(state)

    def test_dry_run_and_live_completion_keep_distinct_remote_results(self):
        for mode in ("dry-run", "live"):
            with self.subTest(mode=mode):
                state = self.state(mode, prepared=True, complete=True)
                self.check(state)
                if mode == "dry-run":
                    state["website"]["pr"] = {
                        "url": "https://github.com/apache/kvrocks-website/pull/99999"
                    }
                else:
                    state["external_operations"][-2]["result"]["commit"] = "f" * 40
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_missing_failed_or_simulated_live_link_validation_blocks_completion(self):
        for variant in ("missing", "checks", "links", "blocker", "simulated"):
            with self.subTest(variant=variant):
                state = self.state("live", prepared=True, complete=True)
                plan = state["website"]["plan"]
                if variant == "missing":
                    plan["checks"] = []
                elif variant == "checks":
                    plan["checks"][0]["status"] = "failed"
                elif variant == "links":
                    plan["link_check"]["status"] = "unavailable"
                elif variant == "blocker":
                    plan["blockers"] = ["Mirror has not synchronized"]
                else:
                    plan["link_check"]["simulated"] = True
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_changed_pr_body_needs_new_pr_approval_but_preserves_push_scope(self):
        state = self.state(prepared=True, complete=True)
        plan = state["website"]["plan"]
        push_hash = website_push_sha256(plan)
        plan["body"] += " Updated reviewer context."
        self.assertEqual(website_push_sha256(plan), push_hash)
        with self.assertRaises(ValueError):
            self.check(state)
        state["external_operations"][-1]["inputs"]["payload_sha256"] = (
            website_pr_sha256(plan)
        )
        self.check(state)

    def test_changed_diff_or_website_commit_invalidates_push_approval(self):
        for key, value in (("diff", "Changed patch"), ("head_commit", "f" * 40)):
            with self.subTest(key=key):
                state = self.state(prepared=True, complete=True)
                state["website"]["plan"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_partial_push_and_uncertain_pr_do_not_claim_completion(self):
        state = self.state("live", prepared=True, complete=True)
        website = state["website"]
        website.update(pr=None, completed_at=None)
        state["external_operations"][-1].update(status="uncertain", result=None)
        state["status"] = "website_pr_uncertain"
        self.check(state)
        self.assertEqual(state["external_operations"][-2]["status"], "succeeded")
        state["status"] = "website_pr_created"
        with self.assertRaises(ValueError):
            self.check(state)

    def test_live_pr_response_must_match_repo_head_and_reviewed_payload(self):
        for key, value in (
            ("repository", "apache/kvrocks"),
            ("head_commit", "f" * 40),
            ("base_branch", "asf-site"),
            ("title", "Unapproved title"),
            ("draft", True),
            ("url", "https://github.com/apache/kvrocks/pull/99999"),
        ):
            with self.subTest(key=key):
                state = self.state("live", prepared=True, complete=True)
                state["website"]["pr"][key] = value
                state["external_operations"][-1]["result"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_existing_matching_pr_can_resume_via_approved_reads(self):
        state = self.state("live", prepared=True, complete=True)
        for op in state["external_operations"][-2:]:
            op["kind"] = "read"
            op["approval"]["at"] = "2030-01-05T11:15:00Z"
        self.check(state)

    def test_diff_cannot_hide_an_unrelated_controller_change(self):
        state = self.state(prepared=True)
        state["website"]["plan"]["diff"] = state["website"]["plan"]["diff"].replace(
            WEBSITE_FILE, "src/components/Releases/kvrocks-controller.tsx"
        )
        with self.assertRaises(ValueError):
            self.check(state)

    def test_already_listed_release_requires_verification_without_empty_pr(self):
        for mode in ("dry-run", "live"):
            with self.subTest(mode=mode):
                state = self.state(mode)
                existing = {
                    "repository": WEBSITE_REPOSITORY,
                    "file": WEBSITE_FILE,
                    "version": "9.9.0",
                    "base_branch": "main",
                    "base_commit": "d" * 40,
                    "links": website_release_links("9.9.0"),
                    "mode": mode,
                    "simulated": mode == "dry-run",
                    "verified_at": "2030-01-05T11:15:00Z",
                    "operation_id": "website-existing",
                }
                state["website"].update(
                    existing_update=existing, completed_at="2030-01-05T11:16:00Z"
                )
                state["external_operations"].append(
                    {
                        "id": "website-existing",
                        "step": 7,
                        "mode": mode,
                        "kind": "read",
                        "target": WEBSITE_REPOSITORY,
                        "request": {
                            "fixture_read": "base release entry and public links"
                        },
                        "inputs": {"payload_sha256": publication_plan_sha256(existing)},
                        "approval": self.fixture.confirmation(
                            mode, "2030-01-05T11:11:00Z"
                        ),
                        "status": "simulated" if mode == "dry-run" else "succeeded",
                        "result": None
                        if mode == "dry-run"
                        else copy.deepcopy(existing),
                    }
                )
                state["status"] = "website_already_updated"
                self.check(state)
                state["external_operations"][-1]["approval"] = None
                with self.assertRaises(ValueError):
                    self.check(state)


if __name__ == "__main__":
    unittest.main()
