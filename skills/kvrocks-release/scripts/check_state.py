#!/usr/bin/env python3
"""Validate release gates and saved evidence without writes or network access."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?")
WAITING = {"dry_run_waiting", "waiting_for_cherry_picks", "deadline_elapsed"}
STATUSES = WAITING | {"awaiting_confirmation", "publication_uncertain"}
SOURCE_STATUSES = {
    "preparing_source_release",
    "source_release_validated",
    "tag_push_uncertain",
    "source_release_staged",
    "dry_run_source_release_staged",
}
DOCKER_STATUSES = {
    "waiting_for_docker",
    "docker_blocked",
    "docker_ready",
    "dry_run_docker_ready",
}
VERIFICATION_STATUSES = {
    "verifying_uploaded_candidate",
    "candidate_verification_blocked",
    "uploaded_candidate_verified",
    "dry_run_uploaded_candidate_verified",
}
VERIFICATION_CHECKS = {
    "downloads",
    "checksums",
    "signatures",
    "archive",
    "license_notice",
    "license_headers",
    "build",
}
EMAIL_STATUSES = {
    "awaiting_email_sender",
    "awaiting_email_review",
    "email_draft_uncertain",
    "gmail_draft_created",
    "manual_email_prepared",
    "dry_run_email_prepared",
}
EMAIL_COMPLETE = {
    "gmail_draft_created",
    "manual_email_prepared",
    "dry_run_email_prepared",
}
VOTE_STATUSES = {
    "awaiting_vote_start",
    "waiting_for_votes",
    "awaiting_vote_outcome",
    "vote_not_passed",
    "vote_passed",
    "dry_run_vote_passed",
    "drafting_vote_result",
    "vote_result_prepared",
    "dry_run_vote_result_prepared",
}
PUBLICATION_STATUSES = {
    "preparing_publication",
    "publishing_release",
    "publication_blocked",
    "release_publication_uncertain",
    "awaiting_github_release_notes",
    "publication_complete",
    "dry_run_publication_complete",
}
PUBLISHED = {"published", "already_published", "simulated"}
WEBSITE_STATUSES = {
    "preparing_website_pr",
    "awaiting_website_pr_review",
    "website_pr_blocked",
    "website_push_uncertain",
    "website_pr_uncertain",
    "website_pr_created",
    "dry_run_website_pr_prepared",
    "website_already_updated",
}
WEBSITE_REPOSITORY = "apache/kvrocks-website"
WEBSITE_FILE = "src/components/Releases/index.tsx"
ANNOUNCEMENT_STATUSES = {
    "preparing_announcement_handoff",
    "awaiting_announcement_sent",
    "release_complete",
    "dry_run_release_complete",
}


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value
    ):
        raise ValueError("Timestamps must use RFC 3339 with an explicit timezone")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def check_source_transition(state, deadline_at, current):
    review = state.get("discussion_review")
    confirmation = state.get("next_step_confirmation")
    simulated = state["mode"] == "dry-run"
    if (
        not isinstance(state.get("source_release"), dict)
        or not isinstance(review, dict)
        or review.get("result") != "no_unresolved_objections"
        or review.get("mode") != state["mode"]
        or review.get("simulated") is not simulated
        or not isinstance(review.get("source"), str)
        or not review["source"].strip()
        or not isinstance(confirmation, dict)
        or confirmation.get("target_step") != 2
        or confirmation.get("mode") != state["mode"]
        or confirmation.get("simulated") is not simulated
        or not isinstance(confirmation.get("by"), str)
        or not confirmation["by"].strip()
    ):
        raise ValueError(
            "Step 2 requires a clear discussion review and matching manager transition confirmation"
        )
    reviewed = instant(review.get("checked_at"))
    confirmed = instant(confirmation.get("at"))
    if (
        not deadline_at <= reviewed <= confirmed <= current
        or instant(confirmation.get("review_checked_at")) != reviewed
    ):
        raise ValueError(
            "Step-2 review and confirmation must follow the deadline and refer to the same review"
        )
    if not simulated and review["source"] != state["discussion"]["url"]:
        raise ValueError("Live transition review must refer to the recorded discussion")
    if (simulated and state["status"] == "source_release_staged") or (
        not simulated and state["status"] == "dry_run_source_release_staged"
    ):
        raise ValueError("Staging status does not match the release execution mode")


def check_docker_state(state, current, require_ready=False):
    source = state["source_release"]
    docker = state.get("docker")
    simulated = state["mode"] == "dry-run"
    if not isinstance(docker, dict):
        raise TypeError("Step 3 requires Docker monitoring state")
    entry = docker.get("entry_confirmation")
    candidate_number = source.get("candidate_number")
    if (
        type(candidate_number) is not int
        or candidate_number <= 0
        or source.get("candidate_tag") != f"v{state['version']}-rc{candidate_number}"
        or not re.fullmatch(r"[0-9a-fA-F]{40}", source.get("prepared_commit") or "")
        or not isinstance(entry, dict)
        or entry.get("target_step") != 3
        or entry.get("mode") != state["mode"]
        or entry.get("simulated") is not simulated
        or docker.get("simulated") is not simulated
        or not isinstance(entry.get("by"), str)
        or not entry["by"].strip()
        or entry.get("candidate_tag") != source["candidate_tag"]
        or entry.get("prepared_commit") != source["prepared_commit"]
        or not isinstance(docker.get("workflow_path"), str)
        or not docker["workflow_path"].strip()
    ):
        raise ValueError(
            "Step 3 requires confirmation for the exact source candidate and execution mode"
        )
    completed = instant(source.get("completed_at"))
    entered = instant(entry.get("at"))
    if (
        not instant(state["next_step_confirmation"]["at"])
        <= completed
        <= entered
        <= current
    ):
        raise ValueError(
            "Docker monitoring must follow completed source staging and manager confirmation"
        )
    remote = source.get("remote_tag")
    if simulated:
        if (
            remote is not None
            or not isinstance(docker.get("evidence_source"), str)
            or not docker["evidence_source"].strip()
        ):
            raise ValueError(
                "A Docker rehearsal requires fixture evidence and cannot claim a live tag push"
            )
    elif (
        not isinstance(remote, dict)
        or remote.get("repository") != state["repository"]
        or remote.get("ref") != f"refs/tags/{source['candidate_tag']}"
        or remote.get("commit") != source["prepared_commit"]
    ):
        raise ValueError("Live Docker monitoring requires the verified candidate tag")
    run = docker.get("run")
    if run is not None and (
        not isinstance(run, dict)
        or run.get("repository") != state["repository"]
        or run.get("workflow_path") != docker["workflow_path"]
        or run.get("head_branch") != source["candidate_tag"]
        or run.get("head_sha") != source["prepared_commit"]
        or run.get("event") != "push"
        or type(run.get("id")) is not int
        or run["id"] <= 0
        or type(run.get("attempt")) is not int
        or run["attempt"] <= 0
    ):
        raise ValueError(
            "Workflow run does not match the candidate tag, commit, workflow, and push event"
        )
    ready_status = state["status"] in {"docker_ready", "dry_run_docker_ready"}
    if not ready_status and not require_ready:
        return
    if ready_status and (state["status"] == "dry_run_docker_ready") is not simulated:
        raise ValueError(
            "Docker readiness status does not match the release execution mode"
        )
    if (
        not isinstance(run, dict)
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
    ):
        raise ValueError("Docker readiness requires a completed successful workflow")
    jobs = run.get("jobs")
    if (
        not isinstance(jobs, list)
        or not jobs
        or any(
            not isinstance(job, dict)
            or job.get("status") != "completed"
            or job.get("conclusion") != "success"
            for job in jobs
        )
    ):
        raise ValueError("All required Docker build and publication jobs must succeed")
    image = docker.get("image")
    expected = docker.get("expected_platforms")
    if (
        not isinstance(image, dict)
        or not isinstance(image.get("ref"), str)
        or not re.fullmatch(r"(?:docker\.io/)?apache/kvrocks:[^@\s]+", image["ref"])
        or image["ref"] != run.get("published_image")
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", image.get("digest") or "")
        or image["digest"] != run.get("published_digest")
        or not isinstance(expected, list)
        or not expected
        or not isinstance(image.get("platforms"), list)
        or not set(expected).issubset(image["platforms"])
    ):
        raise ValueError(
            "Docker readiness requires the published image digest and all expected platforms"
        )
    if (
        not entered
        <= instant(image.get("verified_at"))
        <= instant(docker.get("completed_at"))
        <= current
    ):
        raise ValueError(
            "Docker readiness requires recorded image verification and completion times"
        )


def email_payload_sha256(email):
    payload = {key: email.get(key) for key in ("to", "cc", "bcc", "subject", "body")}
    payload["from"] = email["sender"]["address"]
    if email.get("reply_message_id") is not None:
        payload["reply_message_id"] = email["reply_message_id"]
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def confirmed_at(confirmation, mode):
    if (
        not isinstance(confirmation, dict)
        or confirmation.get("mode") != mode
        or not isinstance(confirmation.get("by"), str)
        or not confirmation["by"].strip()
    ):
        raise ValueError("Release-manager confirmation is required in the current mode")
    return instant(confirmation.get("at"))


def check_candidate_verification(state, current, *, require_complete=False):
    verification = state.get("candidate_verification")
    if verification is None:
        raise ValueError(
            "Uploaded candidate verification is required before email drafting"
        )
    if not isinstance(verification, dict):
        raise TypeError("Uploaded candidate verification must be an object")
    mode = state["mode"]
    simulated = mode == "dry-run"
    source = state["source_release"]
    entry = verification.get("entry_confirmation")
    entered = confirmed_at(entry, mode)
    if (
        entry.get("target_step") != 4
        or entry.get("phase") != "verify_uploaded_candidate"
        or entry.get("simulated") is not simulated
        or verification.get("mode") != mode
        or verification.get("simulated") is not simulated
        or any(
            entry.get(key) != source[key]
            for key in ("candidate_tag", "prepared_commit")
        )
        or not instant(state["docker"]["completed_at"]) <= entered <= current
        or not isinstance(verification.get("blockers"), list)
    ):
        raise ValueError(
            "Verification entry must confirm the candidate after Docker readiness"
        )
    status = verification.get("status")
    if status not in VERIFICATION_STATUSES:
        raise ValueError("Unknown uploaded candidate verification status")
    complete = status in {
        "uploaded_candidate_verified",
        "dry_run_uploaded_candidate_verified",
    }
    if not complete:
        if require_complete or verification.get("completed_at") is not None:
            raise ValueError(
                "Complete uploaded candidate verification before drafting the vote email"
            )
        return
    completed = instant(verification.get("completed_at"))
    if (
        (status == "dry_run_uploaded_candidate_verified") != simulated
        or verification["blockers"]
        or not entered <= completed <= current
        or not re.fullmatch(
            r"https://dist\.apache\.org/repos/dist/dev/kvrocks/[^\s?#]+",
            verification.get("source_url") or "",
        )
        or type(verification.get("source_revision")) is not int
        or verification["source_revision"] <= 0
        or verification.get("keys_url") != "https://downloads.apache.org/kvrocks/KEYS"
        or not re.fullmatch(
            r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}",
            verification.get("signing_fingerprint") or "",
        )
        or verification["signing_fingerprint"] != source.get("signing_fingerprint")
        or (simulated and not verification.get("evidence_source"))
    ):
        raise ValueError(
            "Verification must bind the staged revision, confirmed signer, mode, and completion"
        )
    archive = f"apache-kvrocks-{state['version']}-src.tar.gz"
    files = publication_files(verification.get("files"))
    artifacts = source.get("artifacts") or []
    if (
        set(files) != {archive, archive + ".asc", archive + ".sha512"}
        or any(
            item.get("status") != ("simulated" if simulated else "actual")
            for item in artifacts
        )
        or files
        != publication_files(
            [
                {"name": Path(item["path"]).name, "sha512": item.get("sha512")}
                for item in artifacts
            ]
        )
    ):
        raise ValueError(
            "Downloaded files must match the prepared candidate artifact hashes"
        )
    checks = verification.get("checks")
    if not isinstance(checks, dict) or set(checks) != VERIFICATION_CHECKS:
        raise ValueError("Every uploaded candidate checklist item is required")
    for check in checks.values():
        if (
            not isinstance(check, dict)
            or check.get("result") != ("simulated_pass" if simulated else "passed")
            or not entered <= instant(check.get("at")) <= completed
            or any(
                not isinstance(check.get(key), str) or not check[key].strip()
                for key in ("command_or_review", "evidence")
            )
        ):
            raise ValueError(
                "Verification checks require passing results and dated command/review evidence"
            )
    operation_ids = verification.get("read_operation_ids")
    if not isinstance(operation_ids, list) or not operation_ids:
        raise ValueError(
            "Record the approved artifact and KEYS read scope or authorized dry-run fixtures"
        )
    for operation_id in operation_ids:
        matches = [
            item
            for item in state.get("external_operations", [])
            if item.get("id") == operation_id
        ]
        if len(matches) != 1:
            raise ValueError("Verification read operation is missing or ambiguous")
        operation = matches[0]
        approved = confirmed_at(operation.get("approval"), mode)
        if (
            operation.get("mode") != mode
            or operation.get("step") != 4
            or operation.get("kind") != "read"
            or operation.get("status") != ("simulated" if simulated else "succeeded")
            or operation.get("inputs")
            != {
                "source_url": verification["source_url"],
                "source_revision": verification["source_revision"],
                "keys_url": verification["keys_url"],
            }
            or not entered <= approved <= instant(checks["downloads"]["at"])
        ):
            raise ValueError(
                "Verification downloads must follow approval of the exact resource scope"
            )


def check_email_state(
    state, current, *, email=None, status=None, target_step=4, not_before=None
):
    email = state.get("email") if email is None else email
    if not isinstance(email, dict):
        raise TypeError("Email phase requires email state")
    mode = state["mode"]
    simulated = mode == "dry-run"
    status = state["status"] if status is None else status
    source = state["source_release"]
    check_candidate_verification(state, current, require_complete=True)
    verification = state["candidate_verification"]
    entry = email.get("entry_confirmation")
    entered = confirmed_at(entry, mode)
    if (
        entry.get("target_step") != target_step
        or entry.get("simulated") is not simulated
        or entry.get("verification_sha256") != publication_plan_sha256(verification)
        or any(
            entry.get(key) != source[key]
            for key in ("candidate_tag", "prepared_commit")
        )
        or not (not_before or instant(verification["completed_at"]))
        <= entered
        <= current
    ):
        raise ValueError(
            "Email entry must follow uploaded candidate verification and confirm the exact evidence"
        )
    if status == "awaiting_email_sender":
        if any(
            email.get(key) is not None
            for key in (
                "subject",
                "body",
                "composed_at",
                "content_approval",
                "draft",
                "completed_at",
                "draft_operation_id",
            )
        ):
            raise ValueError(
                "Do not compose or create an email before sender confirmation"
            )
        return
    sender = email.get("sender")
    if not isinstance(sender, dict) or not re.fullmatch(
        r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+", sender.get("address") or ""
    ):
        raise ValueError("Email requires an exact sender address")
    sender_at = confirmed_at(sender.get("confirmation"), mode)
    composed = instant(email.get("composed_at"))
    if (
        sender["confirmation"].get("address") != sender["address"]
        or not sender_at <= composed <= current
        or (
            sender_at < entered
            and sender["confirmation"].get("scope") != "vote_and_result"
        )
        or composed < entered
        or any(
            not isinstance(email.get(key), str) or not email[key].strip()
            for key in ("subject", "body")
        )
        or any(not isinstance(email.get(key), list) for key in ("to", "cc", "bcc"))
        or not email["to"]
        or any(
            not isinstance(address, str)
            or not re.fullmatch(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+", address)
            for key in ("to", "cc", "bcc")
            for address in email[key]
        )
        or email.get("method") not in {"gmail", "manual"}
        or not isinstance(email.get("blockers"), list)
    ):
        raise ValueError(
            "Email content must follow confirmation of its sender and contain valid headers"
        )
    if status == "awaiting_email_review":
        if email.get("draft") is not None or email.get("completed_at") is not None:
            raise ValueError(
                "An unreviewed email cannot claim draft creation or completion"
            )
        return
    approved = confirmed_at(email.get("content_approval"), mode)
    payload_hash = email_payload_sha256(email)
    if (
        not composed <= approved <= current
        or email["content_approval"].get("payload_sha256") != payload_hash
        or email["blockers"]
    ):
        raise ValueError(
            "Email handoff requires approval of the exact content and no blockers"
        )
    artifacts = email.get("artifact_review")
    if (
        not isinstance(artifacts, dict)
        or artifacts.get("mode") != mode
        or artifacts.get("simulated") is not simulated
        or any(
            artifacts.get(key) != source[key]
            for key in ("candidate_tag", "prepared_commit")
        )
        or not re.fullmatch(
            r"https://dist\.apache\.org/repos/dist/dev/kvrocks/[^\s?#]+",
            artifacts.get("source_url") or "",
        )
        or artifacts.get("keys_url") != "https://downloads.apache.org/kvrocks/KEYS"
        or artifacts.get("source_url") != verification["source_url"]
        or artifacts.get("verification_sha256") != publication_plan_sha256(verification)
        or not instant(verification["completed_at"])
        <= instant(artifacts.get("checked_at"))
        <= approved
    ):
        raise ValueError(
            "Email handoff requires verified source artifact and key links for this candidate"
        )
    if (simulated and status != "dry_run_email_prepared") or (
        not simulated and status == "dry_run_email_prepared"
    ):
        raise ValueError("Email outcome does not match the release mode")
    if email["method"] == "gmail":
        connection = email.get("connection") or {}
        if (
            connection.get("status") != "connected"
            or connection.get("can_create_draft") is not True
            or not connection.get("account_address")
            or connection.get("verified_from") != sender["address"]
        ):
            raise ValueError(
                "Gmail draft requires verified capability for the confirmed From address"
            )
        operations = [
            op
            for op in state.get("external_operations", [])
            if op.get("id") == email.get("draft_operation_id")
        ]
        if len(operations) != 1:
            raise ValueError("Gmail draft requires one matching external operation")
        operation = operations[0]
        operation_at = confirmed_at(operation.get("approval"), mode)
        expected = (
            "simulated"
            if simulated
            else "uncertain" if status == "email_draft_uncertain" else "succeeded"
        )
        if (
            operation.get("step") != target_step
            or operation.get("mode") != mode
            or operation.get("kind") != "write"
            or operation.get("status") != expected
            or operation.get("inputs", {}).get("payload_sha256") != payload_hash
            or operation.get("inputs", {}).get("account_address")
            != connection["account_address"]
            or not approved <= operation_at <= current
        ):
            raise ValueError(
                "Gmail operation must match the reviewed payload, account, and mode"
            )
        if status == "email_draft_uncertain":
            if email.get("completed_at") is not None:
                raise ValueError("An uncertain Gmail result is not a completed draft")
            return
        if simulated:
            if operation.get("result") is not None or email.get("draft") is not None:
                raise ValueError("Dry-run cannot claim an actual Gmail draft")
        else:
            draft = email.get("draft") or {}
            if (
                status != "gmail_draft_created"
                or not isinstance(draft.get("id"), str)
                or not draft["id"].strip()
                or draft.get("id") != (operation.get("result") or {}).get("draft_id")
                or draft.get("account_address") != connection["account_address"]
                or draft.get("from") != sender["address"]
                or not operation_at
                <= instant(draft.get("created_at"))
                <= instant(email.get("completed_at"))
            ):
                raise ValueError(
                    "Gmail completion requires the returned draft identity and exact sender"
                )
    elif (
        status not in {"manual_email_prepared", "dry_run_email_prepared"}
        or email.get("draft") is not None
        or email.get("draft_operation_id") is not None
    ):
        raise ValueError(
            "Manual handoff cannot claim Gmail creation or an uncertain operation"
        )
    if not approved <= instant(email.get("completed_at")) <= current:
        raise ValueError("Email completion must follow content approval")


def vote_snapshot_sha256(vote):
    snapshot = {
        key: vote.get(key)
        for key in (
            "outcome_source",
            "started_at",
            "minimum_end_at",
            "announced_end_at",
            "outcome_confirmation",
        )
    }
    return hashlib.sha256(
        json.dumps(
            snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def evaluate_vote(state, current):
    vote = state["vote"]
    result = {
        "gate": "awaiting_start",
        "reason": "Ask the release manager when the vote email was sent",
    }
    if vote.get("started_at") is None:
        if any(
            vote.get(key) is not None
            for key in (
                "start_record",
                "minimum_end_at",
                "announced_end_at",
                "outcome_confirmation",
            )
        ):
            raise ValueError(
                "A vote start time is required before recording its deadline or outcome"
            )
        return result
    simulated = state["mode"] == "dry-run"
    started = instant(vote["started_at"])
    start_record = vote.get("start_record")
    recorded = confirmed_at(start_record, state["mode"])
    if (
        start_record.get("source") not in {"release_manager", "prior_record"}
        or start_record.get("simulated") is not simulated
        or not instant(state["email"]["completed_at"]) <= started <= recorded <= current
    ):
        raise ValueError(
            "Vote start requires a manager-supplied or previously recorded actual timestamp"
        )
    minimum = instant(vote.get("minimum_end_at"))
    if minimum != started + timedelta(hours=72):
        raise ValueError("Vote deadline must be its start time plus exactly 72 hours")
    deadline = (
        instant(vote["announced_end_at"])
        if vote.get("announced_end_at") is not None
        else minimum
    )
    if deadline < minimum:
        raise ValueError(
            "An announced vote deadline cannot shorten the 72-hour minimum"
        )
    result.update(
        deadline=deadline.isoformat(),
        seconds_remaining=max(0, (deadline - current).total_seconds()),
    )
    confirmation = vote.get("outcome_confirmation")
    if confirmation is None:
        if current < deadline:
            result.update(
                gate="waiting",
                reason="Wait until the vote deadline before asking the manager for the outcome",
            )
        else:
            result.update(
                gate="awaiting_outcome",
                reason="Ask the release manager whether the vote passed before entering the next step",
            )
        return result
    confirmed = confirmed_at(confirmation, state["mode"])
    if (
        type(confirmation.get("passed")) is not bool
        or confirmation.get("simulated") is not simulated
        or any(
            confirmation.get(key) != state["source_release"][key]
            for key in ("candidate_tag", "prepared_commit")
        )
        or instant(confirmation.get("started_at")) != started
        or instant(confirmation.get("deadline")) != deadline
        or not max(deadline, recorded, instant(vote["entry_confirmation"]["at"]))
        <= confirmed
        <= current
    ):
        raise ValueError(
            "The manager's vote answer must follow the deadline and match this candidate, clock, and mode"
        )
    if confirmation["passed"]:
        result.update(
            gate="passed",
            reason="The release manager confirmed passage after the vote deadline",
        )
    else:
        result.update(
            gate="not_passed",
            reason="The release manager has not confirmed passage; do not enter the next step",
        )
    return result


def check_vote_state(state, current, status=None):
    vote = state.get("vote")
    if not isinstance(vote, dict):
        raise TypeError("Step 5 requires voting state")
    if vote.get("outcome_source") != "release_manager" or any(
        vote.get(key) is not None for key in ("thread", "review", "result_confirmation")
    ):
        raise ValueError(
            "Migrate the older automatic vote record to the release-manager checkpoint; preserve old evidence in history"
        )
    if vote.get("proposal_email_status") not in EMAIL_COMPLETE:
        raise ValueError(
            "Voting requires a completed opening-email draft or manual handoff"
        )
    check_email_state(state, current, status=vote["proposal_email_status"])
    entry = vote.get("entry_confirmation")
    entered = confirmed_at(entry, state["mode"])
    simulated = state["mode"] == "dry-run"
    if (
        entry.get("target_step") != 5
        or entry.get("simulated") is not simulated
        or any(
            entry.get(key) != state["source_release"][key]
            for key in ("candidate_tag", "prepared_commit")
        )
        or not instant(state["email"]["completed_at"]) <= entered <= current
    ):
        raise ValueError(
            "Voting requires separate confirmation for this completed email and candidate"
        )
    result = evaluate_vote(state, current)
    status = state["status"] if status is None else status
    required_gates = {
        "awaiting_vote_start": "awaiting_start",
        "awaiting_vote_outcome": "awaiting_outcome",
        "vote_not_passed": "not_passed",
    }
    if status in required_gates and result["gate"] != required_gates[status]:
        raise ValueError(
            "The saved vote status conflicts with its clock or manager answer"
        )
    result_phase = status in {
        "drafting_vote_result",
        "vote_result_prepared",
        "dry_run_vote_result_prepared",
    }
    passed_status = status in {"vote_passed", "dry_run_vote_passed"}
    if passed_status or result_phase:
        if result["gate"] != "passed":
            raise ValueError(
                "A passed vote or result email requires a positive manager answer after 72 hours"
            )
        if instant(vote.get("passed_at")) != instant(
            vote["outcome_confirmation"]["at"]
        ):
            raise ValueError(
                "Vote passage time must match the manager's positive confirmation"
            )
        if (
            status in {"dry_run_vote_passed", "dry_run_vote_result_prepared"}
        ) != simulated and status != "drafting_vote_result":
            raise ValueError("Vote outcome does not match the release execution mode")
    elif vote.get("passed_at") is not None or state.get("result_email") is not None:
        raise ValueError(
            "An unconfirmed vote cannot retain active passage or result-email claims"
        )
    if result_phase:
        email = state.get("result_email")
        if not isinstance(email, dict) or email.get("status") not in EMAIL_STATUSES:
            raise ValueError("Result email needs a separate email object and status")
        if email.get("vote_snapshot_sha256") != vote_snapshot_sha256(vote):
            raise ValueError(
                "Result drafting must match the current manager-confirmed vote outcome"
            )
        check_email_state(
            state,
            current,
            email=email,
            status=email["status"],
            target_step=5,
            not_before=instant(vote["outcome_confirmation"]["at"]),
        )
        if status != "drafting_vote_result" and email["status"] not in EMAIL_COMPLETE:
            raise ValueError(
                "A prepared vote result requires a completed unsent draft or manual handoff"
            )
    elif state.get("result_email") is not None:
        raise ValueError("Confirm the passed vote before starting its result email")
    return result


def publication_plan_sha256(plan):
    return hashlib.sha256(
        json.dumps(
            plan, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def publication_files(files):
    if not isinstance(files, list) or len(files) != 3:
        raise ValueError(
            "SVN publication requires exactly the three voted artifact files"
        )
    result = {}
    for item in files:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("name"), str)
            or not re.fullmatch(r"[0-9a-f]{128}", item.get("sha512") or "")
        ):
            raise ValueError("Publication files require names and SHA-512 hashes")
        result[item["name"]] = item["sha512"]
    if len(result) != 3:
        raise ValueError("Publication artifact filenames must be distinct")
    return result


def check_publication_component(state, component, current, not_before, *, svn=False):
    if not isinstance(component, dict) or component.get("status") not in PUBLISHED | {
        "pending",
        "blocked",
        "uncertain",
    }:
        raise ValueError("Invalid publication component status")
    status = component["status"]
    plan = component.get("plan")
    complete = status in PUBLISHED
    if not complete and component.get("completed_at") is not None:
        raise ValueError("Incomplete publication cannot claim completion")
    if plan is None:
        if (
            complete
            or component.get("operation_id") is not None
            or component.get("result") is not None
        ):
            raise ValueError("Publication evidence requires its reviewed plan")
        return None
    if not isinstance(plan, dict):
        raise TypeError("Publication plan must be an object")
    mode = state["mode"]
    simulated = mode == "dry-run"
    checked = instant(plan.get("checked_at"))
    if (
        plan.get("mode") != mode
        or plan.get("simulated") is not simulated
        or not not_before <= checked <= current
        or (simulated and not plan.get("evidence_source"))
    ):
        raise ValueError(
            "Publication plan needs current-mode evidence after entry/prerequisites"
        )
    if svn:
        source_url = (
            f"https://dist.apache.org/repos/dist/dev/kvrocks/{state['version']}"
        )
        target = (
            f"https://dist.apache.org/repos/dist/release/kvrocks/{state['version']}"
        )
        artifacts = state["source_release"].get("artifacts")
        if not isinstance(artifacts, list) or any(
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or item.get("status")
            not in ({"actual", "simulated"} if simulated else {"actual"})
            for item in artifacts
        ):
            raise ValueError(
                "Publication requires recorded voted artifacts in the current mode"
            )
        expected_files = publication_files(
            [
                {"name": Path(item["path"]).name, "sha512": item.get("sha512")}
                for item in artifacts
            ]
        )
        archive = f"apache-kvrocks-{state['version']}-src.tar.gz"
        if (
            set(expected_files) != {archive, archive + ".asc", archive + ".sha512"}
            or publication_files(plan.get("files")) != expected_files
            or plan.get("source_url") != source_url
            or state["email"]["artifact_review"]["source_url"].rstrip("/") != source_url
            or plan.get("destination_url") != target
            or type(plan.get("source_revision")) is not int
            or plan["source_revision"] <= 0
            or plan.get("destination_before") not in {"absent", "matching"}
        ):
            raise ValueError(
                "SVN plan must match the voted files, exact directories, and reviewed revision"
            )
        already = plan["destination_before"] == "matching"
        argv = [
            "svnmucc",
            "--revision",
            str(plan["source_revision"]),
            "--message",
            f"Release {state['version']}",
            "mv",
            source_url,
            target,
        ]
    else:
        target = component.get("ref")
        digest = state["docker"]["image"]["digest"]
        source_ref = "apache/kvrocks@" + digest
        previous = plan.get("previous_digest")
        if (
            plan.get("source_ref") != source_ref
            or plan.get("target_ref") != target
            or "previous_digest" not in plan
            or (
                previous is not None
                and not re.fullmatch(r"sha256:[0-9a-f]{64}", previous)
            )
            or (target != "apache/kvrocks:latest" and previous not in {None, digest})
        ):
            raise ValueError(
                "Docker plan must promote the voted digest without overwriting a different version tag"
            )
        already = previous == digest
        argv = ["docker", "buildx", "imagetools", "create", "--tag", target, source_ref]
    operation_id = component.get("operation_id")
    operation = None
    if operation_id is not None:
        matches = [
            item
            for item in state.get("external_operations", [])
            if item.get("id") == operation_id
        ]
        if len(matches) != 1:
            raise ValueError("Publication must identify one exact external operation")
        operation = matches[0]
        if (
            operation.get("step") != 6
            or operation.get("mode") != mode
            or operation.get("target") != target
            or operation.get("kind") != ("read" if already else "write")
            or operation.get("inputs", {}).get("plan_sha256")
            != publication_plan_sha256(plan)
            or not operation.get("request")
            or (not already and operation["request"].get("argv") != argv)
        ):
            raise ValueError(
                "Publication operation must match the exact reviewed plan and command"
            )
    if simulated and component.get("result") is not None:
        raise ValueError("Dry-run publication cannot claim actual remote results")
    if not complete:
        return None
    if simulated != (status == "simulated") or (
        not simulated and already != (status == "already_published")
    ):
        raise ValueError(
            "Publication outcome conflicts with execution mode or preexisting destination"
        )
    if operation is None:
        raise ValueError(
            "Publication completion requires its approved external operation"
        )
    approved = confirmed_at(operation.get("approval"), mode)
    completed = instant(component.get("completed_at"))
    if (
        not (not_before if already else checked) <= approved <= completed <= current
        or operation.get("status") != ("simulated" if simulated else "succeeded")
        or operation.get("result") != component.get("result")
    ):
        raise ValueError(
            "Publication completion must follow the approved operation and retain its outcome"
        )
    if simulated:
        return completed
    result = component.get("result")
    if (
        not isinstance(result, dict)
        or not max(checked, approved) <= instant(result.get("verified_at")) <= completed
    ):
        raise ValueError("Live publication requires verification after approval")
    if svn:
        if (
            publication_files(result.get("files")) != expected_files
            or type(result.get("revision")) is not int
            or result["revision"] < plan["source_revision"]
            or type(result.get("source_absent")) is not bool
            or (
                not already
                and (
                    not result["source_absent"]
                    or result["revision"] == plan["source_revision"]
                )
            )
        ):
            raise ValueError(
                "Published SVN results must retain the voted bytes and verify the move"
            )
    elif (
        result.get("ref") != target
        or result.get("digest") != digest
        or not isinstance(result.get("platforms"), list)
        or not set(state["docker"]["expected_platforms"]).issubset(result["platforms"])
    ):
        raise ValueError(
            "Published Docker target must verify the voted digest and required platforms"
        )
    return completed


def check_publication_state(state, current, status=None):
    publication = state.get("publication")
    if not isinstance(publication, dict) or publication.get("previous_status") not in {
        "vote_result_prepared",
        "dry_run_vote_result_prepared",
    }:
        raise ValueError("Step 6 requires completed vote-result drafting/handoff")
    vote_result = check_vote_state(
        state, current, status=publication["previous_status"]
    )
    entry = publication.get("entry_confirmation")
    mode = state["mode"]
    simulated = mode == "dry-run"
    entered = confirmed_at(entry, mode)
    if (
        entry.get("target_step") != 6
        or entry.get("simulated") is not simulated
        or any(
            entry.get(key) != state["source_release"][key]
            for key in ("candidate_tag", "prepared_commit")
        )
        or entry.get("vote_snapshot_sha256") != vote_snapshot_sha256(state["vote"])
        or entry.get("docker_digest") != state["docker"]["image"]["digest"]
        or not instant(state["result_email"]["completed_at"]) <= entered <= current
    ):
        raise ValueError(
            "Publication needs separate entry approval for this completed result, candidate, vote, and image"
        )
    svn_completed = check_publication_component(
        state, publication.get("svn"), current, entered, svn=True
    )
    docker = publication.get("docker")
    targets = docker.get("targets") if isinstance(docker, dict) else None
    expected = {f"apache/kvrocks:{state['version']}", "apache/kvrocks:latest"}
    if (
        not isinstance(targets, list)
        or len(targets) != 2
        or any(not isinstance(t, dict) for t in targets)
        or {t.get("ref") for t in targets} != expected
    ):
        raise ValueError(
            "Publication requires the exact version and latest Docker targets"
        )
    docker_completed = []
    for target in targets:
        if svn_completed is None and (
            target.get("plan") is not None or target.get("status") in PUBLISHED
        ):
            raise ValueError("Complete SVN publication before Docker promotion")
        docker_completed.append(
            check_publication_component(
                state, target, current, svn_completed or entered
            )
        )
    ready = svn_completed is not None and all(t is not None for t in docker_completed)
    notes = publication.get("github_release_notes")
    if not isinstance(notes, dict) or notes.get("status") not in {
        "pending",
        "awaiting_manager",
        "published",
        "simulated",
    }:
        raise ValueError("Publication requires a manual GitHub release-note checkpoint")
    confirmation = notes.get("confirmation")
    if notes["status"] == "pending":
        if notes.get("handoff") is not None or confirmation is not None:
            raise ValueError(
                "Pending GitHub release notes cannot claim a handoff or publication"
            )
    else:
        handoff = notes.get("handoff")
        if not ready or not isinstance(handoff, dict):
            raise ValueError(
                "Complete SVN and both Docker tags before the GitHub handoff"
            )
        handed = instant(handoff.get("at"))
        if (
            handoff.get("mode") != mode
            or handoff.get("simulated") is not simulated
            or handoff.get("tag") != f"v{state['version']}"
            or handoff.get("commit") != state["source_release"]["prepared_commit"]
            or not isinstance(handoff.get("content"), str)
            or not handoff["content"].strip()
            or not max([svn_completed, *docker_completed]) <= handed <= current
        ):
            raise ValueError(
                "GitHub handoff must identify the voted commit and final tag after publication"
            )
        if notes["status"] == "awaiting_manager":
            if confirmation is not None:
                raise ValueError("Record the manager's GitHub outcome explicitly")
        else:
            confirmed = confirmed_at(confirmation, mode)
            if (
                (notes["status"] == "simulated") != simulated
                or confirmation.get("simulated") is not simulated
                or confirmation.get("completed") is not True
                or confirmation.get("tag") != handoff["tag"]
                or confirmation.get("commit") != handoff["commit"]
                or not handed <= confirmed <= current
                or (simulated and confirmation.get("url") is not None)
                or (
                    not simulated
                    and confirmation.get("url")
                    != f"https://github.com/apache/kvrocks/releases/tag/v{state['version']}"
                )
            ):
                raise ValueError(
                    "GitHub completion requires the manager's matching publication report or rehearsal acknowledgment"
                )
    status = state["status"] if status is None else status
    if (
        status == "awaiting_github_release_notes"
        and notes["status"] != "awaiting_manager"
    ):
        raise ValueError(
            "Awaiting GitHub publication requires the saved manual handoff"
        )
    if status in {"publication_complete", "dry_run_publication_complete"}:
        if (
            not ready
            or (status == "dry_run_publication_complete") != simulated
            or notes["status"] != ("simulated" if simulated else "published")
            or not instant(confirmation["at"])
            <= instant(publication.get("completed_at"))
            <= current
        ):
            raise ValueError(
                "Complete publication requires all components and the manager's GitHub confirmation"
            )
    elif publication.get("completed_at") is not None:
        raise ValueError("Unfinished publication cannot retain overall completion")
    return vote_result


def website_push_sha256(plan):
    return publication_plan_sha256(
        {
            key: plan.get(key)
            for key in (
                "head_repository",
                "head_branch",
                "head_commit",
                "files",
                "diff",
            )
        }
    )


def website_pr_sha256(plan):
    return publication_plan_sha256(
        {
            key: plan.get(key)
            for key in (
                "base_branch",
                "base_commit",
                "head_repository",
                "head_branch",
                "head_commit",
                "files",
                "diff",
                "title",
                "body",
                "draft",
                "links",
            )
        }
    )


def website_release_links(version):
    archive = f"apache-kvrocks-{version}-src.tar.gz"
    download = f"https://downloads.apache.org/kvrocks/{version}/{archive}"
    return {
        "archive": f"https://www.apache.org/dyn/closer.lua/kvrocks/{version}/{archive}",
        "checksum": download + ".sha512",
        "signature": download + ".asc",
        "github": f"https://github.com/apache/kvrocks/releases/tag/v{version}",
    }


def check_website_operation(
    state, operation_id, payload_hash, target, current, not_before
):
    matches = [
        op
        for op in state.get("external_operations", [])
        if op.get("id") == operation_id
    ]
    if operation_id is None or len(matches) != 1:
        raise ValueError("Website outcome requires one exact recorded operation")
    op = matches[0]
    simulated = state["mode"] == "dry-run"
    if op.get("kind") == "read" and not simulated and op.get("approval") is None:
        operation_at = instant(op.get("checked_at"))
    else:
        operation_at = confirmed_at(op.get("approval"), state["mode"])
    if (
        op.get("step") != 7
        or op.get("mode") != state["mode"]
        or op.get("target") != target
        or op.get("kind") not in {"read", "write"}
        or not op.get("request")
        or op.get("inputs", {}).get("payload_sha256") != payload_hash
        or not not_before <= operation_at <= current
        or op.get("status") != ("simulated" if simulated else "succeeded")
        or (simulated and op.get("result") is not None)
    ):
        raise ValueError(
            "Website operation must match its recorded payload, destination, mode, and time"
        )
    return op, operation_at


def check_website_state(state, current, status=None):
    website = state.get("website")
    if not isinstance(website, dict) or website.get("previous_status") not in {
        "publication_complete",
        "dry_run_publication_complete",
    }:
        raise ValueError(
            "Step 7 requires completed publication and GitHub release notes"
        )
    vote_result = check_publication_state(
        state, current, status=website["previous_status"]
    )
    mode = state["mode"]
    simulated = mode == "dry-run"
    entry = website.get("entry_confirmation")
    entered = confirmed_at(entry, mode)
    if (
        website.get("repository") != WEBSITE_REPOSITORY
        or website.get("file") != WEBSITE_FILE
        or entry.get("target_step") != 7
        or entry.get("mode") != mode
        or entry.get("simulated") is not simulated
        or entry.get("version") != state["version"]
        or entry.get("publication_sha256")
        != publication_plan_sha256(state["publication"])
        or not instant(state["publication"]["completed_at"]) <= entered <= current
    ):
        raise ValueError(
            "Website entry must confirm the completed release and separate website repository"
        )
    status = state["status"] if status is None else status
    complete = status in {
        "website_pr_created",
        "dry_run_website_pr_prepared",
        "website_already_updated",
    }
    if not complete and website.get("completed_at") is not None:
        raise ValueError("Unfinished website work cannot claim completion")
    if simulated and website.get("pr") is not None:
        raise ValueError("Dry-run website work cannot claim a real PR")
    existing = website.get("existing_update")
    if status == "website_already_updated":
        if not isinstance(existing, dict) or any(
            website.get(key) is not None
            for key in ("plan", "pr", "push_operation_id", "pr_operation_id")
        ):
            raise ValueError(
                "An existing website update needs verified base-branch evidence without new writes"
            )
        if (
            existing.get("repository") != WEBSITE_REPOSITORY
            or existing.get("file") != WEBSITE_FILE
            or existing.get("version") != state["version"]
            or existing.get("links") != website_release_links(state["version"])
            or existing.get("mode") != mode
            or existing.get("simulated") is not simulated
            or not existing.get("base_branch")
            or not re.fullmatch(r"[0-9a-f]{40}", existing.get("base_commit") or "")
        ):
            raise ValueError(
                "Existing website entry must match this final release and base commit"
            )
        op, approved = check_website_operation(
            state,
            existing.get("operation_id"),
            publication_plan_sha256(existing),
            WEBSITE_REPOSITORY,
            current,
            entered,
        )
        if (
            op["kind"] != "read"
            or (not simulated and op.get("result") != existing)
            or not approved
            <= instant(existing.get("verified_at"))
            <= instant(website.get("completed_at"))
            <= current
        ):
            raise ValueError(
                "Already-updated completion requires recorded read verification"
            )
        return vote_result
    if existing is not None:
        raise ValueError("Record an already-present website entry as its own outcome")
    plan = website.get("plan")
    if plan is None:
        if (
            complete
            or status not in {"preparing_website_pr", "website_pr_blocked"}
            or any(
                website.get(key) is not None
                for key in ("push_operation_id", "pr_operation_id", "pr")
            )
        ):
            raise ValueError("Website PR work needs its concrete local plan")
        return vote_result
    if not isinstance(plan, dict):
        raise TypeError("Website plan must be an object")
    prepared = instant(plan.get("prepared_at"))
    if (
        plan.get("mode") != mode
        or plan.get("simulated") is not simulated
        or (simulated and not plan.get("evidence_source"))
        or not entered <= prepared <= current
        or plan.get("files") != [WEBSITE_FILE]
        or plan.get("links") != website_release_links(state["version"])
        or any(
            not isinstance(plan.get(key), str) or not plan[key].strip()
            for key in (
                "base_branch",
                "head_repository",
                "head_branch",
                "title",
                "body",
                "diff",
            )
        )
        or re.findall(r"^diff --git a/(\S+) b/(\S+)$", plan["diff"], re.MULTILINE)
        != [(WEBSITE_FILE, WEBSITE_FILE)]
        or plan["head_branch"] in {plan["base_branch"], "main", "asf-site"}
        or any(
            not re.fullmatch(r"[0-9a-f]{40}", plan.get(key) or "")
            for key in ("base_commit", "head_commit")
        )
        or type(plan.get("draft")) is not bool
        or not isinstance(plan.get("checks"), list)
        or not isinstance(plan.get("blockers"), list)
    ):
        raise ValueError(
            "Website plan must contain the scoped final-release diff, links, branches, commit, and PR payload"
        )
    if not complete:
        return vote_result
    link_check = plan.get("link_check")
    if (
        (status == "dry_run_website_pr_prepared") != simulated
        or plan["blockers"]
        or not plan["checks"]
        or not isinstance(link_check, dict)
        or link_check.get("status") != "passed"
        or link_check.get("mode") != mode
        or link_check.get("simulated") is not simulated
        or not entered <= instant(link_check.get("at")) <= prepared
        or any(
            not isinstance(check, dict)
            or check.get("status") != "passed"
            or not check.get("command")
            or not entered <= instant(check.get("at")) <= prepared
            for check in plan["checks"]
        )
    ):
        raise ValueError(
            "Website PR completion requires successful validation and matching execution mode"
        )
    push, pushed = check_website_operation(
        state,
        website.get("push_operation_id"),
        website_push_sha256(plan),
        plan["head_repository"],
        current,
        entered,
    )
    pr_op, approved = check_website_operation(
        state,
        website.get("pr_operation_id"),
        website_pr_sha256(plan),
        WEBSITE_REPOSITORY,
        current,
        entered,
    )
    completed = instant(website.get("completed_at"))
    if (
        not max(prepared, pushed, approved) <= completed <= current
        or (push["kind"] == "write" and pushed < prepared)
        or (pr_op["kind"] == "write" and approved < prepared)
    ):
        raise ValueError(
            "Website completion must follow verified reads or approved writes"
        )
    if simulated:
        return vote_result
    push_result = push.get("result")
    pr = website.get("pr")
    if (
        not isinstance(push_result, dict)
        or push_result.get("repository") != plan["head_repository"]
        or push_result.get("branch") != plan["head_branch"]
        or push_result.get("commit") != plan["head_commit"]
        or not pushed <= instant(push_result.get("verified_at")) <= completed
        or not isinstance(pr, dict)
        or pr_op.get("result") != pr
        or pr.get("repository") != WEBSITE_REPOSITORY
        or type(pr.get("number")) is not int
        or pr["number"] <= 0
        or pr.get("url")
        != f"https://github.com/{WEBSITE_REPOSITORY}/pull/{pr['number']}"
        or any(
            pr.get(key) != plan[key]
            for key in (
                "base_branch",
                "head_repository",
                "head_branch",
                "head_commit",
                "title",
                "body",
                "draft",
            )
        )
        or not max(approved, instant(push_result["verified_at"]))
        <= instant(pr.get("verified_at"))
        <= completed
    ):
        raise ValueError(
            "Live website PR must verify the approved remote branch, PR identity, and complete payload"
        )
    return vote_result


def check_announcement_state(state, current):
    announcement = state.get("announcement")
    if not isinstance(announcement, dict) or announcement.get(
        "previous_status"
    ) not in {
        "website_pr_created",
        "dry_run_website_pr_prepared",
        "website_already_updated",
    }:
        raise ValueError("Final announcement requires a completed website step")
    vote_result = check_website_state(
        state, current, status=announcement["previous_status"]
    )
    mode = state["mode"]
    simulated = mode == "dry-run"
    entry = announcement.get("entry_confirmation")
    entered = confirmed_at(entry, mode)
    if (
        entry.get("target_step") != 8
        or entry.get("version") != state["version"]
        or entry.get("simulated") is not simulated
        or entry.get("website_sha256") != publication_plan_sha256(state["website"])
        or not instant(state["website"]["completed_at"]) <= entered <= current
    ):
        raise ValueError(
            "Announcement entry must confirm this completed website step and release"
        )
    status = state["status"]
    handoff = announcement.get("handoff")
    confirmation = announcement.get("send_confirmation")
    complete = status in {"release_complete", "dry_run_release_complete"}
    if not complete and (
        confirmation is not None or announcement.get("completed_at") is not None
    ):
        raise ValueError(
            "An announcement handoff alone cannot claim sending or release completion"
        )
    if handoff is None:
        if status != "preparing_announcement_handoff":
            raise ValueError(
                "Record the concrete manual announcement handoff before awaiting completion"
            )
        return vote_result
    if not isinstance(handoff, dict):
        raise TypeError("Announcement handoff must be an object")
    handed = instant(handoff.get("at"))
    if (
        status == "preparing_announcement_handoff"
        or handoff.get("mode") != mode
        or handoff.get("simulated") is not simulated
        or handoff.get("version") != state["version"]
        or handoff.get("to") != ["dev@kvrocks.apache.org"]
        or handoff.get("cc") != ["announce@apache.org"]
        or handoff.get("from_domain") != "apache.org"
        or handoff.get("links") != website_release_links(state["version"])
        or not isinstance(handoff.get("content"), str)
        or not handoff["content"].strip()
        or not entered <= handed <= current
    ):
        raise ValueError(
            "Announcement handoff must match this final release, recipients, sender requirement, and mode"
        )
    if not complete:
        return vote_result
    confirmed = confirmed_at(confirmation, mode)
    if (
        (status == "dry_run_release_complete") != simulated
        or confirmation.get("simulated") is not simulated
        or confirmation.get("version") != state["version"]
        or confirmation.get("handoff_sha256") != publication_plan_sha256(handoff)
        or confirmation.get("outcome") != ("simulated" if simulated else "sent")
        or not handed
        <= confirmed
        <= instant(announcement.get("completed_at"))
        <= current
        or (
            simulated
            and any(
                confirmation.get(key) is not None for key in ("sent_at", "message_url")
            )
        )
        or state.get("next_action") is not None
    ):
        raise ValueError(
            "Release completion requires the manager's matching send report or dry-run acknowledgment and no pending action"
        )
    if (
        confirmation.get("sent_at") is not None
        and instant(confirmation["sent_at"]) > confirmed
    ):
        raise ValueError(
            "A reported send time cannot follow the manager's confirmation"
        )
    return vote_result


def inspect_record(path, now=None):
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise TypeError("Release state must be an object")
    version = state.get("version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("Invalid release version")
    if path.name != "release-state.json" or path.parent.name != f"release-{version}":
        raise ValueError(
            "State path must be release-VERSION/release-state.json and match its version"
        )
    if (
        state.get("schema_version") != 1
        or state.get("repository") != "apache/kvrocks"
        or not (
            (state.get("step") == 1 and state.get("status") in STATUSES)
            or (state.get("step") == 2 and state.get("status") in SOURCE_STATUSES)
            or (state.get("step") == 3 and state.get("status") in DOCKER_STATUSES)
            or (
                state.get("step") == 4
                and state.get("status") in EMAIL_STATUSES | VERIFICATION_STATUSES
            )
            or (state.get("step") == 5 and state.get("status") in VOTE_STATUSES)
            or (state.get("step") == 6 and state.get("status") in PUBLICATION_STATUSES)
            or (state.get("step") == 7 and state.get("status") in WEBSITE_STATUSES)
            or (state.get("step") == 8 and state.get("status") in ANNOUNCEMENT_STATUSES)
        )
        or state.get("mode") not in {"dry-run", "live"}
    ):
        raise ValueError(
            "Unsupported release schema, repository, step, mode, or status"
        )
    deadline = state.get("cherry_pick_deadline")
    deadline_at = instant(deadline) if deadline is not None else None
    rule = state.get("cherry_pick_deadline_rule")
    if rule is not None and (
        not isinstance(rule, dict)
        or rule.get("anchor") != "discussion_created_at"
        or type(rule.get("offset_seconds")) is not int
        or rule["offset_seconds"] <= 0
    ):
        raise ValueError(
            "Deadline rule requires discussion_created_at and a positive integer offset_seconds"
        )
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("Current time must include a timezone")
    gate = "blocked"
    vote_evaluation = None
    reason = (
        "Release-manager confirmation and a recorded discussion outcome are required"
    )
    if (
        state["status"]
        in WAITING
        | SOURCE_STATUSES
        | DOCKER_STATUSES
        | EMAIL_STATUSES
        | VERIFICATION_STATUSES
        | VOTE_STATUSES
        | PUBLICATION_STATUSES
        | WEBSITE_STATUSES
        | ANNOUNCEMENT_STATUSES
    ):
        approval = state.get("approval")
        exclusions = state.get("exclusions")
        discussion = state.get("discussion")
        if (
            not isinstance(approval, dict)
            or approval.get("mode") != state["mode"]
            or not isinstance(approval.get("by"), str)
            or not approval["by"].strip()
            or not isinstance(exclusions, list)
            or any(not isinstance(item, str) or not item.strip() for item in exclusions)
            or not isinstance(state.get("proposed_commit"), str)
            or not re.fullmatch(r"[0-9a-fA-F]{40}", state["proposed_commit"])
            or deadline_at is None
            or not isinstance(discussion, dict)
        ):
            raise ValueError(
                "Waiting record is missing confirmed inputs or matching approval"
            )
        instant(approval.get("at"))
        if state["mode"] == "dry-run":
            if (
                state["status"] == "waiting_for_cherry_picks"
                or discussion.get("url") is not None
                or discussion.get("created_at") is not None
            ):
                raise ValueError("Dry-run state cannot claim a published discussion")
            started = instant(discussion.get("simulated_at"))
        else:
            if state["status"] == "dry_run_waiting" or not re.fullmatch(
                r"https://github\.com/apache/kvrocks/discussions/[1-9][0-9]*",
                discussion.get("url") or "",
            ):
                raise ValueError(
                    "Live waiting state requires a real Kvrocks discussion URL"
                )
            started = instant(discussion.get("created_at"))
        if started >= deadline_at:
            raise ValueError(
                "The deadline must be later than discussion creation or simulation"
            )
        if (
            rule is not None
            and (deadline_at - started).total_seconds() != rule["offset_seconds"]
        ):
            raise ValueError(
                "Recorded deadline does not match the creation time plus the approved duration"
            )
        if current >= deadline_at:
            gate = "elapsed"
            reason = (
                "Time gate elapsed only; review discussion objections and obtain explicit "
                "release-manager confirmation before entering a defined next step"
            )
        else:
            reason = "Cherry-pick deadline has not arrived; do not begin the next step"
        if state["status"] == "deadline_elapsed" and gate != "elapsed":
            raise ValueError("Saved elapsed status conflicts with the current deadline")
        if state["step"] >= 2:
            check_source_transition(state, deadline_at, current)
            reason = "Step 2 active; GitHub status reads need no approval; other external operations require a confirmed preview"
        if state["step"] >= 3:
            check_docker_state(state, current, require_ready=state["step"] >= 4)
            reason = "Step 3 active; GitHub status polling needs no approval; registry reads require confirmed scope"
        if state["step"] == 4:
            if state["status"] in VERIFICATION_STATUSES:
                check_candidate_verification(state, current)
                if (
                    state["candidate_verification"]["status"] != state["status"]
                    or state.get("email") is not None
                ):
                    raise ValueError(
                        "Verification phase must retain its status and cannot begin email drafting"
                    )
                reason = "Step 4a active; verify the uploaded candidate and confirm entry to email drafting after all checks pass"
            else:
                check_email_state(state, current)
                reason = "Step 4b active; confirm sender before composing; a draft or manual handoff is not sent mail"
        if state["step"] == 5:
            vote_evaluation = check_vote_state(state, current)
            reason = "Step 5 active; " + vote_evaluation["reason"]
        if state["step"] == 6:
            vote_evaluation = check_publication_state(state, current)
            reason = "Step 6 active; inspect each publication outcome and the manual GitHub checkpoint; dry-run never authorizes external writes"
        if state["step"] == 7:
            vote_evaluation = check_website_state(state, current)
            reason = "Step 7 active; review the website diff and PR payload before approved external writes; a PR does not imply merge or deployment"
        if state["step"] == 8:
            vote_evaluation = check_announcement_state(state, current)
            reason = "Final step; ask the manager to send the announcement and wait for their confirmation; do not send mail automatically"
            if state["status"] == "release_complete":
                reason = "Release process complete: the manager reported sending the announcement; stop without repeating release actions"
            elif state["status"] == "dry_run_release_complete":
                reason = "Dry-run release process complete: the manager acknowledged the simulated announcement handoff; no real send is claimed"
    elif state["status"] == "publication_uncertain":
        reason = (
            "Reconcile the uncertain GitHub publication before retrying or advancing"
        )
    return {
        "record": str(path),
        "state": state,
        "checked_at": current.astimezone(timezone.utc).isoformat(),
        "deadline_gate": gate,
        "seconds_remaining": (
            max(0, (deadline_at - current).total_seconds())
            if deadline_at is not None
            else None
        ),
        "reason": reason,
        "vote_evaluation": vote_evaluation,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_record(args.record.expanduser())
    except (OSError, ValueError, TypeError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["deadline_gate"] == "elapsed" else 1


if __name__ == "__main__":
    sys.exit(main())
