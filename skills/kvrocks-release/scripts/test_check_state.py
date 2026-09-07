#!/usr/bin/env python3
"""Exercise the release deadline gate with isolated local records."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from check_state import (
    VERIFICATION_CHECKS,
    email_payload_sha256,
    inspect_record,
    publication_plan_sha256,
)


class CheckStateTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "release-9.9.0" / "release-state.json"
        self.path.parent.mkdir()
        self.state = {
            "schema_version": 1,
            "repository": "apache/kvrocks",
            "version": "9.9.0",
            "mode": "dry-run",
            "step": 1,
            "status": "dry_run_waiting",
            "proposed_commit": "a" * 40,
            "exclusions": [],
            "cherry_pick_deadline": "2030-01-02T10:00:00Z",
            "approval": {
                "by": "Test release manager",
                "at": "2030-01-01T10:00:00Z",
                "mode": "dry-run",
            },
            "discussion": {
                "draft_file": "discussion-draft.md",
                "url": None,
                "created_at": None,
                "simulated_at": "2030-01-01T10:01:00Z",
            },
            "history": [{"at": "2030-01-01T10:00:00Z", "details": "Preserve me."}],
            "notes": ["Test release"],
            "next_action": "Wait until the cherry-pick deadline.",
        }

    def write_record(self, state=None):
        self.path.write_text(
            json.dumps(self.state if state is None else state, indent=2) + "\n",
            encoding="utf-8",
        )

    def check_at(self, hour=9, minute=59, second=59):
        return inspect_record(
            self.path, datetime(2030, 1, 2, hour, minute, second, tzinfo=timezone.utc)
        )

    def test_blocks_before_deadline_without_modifying_record(self):
        self.write_record()
        before = self.path.read_bytes()
        result = self.check_at()
        self.assertEqual(result["deadline_gate"], "blocked")
        self.assertEqual(result["seconds_remaining"], 1)
        self.assertEqual(result["state"]["history"], self.state["history"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_documented_template_is_a_readable_pending_record(self):
        reference = Path(__file__).parents[1] / "references" / "release-record.md"
        template = reference.read_text().split("```json\n", 1)[1].split("\n```", 1)[0]
        self.path.write_text(template.replace("VERSION", "9.9.0"))
        result = self.check_at()
        self.assertEqual(result["state"]["status"], "awaiting_confirmation")
        self.assertIsNone(result["state"]["exclusions"])
        self.assertEqual(result["deadline_gate"], "blocked")

    def test_versions_have_independent_state_files(self):
        self.write_record()
        other_path = self.path.parent.parent / "release-9.9.1" / "release-state.json"
        other_path.parent.mkdir()
        other_state = copy.deepcopy(self.state)
        other_state.update(version="9.9.1", cherry_pick_deadline="2030-01-02T12:00:00Z")
        other_path.write_text(json.dumps(other_state))
        now = datetime(2030, 1, 2, 11, tzinfo=timezone.utc)
        self.assertEqual(inspect_record(self.path, now)["deadline_gate"], "elapsed")
        self.assertEqual(inspect_record(other_path, now)["deadline_gate"], "blocked")

    def test_state_filename_is_dedicated(self):
        self.write_record()
        wrong_path = self.path.with_name("discussion-draft.md")
        wrong_path.write_bytes(self.path.read_bytes())
        with self.assertRaises(ValueError):
            inspect_record(wrong_path)

    def test_markdown_and_malformed_json_are_rejected(self):
        for text in ("```json\n" + json.dumps(self.state) + "\n```", '{"status":'):
            with self.subTest(text=text):
                self.path.write_text(text)
                with self.assertRaises(json.JSONDecodeError):
                    self.check_at()

    def test_deadline_boundary_and_offset_are_absolute_instants(self):
        for deadline in ("2030-01-02T10:00:00Z", "2030-01-02T18:00:00+08:00"):
            with self.subTest(deadline=deadline):
                self.state["cherry_pick_deadline"] = deadline
                self.write_record()
                self.assertEqual(self.check_at()["deadline_gate"], "blocked")
                self.assertEqual(self.check_at(10, 0, 0)["deadline_gate"], "elapsed")
                self.assertEqual(self.check_at(10, 0, 1)["deadline_gate"], "elapsed")

    def test_incomplete_confirmation_stays_blocked_after_deadline(self):
        self.state.update(
            status="awaiting_confirmation", approval=None, exclusions=None
        )
        self.write_record()
        self.assertEqual(self.check_at(11)["deadline_gate"], "blocked")

    def test_relative_rule_waits_for_creation(self):
        self.state.update(
            status="awaiting_confirmation",
            approval=None,
            cherry_pick_deadline=None,
            cherry_pick_deadline_rule={
                "anchor": "discussion_created_at",
                "offset_seconds": 259200,
            },
        )
        self.state["discussion"]["simulated_at"] = None
        self.write_record()
        self.assertEqual(self.check_at(11)["deadline_gate"], "blocked")

    def test_three_day_deadline_uses_creation_time_in_each_mode(self):
        for mode in ("dry-run", "live"):
            with self.subTest(mode=mode):
                state = copy.deepcopy(self.state)
                state.update(
                    mode=mode,
                    status="dry_run_waiting"
                    if mode == "dry-run"
                    else "waiting_for_cherry_picks",
                    cherry_pick_deadline="2030-01-04T18:01:00+08:00",
                    cherry_pick_deadline_rule={
                        "anchor": "discussion_created_at",
                        "offset_seconds": 259200,
                    },
                )
                state["approval"]["mode"] = mode
                if mode == "live":
                    state["discussion"].update(
                        url="https://github.com/apache/kvrocks/discussions/99999",
                        created_at="2030-01-01T10:01:00Z",
                        simulated_at="2029-12-01T10:01:00Z",
                    )
                self.write_record(state)
                before = self.path.read_bytes()
                now = datetime(2030, 1, 4, 10, 0, 59, tzinfo=timezone.utc)
                self.assertEqual(
                    inspect_record(self.path, now)["deadline_gate"], "blocked"
                )
                now = datetime(2030, 1, 4, 10, 1, tzinfo=timezone.utc)
                self.assertEqual(
                    inspect_record(self.path, now)["deadline_gate"], "elapsed"
                )
                self.assertEqual(self.path.read_bytes(), before)

    def test_relative_deadline_mismatch_is_rejected(self):
        self.state["cherry_pick_deadline_rule"] = {
            "anchor": "discussion_created_at",
            "offset_seconds": 259200,
        }
        self.write_record()
        with self.assertRaises(ValueError):
            self.check_at(11)

    def test_invalid_relative_rule_is_rejected(self):
        for offset in (0, -1, True, "259200"):
            with self.subTest(offset=offset):
                self.state["cherry_pick_deadline_rule"] = {
                    "anchor": "discussion_created_at",
                    "offset_seconds": offset,
                }
                self.write_record()
                with self.assertRaises(ValueError):
                    self.check_at()

    def test_waiting_requires_all_confirmed_inputs(self):
        for key, value in (
            ("approval", None),
            ("exclusions", None),
            ("proposed_commit", "unstable"),
            ("cherry_pick_deadline", None),
        ):
            with self.subTest(key=key):
                state = copy.deepcopy(self.state)
                state[key] = value
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_invalid_and_timezone_free_deadlines_are_rejected(self):
        for deadline in (
            "2030-01-02",
            "2030-01-02T10:00:00",
            "tomorrow",
            "2030-99-99T10:00:00Z",
        ):
            with self.subTest(deadline=deadline):
                self.state["cherry_pick_deadline"] = deadline
                self.write_record()
                with self.assertRaises(ValueError):
                    self.check_at()

    def test_dry_run_cannot_claim_publication(self):
        self.state["discussion"]["url"] = (
            "https://github.com/apache/kvrocks/discussions/99999"
        )
        self.write_record()
        with self.assertRaises(ValueError):
            self.check_at(11)

    def test_live_requires_live_approval_and_real_discussion_evidence(self):
        self.state.update(mode="live", status="waiting_for_cherry_picks")
        self.write_record()
        with self.assertRaises(ValueError):
            self.check_at(11)
        self.state["approval"]["mode"] = "live"
        self.write_record()
        with self.assertRaises(ValueError):
            self.check_at(11)
        self.state["discussion"].update(
            url="https://github.com/apache/kvrocks/discussions/99999",
            created_at="2030-01-01T10:01:00Z",
            simulated_at=None,
        )
        self.write_record()
        self.assertEqual(self.check_at()["deadline_gate"], "blocked")
        self.assertEqual(self.check_at(11)["deadline_gate"], "elapsed")

    def test_publication_uncertainty_blocks_after_deadline(self):
        self.state.update(mode="live", status="publication_uncertain")
        self.write_record()
        self.assertEqual(self.check_at(11)["deadline_gate"], "blocked")

    def source_state(self, mode="dry-run"):
        state = copy.deepcopy(self.state)
        state.update(
            step=2,
            status="preparing_source_release",
            mode=mode,
            source_release={},
            external_operations=[],
            discussion_review={
                "checked_at": "2030-01-02T10:01:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
                "source": "/tmp/manager-authorized-discussion-fixture.json",
                "result": "no_unresolved_objections",
            },
            next_step_confirmation={
                "by": "Test release manager",
                "at": "2030-01-02T10:02:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
                "review_checked_at": "2030-01-02T10:01:00Z",
                "target_step": 2,
                "next_step": "Create source releases and stage",
            },
        )
        state["approval"]["mode"] = mode
        if mode == "live":
            state["discussion"].update(
                url="https://github.com/apache/kvrocks/discussions/99999",
                created_at="2030-01-01T10:01:00Z",
                simulated_at=None,
            )
            state["discussion_review"]["source"] = state["discussion"]["url"]
        return state

    def test_step_two_resumes_without_resetting_status_or_approving_operations(self):
        for mode in ("dry-run", "live"):
            with self.subTest(mode=mode):
                state = self.source_state(mode)
                self.write_record(state)
                before = self.path.read_bytes()
                result = self.check_at(11)
                self.assertEqual(result["deadline_gate"], "elapsed")
                self.assertEqual(result["state"]["status"], "preparing_source_release")
                self.assertEqual(result["state"]["external_operations"], [])
                self.assertEqual(self.path.read_bytes(), before)

    def test_step_two_cannot_bypass_deadline_or_transition_time(self):
        self.write_record(self.source_state())
        for hour, minute, second in ((9, 59, 59), (10, 0, 0), (10, 1, 59)):
            with (
                self.subTest(time=(hour, minute, second)),
                self.assertRaises(ValueError),
            ):
                self.check_at(hour, minute, second)

    def test_step_two_requires_review_and_separate_confirmation(self):
        for field in ("source_release", "discussion_review", "next_step_confirmation"):
            with self.subTest(field=field):
                state = self.source_state()
                state[field] = None
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_step_two_blocks_objections_and_mismatched_confirmation(self):
        for section, field, value in (
            ("discussion_review", "result", "unresolved_objections"),
            ("discussion_review", "result", "unverified"),
            ("discussion_review", "checked_at", "2030-01-02T09:59:59Z"),
            ("discussion_review", "simulated", False),
            ("next_step_confirmation", "target_step", 3),
            ("next_step_confirmation", "review_checked_at", "2030-01-02T10:00:00Z"),
            ("next_step_confirmation", "mode", "live"),
        ):
            with self.subTest(section=section, field=field, value=value):
                state = self.source_state()
                state[section][field] = value
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_live_step_two_cannot_use_another_discussion_or_simulated_review(self):
        for field, value in (
            ("source", "https://github.com/apache/kvrocks/discussions/1"),
            ("simulated", True),
        ):
            with self.subTest(field=field):
                state = self.source_state("live")
                state["discussion_review"][field] = value
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_staging_status_must_match_execution_mode(self):
        for mode, status in (
            ("dry-run", "source_release_staged"),
            ("live", "dry_run_source_release_staged"),
        ):
            with self.subTest(mode=mode):
                state = self.source_state(mode)
                state["status"] = status
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def docker_state(self, mode="dry-run", ready=False):
        state = self.source_state(mode)
        source = state["source_release"]
        source.update(
            candidate_number=1,
            candidate_tag="v9.9.0-rc1",
            prepared_commit="b" * 40,
            completed_at="2030-01-02T10:03:00Z",
            remote_tag=None,
        )
        if mode == "live":
            source["remote_tag"] = {
                "repository": "apache/kvrocks",
                "ref": "refs/tags/v9.9.0-rc1",
                "object": "c" * 40,
                "commit": "b" * 40,
                "verified_at": "2030-01-02T10:03:00Z",
            }
        state.update(step=3, status="waiting_for_docker")
        state["docker"] = {
            "entry_confirmation": {
                "by": "Test release manager",
                "at": "2030-01-02T10:04:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
                "target_step": 3,
                "candidate_tag": source["candidate_tag"],
                "prepared_commit": source["prepared_commit"],
            },
            "workflow_path": ".github/workflows/nightly.yaml",
            "expected_platforms": ["linux/amd64", "linux/arm64"],
            "simulated": mode == "dry-run",
            "evidence_source": "/tmp/manager-authorized-docker-fixture.json"
            if mode == "dry-run"
            else None,
            "run": None,
            "image": None,
            "completed_at": None,
        }
        if ready:
            state["status"] = (
                "dry_run_docker_ready" if mode == "dry-run" else "docker_ready"
            )
            ref = "apache/kvrocks:nightly-20300102-v9.9.0-rc1-bbbbbbb"
            digest = "sha256:" + "1" * 64
            state["docker"].update(
                run={
                    "id": 123,
                    "attempt": 1,
                    "repository": "apache/kvrocks",
                    "workflow_path": ".github/workflows/nightly.yaml",
                    "head_branch": source["candidate_tag"],
                    "head_sha": source["prepared_commit"],
                    "event": "push",
                    "status": "completed",
                    "conclusion": "success",
                    "jobs": [
                        {
                            "id": i,
                            "name": name,
                            "status": "completed",
                            "conclusion": "success",
                        }
                        for i, name in enumerate(
                            ("build amd64", "build arm64", "merge"), start=1
                        )
                    ],
                    "published_image": ref,
                    "published_digest": digest,
                },
                image={
                    "ref": ref,
                    "digest": digest,
                    "platforms": ["linux/amd64", "linux/arm64"],
                    "verified_at": "2030-01-02T10:11:00Z",
                },
                completed_at="2030-01-02T10:12:00Z",
            )
        return state

    def test_step_three_resumes_waiting_without_changing_prior_approval(self):
        state = self.docker_state()
        self.write_record(state)
        before = self.path.read_bytes()
        result = self.check_at(11)
        self.assertEqual(result["state"]["status"], "waiting_for_docker")
        self.assertIsNone(result["state"]["docker"]["run"])
        self.assertEqual(result["state"]["next_step_confirmation"]["target_step"], 2)
        self.assertEqual(self.path.read_bytes(), before)

    def test_step_three_requires_staging_and_candidate_confirmation(self):
        for section, field, value in (
            ("source_release", "completed_at", None),
            ("source_release", "candidate_tag", "v9.9.0-rc2"),
            ("docker", "entry_confirmation", None),
            ("docker", "simulated", False),
            ("docker", "evidence_source", None),
        ):
            with self.subTest(section=section, field=field):
                state = self.docker_state()
                state[section][field] = value
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)
        state = self.docker_state("live")
        state["source_release"]["remote_tag"] = None
        self.write_record(state)
        with self.assertRaises(ValueError):
            self.check_at(11)

    def test_docker_ready_requires_matching_workflow_and_verified_manifest(self):
        for mode in ("dry-run", "live"):
            with self.subTest(mode=mode):
                state = self.docker_state(mode, ready=True)
                self.write_record(state)
                self.assertEqual(self.check_at(11)["state"]["status"], state["status"])

    def test_docker_ready_rejects_other_runs_and_nonterminal_or_failed_results(self):
        for field, value in (
            ("repository", "someone/kvrocks"),
            ("workflow_path", ".github/workflows/unrelated.yaml"),
            ("head_branch", "unstable"),
            ("head_sha", "c" * 40),
            ("event", "pull_request"),
            ("status", "in_progress"),
            ("conclusion", "failure"),
            ("conclusion", "cancelled"),
        ):
            with self.subTest(field=field, value=value):
                state = self.docker_state(ready=True)
                state["docker"]["run"][field] = value
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_docker_ready_requires_merge_job_and_every_expected_platform(self):
        for variant in (
            "merge_pending",
            "missing_image",
            "missing_platform",
            "wrong_digest",
        ):
            with self.subTest(variant=variant):
                state = self.docker_state(ready=True)
                docker = state["docker"]
                if variant == "merge_pending":
                    docker["run"]["jobs"][-1].update(
                        status="in_progress", conclusion=None
                    )
                elif variant == "missing_image":
                    docker["image"] = None
                elif variant == "missing_platform":
                    docker["image"]["platforms"] = ["linux/amd64"]
                else:
                    docker["image"]["digest"] = "sha256:" + "2" * 64
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_docker_ready_cannot_promote_simulated_evidence_to_live(self):
        state = self.docker_state(ready=True)
        state["status"] = "docker_ready"
        self.write_record(state)
        with self.assertRaises(ValueError):
            self.check_at(11)

    def verification_state(self, mode="dry-run", complete=True):
        state = self.docker_state(mode, ready=True)
        archive = "apache-kvrocks-9.9.0-src.tar.gz"
        state["source_release"].update(
            signing_fingerprint="A" * 40,
            artifacts=[
                {
                    "path": "/tmp/" + archive + suffix,
                    "sha512": str(i) * 128,
                    "size": i,
                    "status": "simulated" if mode == "dry-run" else "actual",
                }
                for i, suffix in enumerate(("", ".asc", ".sha512"), 1)
            ],
        )
        status = (
            (
                "dry_run_uploaded_candidate_verified"
                if mode == "dry-run"
                else "uploaded_candidate_verified"
            )
            if complete
            else "verifying_uploaded_candidate"
        )
        verification = {
            "status": status,
            "mode": mode,
            "simulated": mode == "dry-run",
            "entry_confirmation": {
                "by": "Test release manager",
                "at": "2030-01-02T10:12:10Z",
                "mode": mode,
                "simulated": mode == "dry-run",
                "target_step": 4,
                "phase": "verify_uploaded_candidate",
                "candidate_tag": "v9.9.0-rc1",
                "prepared_commit": "b" * 40,
            },
            "source_url": "https://dist.apache.org/repos/dist/dev/kvrocks/9.9.0/",
            "source_revision": 100,
            "keys_url": "https://downloads.apache.org/kvrocks/KEYS",
            "signing_fingerprint": "A" * 40,
            "files": [
                {"name": item["path"].rsplit("/", 1)[1], "sha512": item["sha512"]}
                for item in state["source_release"]["artifacts"]
            ],
            "evidence_source": "manager-authorized local fixture"
            if mode == "dry-run"
            else None,
            "checks": {
                name: {
                    "result": "simulated_pass" if mode == "dry-run" else "passed",
                    "at": "2030-01-02T10:12:40Z",
                    "command_or_review": "Test fixture for " + name,
                    "evidence": "Isolated test log for " + name,
                }
                for name in VERIFICATION_CHECKS
            }
            if complete
            else {},
            "read_operation_ids": ["verification-reads"],
            "blockers": [],
            "completed_at": "2030-01-02T10:12:50Z" if complete else None,
        }
        state["candidate_verification"] = verification
        state["external_operations"].append(
            {
                "id": "verification-reads",
                "step": 4,
                "mode": mode,
                "kind": "read",
                "inputs": {
                    key: verification[key]
                    for key in ("source_url", "source_revision", "keys_url")
                },
                "approval": {
                    "by": "Test release manager",
                    "at": "2030-01-02T10:12:20Z",
                    "mode": mode,
                },
                "status": "simulated" if mode == "dry-run" else "succeeded",
            }
        )
        state.update(step=4, status=status, email=None)
        return state

    def email_state(self, mode="dry-run", method="manual", complete=False):
        state = self.verification_state(mode)
        state.update(step=4, status="awaiting_email_sender")
        email = {
            "entry_confirmation": {
                "by": "Test release manager",
                "at": "2030-01-02T10:13:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
                "target_step": 4,
                "candidate_tag": "v9.9.0-rc1",
                "prepared_commit": "b" * 40,
                "verification_sha256": publication_plan_sha256(
                    state["candidate_verification"]
                ),
            },
            "sender": {"address": None, "confirmation": None},
            "to": ["dev@kvrocks.apache.org"],
            "cc": [],
            "bcc": [],
            "subject": None,
            "body": None,
            "composed_at": None,
            "content_approval": None,
            "artifact_review": None,
            "method": method,
            "draft_operation_id": None,
            "draft": None,
            "completed_at": None,
            "blockers": [],
            "connection": {
                "status": "connected" if method == "gmail" else "unavailable",
                "account_address": "manager@example.org" if method == "gmail" else None,
                "can_create_draft": method == "gmail",
                "verified_from": "manager@apache.org" if method == "gmail" else None,
            },
        }
        state["email"] = email
        if not complete:
            return state
        email.update(
            sender={
                "address": "manager@apache.org",
                "confirmation": {
                    "by": "Test release manager",
                    "at": "2030-01-02T10:14:00Z",
                    "mode": mode,
                    "address": "manager@apache.org",
                },
            },
            subject="[VOTE] Release Apache Kvrocks 9.9.0",
            body="Test-only candidate v9.9.0-rc1 vote fixture.",
            composed_at="2030-01-02T10:17:00Z",
            artifact_review={
                "verification_sha256": publication_plan_sha256(
                    state["candidate_verification"]
                ),
                "candidate_tag": "v9.9.0-rc1",
                "prepared_commit": "b" * 40,
                "source_url": "https://dist.apache.org/repos/dist/dev/kvrocks/9.9.0/",
                "keys_url": "https://downloads.apache.org/kvrocks/KEYS",
                "checked_at": "2030-01-02T10:16:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
            },
            completed_at="2030-01-02T10:21:00Z",
        )
        payload_hash = email_payload_sha256(email)
        email["content_approval"] = {
            "by": "Test release manager",
            "at": "2030-01-02T10:18:00Z",
            "mode": mode,
            "payload_sha256": payload_hash,
        }
        state["status"] = (
            "dry_run_email_prepared" if mode == "dry-run" else "manual_email_prepared"
        )
        if method == "gmail":
            email["draft_operation_id"] = "draft-create-1"
            state["external_operations"] = [
                {
                    "id": "draft-create-1",
                    "step": 4,
                    "mode": mode,
                    "kind": "write",
                    "inputs": {
                        "payload_sha256": payload_hash,
                        "account_address": "manager@example.org",
                    },
                    "approval": {
                        "by": "Test release manager",
                        "at": "2030-01-02T10:19:00Z",
                        "mode": mode,
                    },
                    "status": "simulated" if mode == "dry-run" else "succeeded",
                    "result": None
                    if mode == "dry-run"
                    else {"draft_id": "test-draft-id"},
                }
            ] + state["external_operations"]
            if mode == "live":
                state["status"] = "gmail_draft_created"
                email["draft"] = {
                    "id": "test-draft-id",
                    "account_address": "manager@example.org",
                    "from": "manager@apache.org",
                    "created_at": "2030-01-02T10:20:00Z",
                }
        return state

    def test_email_sender_checkpoint_resumes_without_composing_or_writing(self):
        self.write_record(self.email_state())
        before = self.path.read_bytes()
        result = self.check_at(11)
        self.assertEqual(result["state"]["status"], "awaiting_email_sender")
        self.assertIsNone(result["state"]["email"]["subject"])
        self.assertEqual(result["state"]["next_step_confirmation"]["target_step"], 2)
        self.assertEqual(self.path.read_bytes(), before)

    def test_uploaded_verification_resumes_pending_blocked_and_complete(self):
        for mode in ("live", "dry-run"):
            for complete in (False, True):
                with self.subTest(mode=mode, complete=complete):
                    state = self.verification_state(mode, complete)
                    self.write_record(state)
                    before = self.path.read_bytes()
                    result = self.check_at(11)
                    self.assertIn("Step 4a", result["reason"])
                    self.assertEqual(self.path.read_bytes(), before)
                    self.assertIsNone(result["state"]["email"])
        state = self.verification_state(complete=False)
        state["status"] = "candidate_verification_blocked"
        state["candidate_verification"].update(
            status=state["status"], blockers=["Signature check failed"]
        )
        self.write_record(state)
        self.check_at(11)

    def test_opening_email_requires_new_verification_even_for_legacy_records(self):
        for variant in ("missing", "pending", "blocked"):
            state = self.email_state()
            if variant == "missing":
                state.pop("candidate_verification")
            else:
                state["candidate_verification"].update(
                    status="candidate_verification_blocked"
                    if variant == "blocked"
                    else "verifying_uploaded_candidate",
                    completed_at=None,
                )
            self.write_record(state)
            with self.assertRaises(ValueError):
                self.check_at(11)

    def test_every_uploaded_check_must_pass_with_evidence(self):
        for name in VERIFICATION_CHECKS:
            for variant in ("missing", "failed", "no_evidence", "future"):
                with self.subTest(check=name, variant=variant):
                    state = self.verification_state()
                    checks = state["candidate_verification"]["checks"]
                    if variant == "missing":
                        checks.pop(name)
                    elif variant == "failed":
                        checks[name]["result"] = "failed"
                    elif variant == "no_evidence":
                        checks[name]["evidence"] = ""
                    else:
                        checks[name]["at"] = "2030-01-03T10:00:00Z"
                    self.write_record(state)
                    with self.assertRaises(ValueError):
                        self.check_at(11)

    def test_uploaded_identity_and_read_approval_cannot_be_skipped(self):
        for variant in (
            "hash",
            "filename",
            "fingerprint",
            "revision",
            "read_approval",
            "read_scope",
            "read_failed",
            "late_approval",
            "early_entry",
            "simulated_live",
            "blockers",
        ):
            with self.subTest(variant=variant):
                state = self.verification_state("live")
                verification = state["candidate_verification"]
                operation = state["external_operations"][0]
                if variant == "hash":
                    verification["files"][0]["sha512"] = "f" * 128
                elif variant == "filename":
                    verification["files"][0]["name"] = "other.tar.gz"
                elif variant == "fingerprint":
                    verification["signing_fingerprint"] = "B" * 40
                elif variant == "revision":
                    verification["source_revision"] = 0
                elif variant == "read_approval":
                    operation["approval"] = None
                elif variant == "read_scope":
                    operation["inputs"]["source_revision"] = 101
                elif variant == "read_failed":
                    operation["status"] = "failed"
                elif variant == "late_approval":
                    operation["approval"]["at"] = "2030-01-02T10:12:45Z"
                elif variant == "early_entry":
                    verification["entry_confirmation"]["at"] = "2030-01-02T10:11:00Z"
                elif variant == "simulated_live":
                    verification["simulated"] = True
                else:
                    verification["blockers"] = ["Build unresolved"]
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_email_approval_is_bound_to_completed_verification(self):
        for variant in (
            "early_email",
            "changed_revision",
            "changed_bytes",
            "changed_review",
            "unlinked_artifacts",
        ):
            with self.subTest(variant=variant):
                state = self.email_state("live", complete=True)
                verification = state["candidate_verification"]
                if variant == "early_email":
                    state["email"]["entry_confirmation"]["at"] = "2030-01-02T10:12:30Z"
                elif variant == "changed_revision":
                    verification["source_revision"] = 101
                    state["external_operations"][0]["inputs"]["source_revision"] = 101
                elif variant == "changed_bytes":
                    verification["files"][0]["sha512"] = "f" * 128
                    state["source_release"]["artifacts"][0]["sha512"] = "f" * 128
                elif variant == "changed_review":
                    verification["checks"]["build"]["evidence"] = "Replacement log"
                else:
                    state["email"]["artifact_review"].pop("verification_sha256")
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_email_cannot_bypass_docker_readiness_or_candidate_entry(self):
        for variant in (
            "missing_image",
            "failed_run",
            "different_candidate",
            "early_entry",
        ):
            with self.subTest(variant=variant):
                state = self.email_state()
                if variant == "missing_image":
                    state["docker"]["image"] = None
                elif variant == "failed_run":
                    state["docker"]["run"]["conclusion"] = "failure"
                elif variant == "different_candidate":
                    state["email"]["entry_confirmation"]["candidate_tag"] = "v9.9.0-rc2"
                else:
                    state["email"]["entry_confirmation"]["at"] = "2030-01-02T10:11:00Z"
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_email_cannot_be_composed_before_exact_sender_confirmation(self):
        for variant in (
            "pending_subject",
            "missing_approval",
            "different_sender",
            "early_content",
        ):
            with self.subTest(variant=variant):
                state = self.email_state(complete=True)
                email = state["email"]
                if variant == "pending_subject":
                    state["status"] = "awaiting_email_sender"
                elif variant == "missing_approval":
                    email["sender"]["confirmation"] = None
                elif variant == "different_sender":
                    email["sender"]["address"] = "other@apache.org"
                else:
                    email["composed_at"] = "2030-01-02T10:13:30Z"
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_email_manual_and_connector_outcomes_in_each_mode(self):
        for mode in ("live", "dry-run"):
            for method in ("manual", "gmail"):
                with self.subTest(mode=mode, method=method):
                    state = self.email_state(mode, method, complete=True)
                    self.write_record(state)
                    self.assertEqual(
                        self.check_at(11)["state"]["status"], state["status"]
                    )

    def test_email_header_or_body_changes_invalidate_content_approval(self):
        for key, value in (
            ("subject", "Changed subject"),
            ("body", "Changed body"),
            ("to", ["other@example.org"]),
            ("bcc", ["hidden@example.org"]),
        ):
            with self.subTest(key=key):
                state = self.email_state(complete=True)
                state["email"][key] = value
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_email_allows_incomplete_preview_but_blocks_handoff(self):
        state = self.email_state(complete=True)
        email = state["email"]
        email.update(
            artifact_review=None,
            blockers=["Source candidate URL required"],
            completed_at=None,
            content_approval=None,
        )
        state["status"] = "awaiting_email_review"
        self.write_record(state)
        self.assertEqual(self.check_at(11)["state"]["status"], "awaiting_email_review")
        for variant in (
            "blockers",
            "missing_artifacts",
            "wrong_artifacts",
            "simulated_artifacts",
        ):
            with self.subTest(variant=variant):
                state = self.email_state("live", complete=True)
                if variant == "blockers":
                    state["email"]["blockers"] = ["Unverified source artifacts"]
                elif variant == "missing_artifacts":
                    state["email"]["artifact_review"] = None
                elif variant == "wrong_artifacts":
                    state["email"]["artifact_review"]["prepared_commit"] = "c" * 40
                else:
                    state["email"]["artifact_review"]["simulated"] = True
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_gmail_requires_sender_capability_operation_and_real_draft_id(self):
        for variant in (
            "unsupported_sender",
            "read_only",
            "wrong_account",
            "missing_approval",
            "message_id_only",
            "wrong_draft_sender",
        ):
            with self.subTest(variant=variant):
                state = self.email_state("live", "gmail", complete=True)
                email = state["email"]
                if variant == "unsupported_sender":
                    email["connection"]["verified_from"] = "manager@example.org"
                elif variant == "read_only":
                    email["connection"]["can_create_draft"] = False
                elif variant == "wrong_account":
                    state["external_operations"][0]["inputs"]["account_address"] = (
                        "other@example.org"
                    )
                elif variant == "missing_approval":
                    state["external_operations"][0]["approval"] = None
                elif variant == "message_id_only":
                    state["external_operations"][0]["result"] = {
                        "message_id": "test-draft-id"
                    }
                else:
                    email["draft"]["from"] = "manager@example.org"
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_email_dry_run_cannot_claim_live_draft_or_promote_approval(self):
        for variant in ("remote_id", "live_status", "live_approval"):
            with self.subTest(variant=variant):
                state = self.email_state("dry-run", "gmail", complete=True)
                if variant == "remote_id":
                    state["email"]["draft"] = {"id": "invented"}
                elif variant == "live_status":
                    state["status"] = "gmail_draft_created"
                else:
                    state["email"]["sender"]["confirmation"]["mode"] = "live"
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at(11)

    def test_uncertain_email_draft_cannot_claim_completion(self):
        state = self.email_state("live", "gmail", complete=True)
        state["status"] = "email_draft_uncertain"
        state["external_operations"][0].update(status="uncertain", result=None)
        state["email"].update(draft=None, completed_at=None)
        self.write_record(state)
        self.assertEqual(self.check_at(11)["state"]["status"], "email_draft_uncertain")
        state["email"]["completed_at"] = "2030-01-02T10:21:00Z"
        self.write_record(state)
        with self.assertRaises(ValueError):
            self.check_at(11)

    def test_mismatched_version_and_unknown_state_are_rejected(self):
        for key, value in (
            ("version", "../9.9.0"),
            ("version", "9.9.1"),
            ("schema_version", 2),
            ("step", 2),
            ("status", "completed"),
            ("repository", "someone/kvrocks"),
        ):
            with self.subTest(key=key):
                state = copy.deepcopy(self.state)
                state[key] = value
                self.write_record(state)
                with self.assertRaises(ValueError):
                    self.check_at()

    def test_expired_deadline_at_simulation_is_rejected(self):
        self.state["discussion"]["simulated_at"] = self.state["cherry_pick_deadline"]
        self.write_record()
        with self.assertRaises(ValueError):
            self.check_at(11)

    def test_saved_elapsed_status_cannot_bypass_time_gate(self):
        self.state["status"] = "deadline_elapsed"
        self.write_record()
        with self.assertRaises(ValueError):
            self.check_at()

    def test_missing_and_duplicate_records_fail_closed(self):
        with self.assertRaises(FileNotFoundError):
            self.check_at()
        self.write_record()
        self.path.write_text(self.path.read_text() * 2)
        with self.assertRaises(ValueError):
            self.check_at()

    def test_cli_reports_block_and_missing_file(self):
        command = [
            sys.executable,
            str(Path(__file__).with_name("check_state.py")),
            str(self.path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.state["cherry_pick_deadline"] = "2099-01-02T10:00:00Z"
        self.write_record()
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["deadline_gate"], "blocked")


if __name__ == "__main__":
    unittest.main()
