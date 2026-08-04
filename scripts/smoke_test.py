#!/usr/bin/env python
"""
End-to-end smoke test for Intelligent Mailroom.

Checks:
1. Maarch connectivity and user mode
2. Email/IMAP connectivity
3. Classification pipeline
4. Optional mailbox poll (when --poll is passed)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings
from src.email import EmailIngestionService, ImapClient
from src.maarch import get_maarch_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Intelligent Mailroom smoke test")
    parser.add_argument("--poll", action="store_true", help="Run one email poll/ingest cycle")
    parser.add_argument("--limit", type=int, default=1, help="Max emails to ingest with --poll")
    args = parser.parse_args()

    settings = get_settings()
    failures: list[str] = []

    print("=== Intelligent Mailroom Smoke Test ===")

    try:
        maarch = get_maarch_service()
        connection = maarch.validate_connection()
        print(f"[OK] Maarch connected: {connection.get('application_name')}")
        print(f"     User: {connection.get('current_user')} (mode={connection.get('current_user_mode')})")
        for warning in connection.get("warnings", []):
            print(f"[WARN] {warning}")
        if not connection.get("webservice_ready"):
            failures.append("Maarch user is not configured as a dedicated WebService account")
    except Exception as exc:
        failures.append(f"Maarch connection failed: {exc}")
        print(f"[FAIL] Maarch connection failed: {exc}")

    if settings.email_host and settings.email_username and settings.email_password:
        try:
            mailbox = ImapClient(settings).ping()
            print(f"[OK] IMAP connected: {mailbox.get('host')} ({mailbox.get('message_count')} messages)")
        except Exception as exc:
            failures.append(f"IMAP connection failed: {exc}")
            print(f"[FAIL] IMAP connection failed: {exc}")
    else:
        print("[SKIP] Email/IMAP not configured")

    try:
        from src.ai import get_document_analysis_pipeline

        pipeline = get_document_analysis_pipeline(maarch.reference if "maarch" in locals() else None)
        result = pipeline.analyze(
            subject="Facture fournisseur",
            body_text="Merci de traiter la facture jointe.",
            sender="billing@example.com",
        )
        print(
            "[OK] Classification: "
            f"{result.classification.category} -> {result.classification.destination_entity_id}"
        )
    except Exception as exc:
        failures.append(f"Classification failed: {exc}")
        print(f"[FAIL] Classification failed: {exc}")

    if args.poll:
        if not (settings.email_host and settings.email_username and settings.email_password):
            failures.append("Cannot poll mailbox: IMAP is not configured")
            print("[FAIL] Cannot poll mailbox: IMAP is not configured")
        else:
            try:
                service = EmailIngestionService()
                poll_result = service.poll_and_ingest(limit=args.limit)
                print(
                    "[OK] Email poll: "
                    f"fetched={poll_result.fetched} ingested={poll_result.ingested} "
                    f"skipped={poll_result.skipped} failed={poll_result.failed}"
                )
                for item in poll_result.results:
                    if item.res_id:
                        print(f"     res_id={item.res_id} subject={item.subject!r}")
                for error in poll_result.errors:
                    print(f"[FAIL] {error}")
                    failures.append(error)
            except Exception as exc:
                failures.append(f"Email poll failed: {exc}")
                print(f"[FAIL] Email poll failed: {exc}")

    print("=== Summary ===")
    if failures:
        print(f"FAILED ({len(failures)} issue(s))")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
