import copy
import json
import unittest

import test_website as fixtures
from check_state import (
    inspect_record,
    instant,
    publication_plan_sha256,
    website_release_links,
)


class AnnouncementTest(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.WebsiteTest()
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

    def state(self, mode="dry-run", handoff=True, complete=False):
        state = self.fixture.state(mode, prepared=True, complete=True)
        announcement = {
            "previous_status": state["status"],
            "entry_confirmation": {
                "by": "Test release manager",
                "at": "2030-01-05T11:30:00Z",
                "mode": mode,
                "simulated": mode == "dry-run",
                "target_step": 8,
                "version": "9.9.0",
                "website_sha256": publication_plan_sha256(state["website"]),
            },
            "handoff": None,
            "send_confirmation": None,
            "completed_at": None,
        }
        state.update(
            step=8,
            status="preparing_announcement_handoff",
            announcement=announcement,
            next_action="Hand off the announcement to the release manager",
        )
        if not handoff:
            return state
        announcement["handoff"] = {
            "at": "2030-01-05T11:31:00Z",
            "mode": mode,
            "simulated": mode == "dry-run",
            "version": "9.9.0",
            "to": ["dev@kvrocks.apache.org"],
            "cc": ["announce@apache.org"],
            "from_domain": "apache.org",
            "links": website_release_links("9.9.0"),
            "content": "Test fixture: acknowledge this simulated announcement handoff."
            if mode == "dry-run"
            else "Test fixture: send the 9.9.0 announcement to dev@kvrocks.apache.org, Cc announce@apache.org, from your Apache address; report when sent.",
        }
        state["status"] = "awaiting_announcement_sent"
        if not complete:
            return state
        announcement["send_confirmation"] = {
            "by": "Test release manager",
            "at": "2030-01-05T11:40:00Z",
            "mode": mode,
            "simulated": mode == "dry-run",
            "version": "9.9.0",
            "handoff_sha256": publication_plan_sha256(announcement["handoff"]),
            "outcome": "simulated" if mode == "dry-run" else "sent",
            "sent_at": None,
            "message_url": None,
        }
        announcement["completed_at"] = "2030-01-05T11:40:01Z"
        state.update(
            status="dry_run_release_complete"
            if mode == "dry-run"
            else "release_complete",
            next_action=None,
        )
        return state

    def test_manual_handoff_needs_no_external_operation_or_email_draft(self):
        for handoff in (False, True):
            state = self.state(handoff=handoff)
            self.check(state)
            self.assertIsNone(state["announcement"]["send_confirmation"])
            self.assertFalse(
                any(op.get("step") == 8 for op in state["external_operations"])
            )

    def test_entry_requires_completed_website_and_separate_confirmation(self):
        for variant in ("website", "entry", "clock", "version", "snapshot"):
            with self.subTest(variant=variant):
                state = self.state()
                announcement = state["announcement"]
                if variant == "website":
                    announcement["previous_status"] = "awaiting_website_pr_review"
                elif variant == "entry":
                    announcement["entry_confirmation"] = None
                elif variant == "clock":
                    announcement["entry_confirmation"]["at"] = "2030-01-05T11:24:00Z"
                elif variant == "version":
                    announcement["entry_confirmation"]["version"] = "9.8.0"
                else:
                    announcement["entry_confirmation"]["website_sha256"] = "0" * 64
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_asking_or_unclear_answer_does_not_complete_release(self):
        state = self.state()
        state["status"] = "dry_run_release_complete"
        with self.assertRaises(ValueError):
            self.check(state)
        state = self.state(complete=True)
        state["announcement"]["send_confirmation"]["outcome"] = "not_yet"
        with self.assertRaises(ValueError):
            self.check(state)

    def test_live_manager_report_suffices_without_send_time_or_archive_lookup(self):
        state = self.state("live", complete=True)
        result = self.check(state)
        self.assertIn("manager reported sending", result["reason"])
        self.assertIsNone(state["announcement"]["send_confirmation"]["sent_at"])
        self.assertIsNone(state["announcement"]["send_confirmation"]["message_url"])

    def test_dry_run_completion_cannot_claim_live_send_or_message_url(self):
        for key, value in (
            ("outcome", "sent"),
            ("simulated", False),
            ("sent_at", "2030-01-05T11:35:00Z"),
            ("message_url", "https://lists.apache.org/thread/test"),
        ):
            with self.subTest(key=key):
                state = self.state(complete=True)
                state["announcement"]["send_confirmation"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)
        state = self.state(complete=True)
        state["status"] = "release_complete"
        with self.assertRaises(ValueError):
            self.check(state)

    def test_recipient_sender_requirement_links_and_changed_handoff_are_bound(self):
        for key, value in (
            ("to", ["announce@apache.org"]),
            ("cc", []),
            ("from_domain", "gmail.com"),
            ("links", website_release_links("9.8.0")),
            ("content", "Revised handoff"),
        ):
            with self.subTest(key=key):
                state = self.state(complete=True)
                state["announcement"]["handoff"][key] = value
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_completion_follows_confirmation_and_clears_pending_work(self):
        for variant in ("confirmation", "completed_at", "next_action", "sent_at"):
            with self.subTest(variant=variant):
                state = self.state("live", complete=True)
                announcement = state["announcement"]
                if variant == "confirmation":
                    announcement["send_confirmation"]["at"] = "2030-01-05T11:30:00Z"
                elif variant == "completed_at":
                    announcement["completed_at"] = "2030-01-05T11:39:00Z"
                elif variant == "next_action":
                    state["next_action"] = "Send the announcement again"
                else:
                    announcement["send_confirmation"]["sent_at"] = (
                        "2030-01-05T11:41:00Z"
                    )
                with self.assertRaises(ValueError):
                    self.check(state)

    def test_terminal_resumption_preserves_history_and_all_prior_outcomes(self):
        for mode in ("dry-run", "live"):
            with self.subTest(mode=mode):
                state = self.state(mode, complete=True)
                saved = copy.deepcopy(state)
                result = self.check(state)
                self.assertEqual(result["state"], saved)
                self.assertEqual(result["state"]["step"], 8)
                self.assertIn("process complete", result["reason"])
                self.assertIsNone(result["state"]["next_action"])


if __name__ == "__main__":
    unittest.main()
