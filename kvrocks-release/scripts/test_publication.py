import copy
import json
import unittest

import test_voting as fixtures
from check_state import (
    inspect_record,
    instant,
    publication_plan_sha256,
    vote_snapshot_sha256,
)


class PublicationTest(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.VotingTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.now = instant("2030-01-05T12:00:00Z")

    def check(self, state):
        self.path.write_text(json.dumps(state))
        before = self.path.read_bytes()
        result = inspect_record(self.path, self.now)
        self.assertEqual(self.path.read_bytes(), before)
        return result

    def confirmation(self, mode, at):
        return {
            "by": "Test release manager",
            "at": at,
            "mode": mode,
            "simulated": mode == "dry-run",
        }

    def component(self, **kwargs):
        return dict(
            status="pending",
            plan=None,
            operation_id=None,
            result=None,
            completed_at=None,
            **kwargs,
        )

    def state(self, mode="dry-run"):
        state = self.fixture.result_state(mode, complete=True)
        archive = "apache-kvrocks-9.9.0-src.tar.gz"
        state["source_release"]["artifacts"] = [
            {
                "path": "/tmp/" + archive + suffix,
                "sha512": str(i) * 128,
                "size": i,
                "status": "simulated" if mode == "dry-run" else "actual",
            }
            for i, suffix in enumerate(("", ".asc", ".sha512"), 1)
        ]
        state["publication"] = {
            "previous_status": state["status"],
            "entry_confirmation": dict(
                self.confirmation(mode, "2030-01-05T10:40:00Z"),
                target_step=6,
                candidate_tag="v9.9.0-rc1",
                prepared_commit="b" * 40,
                vote_snapshot_sha256=vote_snapshot_sha256(state["vote"]),
                docker_digest=state["docker"]["image"]["digest"],
            ),
            "svn": self.component(),
            "docker": {
                "targets": [
                    self.component(ref="apache/kvrocks:9.9.0"),
                    self.component(ref="apache/kvrocks:latest"),
                ]
            },
            "github_release_notes": {
                "status": "pending",
                "handoff": None,
                "confirmation": None,
            },
            "completed_at": None,
        }
        state.update(step=6, status="preparing_publication")
        return state

    def publish(self, state, *, svn=False, index=0, already=False):
        mode = state["mode"]
        component = (
            state["publication"]["svn"]
            if svn
            else state["publication"]["docker"]["targets"][index]
        )
        minute = 41 if svn else 46 + index * 5
        at = lambda offset: f"2030-01-05T10:{minute + offset:02d}:00Z"
        plan = {
            "mode": mode,
            "simulated": mode == "dry-run",
            "checked_at": at(0),
            "evidence_source": "manager-authorized local fixture"
            if mode == "dry-run"
            else None,
        }
        if svn:
            files = [
                {"name": item["path"].rsplit("/", 1)[1], "sha512": item["sha512"]}
                for item in state["source_release"]["artifacts"]
            ]
            source = "https://dist.apache.org/repos/dist/dev/kvrocks/9.9.0"
            target = "https://dist.apache.org/repos/dist/release/kvrocks/9.9.0"
            plan.update(
                source_url=source,
                destination_url=target,
                source_revision=100,
                files=files,
                destination_before="matching" if already else "absent",
            )
            argv = [
                "svnmucc",
                "--revision",
                "100",
                "--message",
                "Release 9.9.0",
                "mv",
                source,
                target,
            ]
            result = {
                "revision": 101,
                "files": copy.deepcopy(files),
                "source_absent": not already,
                "verified_at": at(2),
            }
        else:
            target = component["ref"]
            digest = state["docker"]["image"]["digest"]
            source_ref = "apache/kvrocks@" + digest
            plan.update(
                source_ref=source_ref,
                target_ref=target,
                previous_digest=digest if already else None,
            )
            argv = [
                "docker",
                "buildx",
                "imagetools",
                "create",
                "--tag",
                target,
                source_ref,
            ]
            result = {
                "ref": target,
                "digest": digest,
                "platforms": ["linux/amd64", "linux/arm64"],
                "verified_at": at(2),
            }
        if mode == "dry-run":
            result = None
        operation = {
            "id": "publish-" + target,
            "step": 6,
            "mode": mode,
            "kind": "read" if already else "write",
            "target": target,
            "request": {"verification": target} if already else {"argv": argv},
            "inputs": {"plan_sha256": publication_plan_sha256(plan)},
            "approval": self.confirmation(mode, at(1)),
            "status": "simulated" if mode == "dry-run" else "succeeded",
            "result": copy.deepcopy(result),
        }
        state["external_operations"].append(operation)
        component.update(
            status="simulated"
            if mode == "dry-run"
            else "already_published"
            if already
            else "published",
            plan=plan,
            operation_id=operation["id"],
            result=result,
            completed_at=at(3),
        )
        state["status"] = "publishing_release"
        return component, operation

    def ready(self, mode="dry-run"):
        state = self.state(mode)
        self.publish(state, svn=True)
        self.publish(state, index=0)
        self.publish(state, index=1)
        return state

    def handoff(self, mode="dry-run", complete=False):
        state = self.ready(mode)
        notes = state["publication"]["github_release_notes"]
        notes.update(
            status="awaiting_manager",
            handoff={
                "content": "Test fixture manual handoff for apache/kvrocks 9.9.0.",
                "at": "2030-01-05T11:00:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
                "tag": "v9.9.0",
                "commit": "b" * 40,
            },
        )
        state["status"] = "awaiting_github_release_notes"
        if complete:
            notes.update(
                status="simulated" if mode == "dry-run" else "published",
                confirmation=dict(
                    self.confirmation(mode, "2030-01-05T11:05:00Z"),
                    completed=True,
                    tag="v9.9.0",
                    commit="b" * 40,
                    url=None
                    if mode == "dry-run"
                    else "https://github.com/apache/kvrocks/releases/tag/v9.9.0",
                ),
            )
            state["publication"]["completed_at"] = "2030-01-05T11:06:00Z"
            state["status"] = (
                "dry_run_publication_complete"
                if mode == "dry-run"
                else "publication_complete"
            )
        return state

    def test_entry_preserves_vote_and_result_without_archive_checks(self):
        state = self.state()
        result = self.check(state)
        self.assertEqual(result["vote_evaluation"]["gate"], "passed")
        self.assertEqual(result["state"]["step"], 6)
        self.assertEqual(result["state"]["external_operations"], [])

    def test_missing_early_or_changed_vote_and_incomplete_result_block_entry(self):
        for variant in ("missing", "no", "early", "changed", "result"):
            with self.subTest(variant=variant):
                state = self.state()
                if variant == "missing":
                    state["vote"]["outcome_confirmation"] = None
                elif variant == "no":
                    state["vote"]["outcome_confirmation"]["passed"] = False
                elif variant == "early":
                    state["vote"]["outcome_confirmation"]["at"] = "2030-01-05T10:29:59Z"
                elif variant == "changed":
                    state["vote"]["outcome_confirmation"]["by"] = "Different manager"
                else:
                    state["result_email"]["status"] = "awaiting_email_review"
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_entry_is_separate_and_bound_to_candidate_vote_and_mode(self):
        for key, value in (
            ("target_step", 5),
            ("prepared_commit", "c" * 40),
            ("mode", "live"),
            ("simulated", False),
            ("vote_snapshot_sha256", "x" * 64),
            ("docker_digest", "sha256:" + "2" * 64),
            ("at", "2030-01-05T10:38:00Z"),
        ):
            with self.subTest(key=key):
                state = self.state()
                state["publication"]["entry_confirmation"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_live_and_dry_run_complete_only_after_manual_confirmation(self):
        for mode in ("dry-run", "live"):
            with self.subTest(mode=mode):
                state = self.handoff(mode, complete=True)
                self.assertEqual(self.check(state)["state"]["status"], state["status"])
                state["publication"]["github_release_notes"]["confirmation"] = None
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_dry_run_cannot_claim_remote_results_or_real_github_url(self):
        for variant in ("svn", "docker", "url", "mode"):
            with self.subTest(variant=variant):
                state = self.handoff(complete=True)
                if variant == "svn":
                    state["publication"]["svn"]["result"] = {"revision": 101}
                elif variant == "docker":
                    state["publication"]["docker"]["targets"][0]["result"] = {
                        "digest": "sha256:" + "1" * 64
                    }
                elif variant == "url":
                    state["publication"]["github_release_notes"]["confirmation"][
                        "url"
                    ] = "https://github.com/apache/kvrocks/releases/tag/v9.9.0"
                else:
                    state["status"] = "publication_complete"
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_changed_svn_files_directory_revision_or_plan_require_new_review(self):
        for variant in (
            "files",
            "directory",
            "revision",
            "operation",
            "argv",
            "approval",
        ):
            with self.subTest(variant=variant):
                state = self.state("live")
                component, operation = self.publish(state, svn=True)
                if variant == "files":
                    component["plan"]["files"][0]["sha512"] = "4" * 128
                elif variant == "directory":
                    component["plan"]["destination_url"] += "-rc1"
                elif variant == "revision":
                    component["plan"]["source_revision"] += 1
                elif variant == "operation":
                    operation["inputs"]["plan_sha256"] = "0" * 64
                elif variant == "argv":
                    operation["request"]["argv"][2] = "HEAD"
                else:
                    operation["approval"] = None
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_live_svn_checks_bytes_revision_and_source_disappearance(self):
        for key, value in (("files", []), ("revision", 100), ("source_absent", False)):
            with self.subTest(key=key):
                state = self.state("live")
                component, operation = self.publish(state, svn=True)
                component["result"][key] = value
                operation["result"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_matching_existing_svn_destination_needs_no_move_or_dev_deletion(self):
        state = self.state("live")
        component, operation = self.publish(state, svn=True, already=True)
        self.check(state)
        self.assertFalse(component["result"]["source_absent"])
        self.assertEqual(operation["kind"], "read")
        operation["kind"] = "write"
        with self.assertRaises(ValueError):
            self.check(state)

    def test_existing_destination_reuses_prior_approved_verification_read(self):
        state = self.state("live")
        component, operation = self.publish(state, svn=True, already=True)
        operation["approval"]["at"] = "2030-01-05T10:40:00Z"
        component["result"]["verified_at"] = component["plan"]["checked_at"]
        operation["result"] = copy.deepcopy(component["result"])
        self.check(state)

    def test_docker_cannot_precede_svn_publication(self):
        state = self.state()
        self.publish(state, index=0)
        with self.assertRaises(ValueError):
            self.check(state)

    def test_docker_rejects_moving_source_tag_or_conflicting_version_digest(self):
        for variant in ("source", "conflict", "target"):
            with self.subTest(variant=variant):
                state = self.ready("live")
                component = state["publication"]["docker"]["targets"][0]
                if variant == "source":
                    component["plan"]["source_ref"] = state["docker"]["image"]["ref"]
                elif variant == "conflict":
                    component["plan"]["previous_digest"] = "sha256:" + "2" * 64
                else:
                    component["ref"] = "apache/kvrocks:9.9.0-rc1"
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_live_docker_verifies_digest_and_platforms(self):
        for key, value in (
            ("digest", "sha256:" + "2" * 64),
            ("platforms", ["linux/amd64"]),
        ):
            with self.subTest(key=key):
                state = self.state("live")
                self.publish(state, svn=True)
                component, operation = self.publish(state, index=0)
                component["result"][key] = value
                operation["result"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_latest_change_requires_approval_of_its_previous_digest(self):
        state = self.state("live")
        self.publish(state, svn=True)
        self.publish(state, index=0)
        component, operation = self.publish(state, index=1)
        component["plan"]["previous_digest"] = "sha256:" + "2" * 64
        with self.assertRaises(ValueError):
            self.check(state)
        operation["inputs"]["plan_sha256"] = publication_plan_sha256(component["plan"])
        self.check(state)

    def test_already_published_docker_uses_read_verification(self):
        state = self.state("live")
        self.publish(state, svn=True)
        component, operation = self.publish(state, index=0, already=True)
        self.check(state)
        self.assertEqual(component["status"], "already_published")
        self.assertEqual(operation["kind"], "read")

    def test_partial_and_uncertain_outcomes_survive_without_claiming_completion(self):
        state = self.state("live")
        self.publish(state, svn=True)
        self.publish(state, index=0)
        component, operation = self.publish(state, index=1)
        component.update(status="uncertain", result=None, completed_at=None)
        operation.update(status="uncertain", result=None)
        state["status"] = "release_publication_uncertain"
        self.check(state)
        self.assertEqual(
            state["publication"]["docker"]["targets"][0]["status"], "published"
        )
        state["status"] = "publication_complete"
        with self.assertRaises(ValueError):
            self.check(state)

    def test_manual_handoff_is_not_publication_and_cannot_precede_images(self):
        state = self.handoff()
        self.check(state)
        state["status"] = "dry_run_publication_complete"
        with self.assertRaises(ValueError):
            self.check(state)
        state = self.handoff()
        state["publication"]["docker"]["targets"][1] = self.component(
            ref="apache/kvrocks:latest"
        )
        with self.assertRaises(ValueError):
            self.check(state)

    def test_github_report_must_match_final_tag_commit_mode_and_order(self):
        for key, value in (
            ("tag", "v9.9.0-rc1"),
            ("commit", "c" * 40),
            ("mode", "dry-run"),
            ("completed", False),
            ("at", "2030-01-05T10:59:00Z"),
            ("url", "https://github.com/example/kvrocks/releases/tag/v9.9.0"),
        ):
            with self.subTest(key=key):
                state = self.handoff("live", complete=True)
                state["publication"]["github_release_notes"]["confirmation"][key] = (
                    value
                )
                with self.assertRaises(ValueError):
                    self.check(state)


if __name__ == "__main__":
    unittest.main()
