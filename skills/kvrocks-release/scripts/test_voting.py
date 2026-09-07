"""Verify vote and result-email gates using isolated release records."""

import copy
import json
import unittest
from datetime import datetime, timedelta, timezone

import test_check_state as fixtures
from check_state import email_payload_sha256, inspect_record, vote_snapshot_sha256


class VotingTest(unittest.TestCase):
    def setUp(self):
        self.base = fixtures.CheckStateTest()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.path = self.base.path
        self.now = datetime(2030, 1, 5, 10, 30, tzinfo=timezone.utc)

    def state(self, mode="dry-run", with_start=True):
        state = self.base.email_state(mode, complete=True)
        outcome = state["status"]
        state.update(
            step=5,
            status="waiting_for_votes" if with_start else "awaiting_vote_start",
            result_email=None,
        )
        vote = {
            "outcome_source": "release_manager",
            "proposal_email_status": outcome,
            "entry_confirmation": {
                "by": "Test release manager",
                "at": "2030-01-02T10:25:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
                "target_step": 5,
                "candidate_tag": "v9.9.0-rc1",
                "prepared_commit": "b" * 40,
            },
            "started_at": None,
            "start_record": None,
            "minimum_end_at": None,
            "announced_end_at": None,
            "outcome_confirmation": None,
            "passed_at": None,
        }
        state["vote"] = vote
        if with_start:
            vote.update(
                started_at="2030-01-02T10:30:00Z",
                start_record={
                    "source": "release_manager",
                    "by": "Test release manager",
                    "at": "2030-01-02T10:35:00Z",
                    "mode": mode,
                    "simulated": mode == "dry-run",
                },
                minimum_end_at="2030-01-05T10:30:00Z",
            )
        return state

    def check(self, state, now=None):
        self.path.write_text(json.dumps(state, indent=2) + "\n")
        before = self.path.read_bytes()
        result = inspect_record(self.path, now or self.now)
        self.assertEqual(self.path.read_bytes(), before)
        return result["vote_evaluation"]

    def passed(self, mode="dry-run"):
        state = self.state(mode)
        state["status"] = "dry_run_vote_passed" if mode == "dry-run" else "vote_passed"
        state["vote"]["outcome_confirmation"] = {
            "by": "Test release manager",
            "at": "2030-01-05T10:30:00Z",
            "mode": mode,
            "simulated": mode == "dry-run",
            "passed": True,
            "candidate_tag": "v9.9.0-rc1",
            "prepared_commit": "b" * 40,
            "started_at": state["vote"]["started_at"],
            "deadline": state["vote"]["minimum_end_at"],
        }
        state["vote"]["passed_at"] = "2030-01-05T10:30:00Z"
        return state

    def result_state(self, mode="dry-run", method="manual", complete=False):
        state = self.passed(mode)
        state["status"] = "drafting_vote_result"
        prepared = self.base.email_state(mode, method=method, complete=complete)
        email = copy.deepcopy(prepared["email"])
        email["status"] = prepared["status"]
        email["entry_confirmation"].update(target_step=5, at="2030-01-05T10:32:00Z")
        email["vote_snapshot_sha256"] = vote_snapshot_sha256(state["vote"])
        state["result_email"] = email
        if not complete:
            return state
        email["sender"]["confirmation"]["at"] = "2030-01-05T10:33:00Z"
        email.update(
            subject="[RESULT][VOTE] Release Apache Kvrocks 9.9.0",
            body="Test fixture: the v9.9.0-rc1 vote passed as confirmed by the release manager.",
            reply_message_id="test-connector-opening-id",
            composed_at="2030-01-05T10:35:00Z",
            completed_at="2030-01-05T10:39:00Z",
        )
        email["content_approval"].update(
            at="2030-01-05T10:36:00Z", payload_sha256=email_payload_sha256(email)
        )
        if method == "gmail":
            operation = copy.deepcopy(prepared["external_operations"][0])
            operation.update(id="result-draft-create", step=5)
            operation["inputs"]["payload_sha256"] = email_payload_sha256(email)
            operation["approval"]["at"] = "2030-01-05T10:37:00Z"
            state["external_operations"].append(operation)
            email["draft_operation_id"] = operation["id"]
            if email["draft"] is not None:
                email["draft"]["created_at"] = "2030-01-05T10:38:00Z"
        state["status"] = (
            "dry_run_vote_result_prepared"
            if mode == "dry-run"
            else "vote_result_prepared"
        )
        return state

    def test_draft_handoff_does_not_start_vote_clock(self):
        state = self.state(with_start=False)
        self.assertEqual(self.check(state)["gate"], "awaiting_start")
        state["vote"]["minimum_end_at"] = "2030-01-05T10:30:00Z"
        with self.assertRaises(ValueError):
            self.check(state)

    def test_wait_before_72_hours_then_ask_for_outcome(self):
        state = self.state()
        before = self.now - timedelta(seconds=1)
        self.assertEqual(self.check(state, before)["gate"], "waiting")
        self.assertEqual(self.check(state)["gate"], "awaiting_outcome")
        state["status"] = "awaiting_vote_outcome"
        self.assertEqual(self.check(state)["gate"], "awaiting_outcome")
        with self.assertRaises(ValueError):
            self.check(state, before)

    def test_positive_manager_answer_at_exactly_72_hours_is_sufficient(self):
        for mode in ("dry-run", "live"):
            with self.subTest(mode=mode):
                state = self.passed(mode)
                self.assertNotIn("thread", state["vote"])
                self.assertNotIn("review", state["vote"])
                self.assertEqual(self.check(state)["gate"], "passed")

    def test_missing_or_negative_answer_blocks_passage_and_drafting(self):
        state = self.passed()
        state["vote"]["outcome_confirmation"] = None
        with self.assertRaises(ValueError):
            self.check(state)
        state = self.passed()
        state["vote"]["outcome_confirmation"]["passed"] = False
        state["vote"]["passed_at"] = None
        state["status"] = "vote_not_passed"
        self.assertEqual(self.check(state)["gate"], "not_passed")
        state["status"] = "drafting_vote_result"
        with self.assertRaises(ValueError):
            self.check(state)

    def test_early_and_unclear_answers_cannot_authorize_a_later_transition(self):
        for key, value in (
            ("at", "2030-01-05T10:29:59Z"),
            ("at", "2030-01-05T10:30:01Z"),
            ("passed", "yes"),
            ("passed", 1),
            ("passed", None),
        ):
            with self.subTest(key=key, value=value):
                state = self.passed()
                state["vote"]["outcome_confirmation"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_manager_answer_is_bound_to_candidate_clock_and_mode(self):
        for key, value in (
            ("candidate_tag", "v9.9.0-rc2"),
            ("prepared_commit", "c" * 40),
            ("mode", "live"),
            ("simulated", False),
            ("started_at", "2030-01-01T10:30:00Z"),
            ("deadline", "2030-01-06T10:30:00Z"),
            ("by", ""),
        ):
            with self.subTest(key=key):
                state = self.passed()
                state["vote"]["outcome_confirmation"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_vote_clock_cannot_use_cherry_pick_deadline_or_skip_longer_window(self):
        state = self.state()
        state["vote"]["minimum_end_at"] = state["cherry_pick_deadline"]
        with self.assertRaises(ValueError):
            self.check(state)
        state = self.state()
        state["vote"]["announced_end_at"] = "2030-01-06T10:30:00Z"
        self.assertEqual(self.check(state)["gate"], "waiting")
        state = self.passed()
        state["vote"]["announced_end_at"] = "2030-01-06T10:30:00Z"
        with self.assertRaises(ValueError):
            self.check(state)

    def test_prior_record_can_supply_start_without_archive_access(self):
        state = self.state("live")
        state["vote"]["start_record"].update(source="prior_record", by="Codex")
        self.assertEqual(self.check(state)["gate"], "awaiting_outcome")

    def test_legacy_automated_outcome_cannot_substitute_for_manager_answer(self):
        state = self.state()
        state["vote"].pop("outcome_source")
        state["vote"]["review"] = {"complete": True, "binding_plus_one": 3}
        with self.assertRaisesRegex(ValueError, "Migrate"):
            self.check(state)

    def test_result_entry_uses_positive_answer_without_second_vote_confirmation(self):
        state = self.result_state()
        self.assertNotIn("result_confirmation", state["vote"])
        self.assertEqual(
            self.check(state, self.now + timedelta(hours=1))["gate"], "passed"
        )
        self.assertIsNone(state["result_email"]["subject"])
        state["result_email"]["subject"] = "Premature result"
        with self.assertRaises(ValueError):
            self.check(state, self.now + timedelta(hours=1))

    def test_result_manual_and_gmail_drafts_preserve_opening_email(self):
        for mode in ("dry-run", "live"):
            for method in ("manual", "gmail"):
                with self.subTest(mode=mode, method=method):
                    state = self.result_state(mode, method, complete=True)
                    opening = copy.deepcopy(state["email"])
                    self.assertEqual(
                        self.check(state, self.now + timedelta(hours=1))["gate"],
                        "passed",
                    )
                    self.assertEqual(state["email"], opening)

    def test_changed_answer_invalidates_result_email(self):
        for variant in ("negative", "new_confirmation"):
            with self.subTest(variant=variant):
                state = self.result_state(complete=True)
                if variant == "negative":
                    state["vote"]["outcome_confirmation"]["passed"] = False
                else:
                    state["vote"]["outcome_confirmation"]["at"] = "2030-01-05T10:31:00Z"
                    state["vote"]["passed_at"] = "2030-01-05T10:31:00Z"
                with self.assertRaises(ValueError):
                    self.check(state, self.now + timedelta(hours=1))

    def test_unchanged_answer_is_reused_on_resume(self):
        state = self.result_state(complete=True)
        self.assertEqual(
            self.check(state, self.now + timedelta(days=1))["gate"], "passed"
        )


if __name__ == "__main__":
    unittest.main()
