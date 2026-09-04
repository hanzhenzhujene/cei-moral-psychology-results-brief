from __future__ import annotations

import os
import signal
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.publish_slides import (
    ReleaseError,
    TerminationRequested,
    acquire_release_lock,
    describe_interrupted_release,
    publish_with_rollback,
    release_release_lock,
    sha256,
)


class PublishSlidesTransactionTests(unittest.TestCase):
    def make_plan(
        self, root: Path
    ) -> tuple[list[tuple[Path, Path]], dict[Path, str], dict[Path, str]]:
        stage = root / "stage"
        public = root / "public"
        stage.mkdir()
        public.mkdir()
        plan: list[tuple[Path, Path]] = []
        old_hashes: dict[Path, str] = {}
        new_hashes: dict[Path, str] = {}
        for index in range(11):
            source = stage / f"artifact-{index:02d}"
            target = public / f"artifact-{index:02d}"
            source.write_bytes(f"new-{index}".encode())
            target.write_bytes(f"old-{index}".encode())
            plan.append((source, target))
            old_hashes[target] = sha256(target)
            new_hashes[target] = sha256(source)
        return plan, old_hashes, new_hashes

    def assert_hashes(self, expected: dict[Path, str]) -> None:
        self.assertEqual({path: sha256(path) for path in expected}, expected)

    def test_failure_after_each_replace_restores_all_eleven_files(self) -> None:
        for fail_after in range(1, 12):
            with (
                self.subTest(fail_after=fail_after),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                plan, old_hashes, _ = self.make_plan(root)
                backup = root / "backup"
                backup.mkdir()

                def validate_restored() -> str:
                    self.assert_hashes(old_hashes)
                    return "VALIDATION PASSED"

                with self.assertRaisesRegex(ReleaseError, "restored from backup"):
                    publish_with_rollback(plan, backup, validate_restored, fail_after)
                self.assert_hashes(old_hashes)
                self.assertEqual(list((root / "public").glob(".*.new")), [])
                self.assertEqual(list((root / "public").glob(".*.restore")), [])

    def test_public_validation_failure_rolls_back_and_revalidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, old_hashes, new_hashes = self.make_plan(root)
            backup = root / "backup"
            backup.mkdir()
            calls = 0

            def validate_public() -> str:
                nonlocal calls
                calls += 1
                if calls == 1:
                    self.assert_hashes(new_hashes)
                    raise ReleaseError("forced public validation failure")
                self.assert_hashes(old_hashes)
                return "VALIDATION PASSED"

            with self.assertRaisesRegex(ReleaseError, "restored from backup"):
                publish_with_rollback(plan, backup, validate_public)
            self.assertEqual(calls, 2)
            self.assert_hashes(old_hashes)

    def test_replace_failure_at_each_file_restores_prior_files(self) -> None:
        for fail_at in range(1, 12):
            with (
                self.subTest(fail_at=fail_at),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                plan, old_hashes, _ = self.make_plan(root)
                backup = root / "backup"
                backup.mkdir()
                real_replace = os.replace
                replacements = 0

                def fail_one_replace(source: Path, target: Path) -> None:
                    nonlocal replacements
                    if Path(source).name.endswith(".new"):
                        replacements += 1
                        if replacements == fail_at:
                            raise OSError("forced os.replace failure")
                    real_replace(source, target)

                def validate_restored() -> str:
                    self.assert_hashes(old_hashes)
                    return "VALIDATION PASSED"

                with (
                    mock.patch(
                        "scripts.publish_slides.os.replace",
                        side_effect=fail_one_replace,
                    ),
                    self.assertRaisesRegex(ReleaseError, "restored from backup"),
                ):
                    publish_with_rollback(plan, backup, validate_restored)
                self.assert_hashes(old_hashes)

    def test_keyboard_interrupt_rolls_back_before_propagating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, old_hashes, _ = self.make_plan(root)
            backup = root / "backup"
            backup.mkdir()
            real_replace = os.replace
            replacements = 0

            def interrupt_fourth_replace(source: Path, target: Path) -> None:
                nonlocal replacements
                if Path(source).name.endswith(".new"):
                    replacements += 1
                    if replacements == 4:
                        raise KeyboardInterrupt
                real_replace(source, target)

            def validate_restored() -> str:
                self.assert_hashes(old_hashes)
                return "VALIDATION PASSED"

            with (
                mock.patch(
                    "scripts.publish_slides.os.replace",
                    side_effect=interrupt_fourth_replace,
                ),
                self.assertRaises(KeyboardInterrupt),
            ):
                publish_with_rollback(plan, backup, validate_restored)
            self.assert_hashes(old_hashes)

    @unittest.skipUnless(
        hasattr(signal, "pthread_sigmask"), "POSIX signal masks are required"
    )
    def test_real_sigint_during_validation_rolls_back_before_propagating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, old_hashes, new_hashes = self.make_plan(root)
            backup = root / "backup"
            backup.mkdir()
            before_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())

            def validate_new_release() -> str:
                self.assert_hashes(new_hashes)
                os.kill(os.getpid(), signal.SIGINT)
                return "VALIDATION PASSED"

            def validate_restored_release() -> str:
                self.assert_hashes(old_hashes)
                return "SLIDE EXPORT INTEGRITY PASSED"

            with self.assertRaises(KeyboardInterrupt):
                publish_with_rollback(
                    plan,
                    backup,
                    validate_new_release,
                    validate_rollback=validate_restored_release,
                )
            self.assert_hashes(old_hashes)
            self.assertEqual(list((root / "public").glob(".*.new")), [])
            self.assertEqual(list((root / "public").glob(".*.restore")), [])
            after_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
            self.assertEqual(after_mask, before_mask)

    @unittest.skipUnless(
        hasattr(signal, "pthread_sigmask"), "POSIX signal masks are required"
    )
    def test_real_sigterm_during_validation_rolls_back_before_propagating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, old_hashes, new_hashes = self.make_plan(root)
            backup = root / "backup"
            backup.mkdir()
            before_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
            before_handler = signal.getsignal(signal.SIGTERM)

            def validate_new_release() -> str:
                self.assert_hashes(new_hashes)
                os.kill(os.getpid(), signal.SIGTERM)
                return "VALIDATION PASSED"

            def validate_restored_release() -> str:
                self.assert_hashes(old_hashes)
                return "SLIDE EXPORT INTEGRITY PASSED"

            with self.assertRaises(TerminationRequested):
                publish_with_rollback(
                    plan,
                    backup,
                    validate_new_release,
                    validate_rollback=validate_restored_release,
                )
            self.assert_hashes(old_hashes)
            after_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
            self.assertEqual(after_mask, before_mask)
            self.assertEqual(signal.getsignal(signal.SIGTERM), before_handler)

    @unittest.skipUnless(
        hasattr(signal, "pthread_sigmask"), "POSIX signal masks are required"
    )
    def test_cleanup_failure_still_restores_signal_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, old_hashes, _ = self.make_plan(root)
            backup = root / "backup"
            backup.mkdir()
            before_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
            before_handler = signal.getsignal(signal.SIGTERM)
            real_unlink = Path.unlink

            def fail_candidate_cleanup(
                path: Path, missing_ok: bool = False
            ) -> None:
                if path.name.endswith(".new"):
                    raise OSError("forced candidate cleanup failure")
                real_unlink(path, missing_ok=missing_ok)

            def validate_restored_release() -> str:
                self.assert_hashes(old_hashes)
                return "SLIDE EXPORT INTEGRITY PASSED"

            with (
                mock.patch.object(Path, "unlink", new=fail_candidate_cleanup),
                self.assertRaisesRegex(OSError, "forced candidate cleanup failure"),
            ):
                publish_with_rollback(
                    plan,
                    backup,
                    validate_restored_release,
                    fail_after=1,
                )
            after_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
            self.assertEqual(after_mask, before_mask)
            self.assertEqual(signal.getsignal(signal.SIGTERM), before_handler)

    @unittest.skipUnless(
        hasattr(signal, "pthread_sigmask"), "POSIX signal masks are required"
    )
    def test_real_sigint_during_success_cleanup_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, old_hashes, new_hashes = self.make_plan(root)
            backup = root / "backup"
            backup.mkdir()
            real_unlink = Path.unlink
            interrupted = False

            def interrupt_first_candidate_cleanup(
                path: Path, missing_ok: bool = False
            ) -> None:
                nonlocal interrupted
                if path.name.endswith(".new") and not interrupted:
                    interrupted = True
                    os.kill(os.getpid(), signal.SIGINT)
                real_unlink(path, missing_ok=missing_ok)

            def validate_new_release() -> str:
                self.assert_hashes(new_hashes)
                return "VALIDATION PASSED"

            def validate_restored_release() -> str:
                self.assert_hashes(old_hashes)
                return "SLIDE EXPORT INTEGRITY PASSED"

            with (
                mock.patch.object(
                    Path, "unlink", new=interrupt_first_candidate_cleanup
                ),
                self.assertRaises(KeyboardInterrupt),
            ):
                publish_with_rollback(
                    plan,
                    backup,
                    validate_new_release,
                    validate_rollback=validate_restored_release,
                )
            self.assertTrue(interrupted)
            self.assert_hashes(old_hashes)

    def test_cleanup_failure_after_validation_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, old_hashes, new_hashes = self.make_plan(root)
            backup = root / "backup"
            backup.mkdir()
            real_unlink = Path.unlink
            failed = False

            def fail_first_candidate_cleanup(
                path: Path, missing_ok: bool = False
            ) -> None:
                nonlocal failed
                if path.name.endswith(".new") and not failed:
                    failed = True
                    raise OSError("forced success-path cleanup failure")
                real_unlink(path, missing_ok=missing_ok)

            def validate_new_release() -> str:
                self.assert_hashes(new_hashes)
                return "VALIDATION PASSED"

            def validate_restored_release() -> str:
                self.assert_hashes(old_hashes)
                return "SLIDE EXPORT INTEGRITY PASSED"

            with (
                mock.patch.object(Path, "unlink", new=fail_first_candidate_cleanup),
                self.assertRaisesRegex(ReleaseError, "restored from backup"),
            ):
                publish_with_rollback(
                    plan,
                    backup,
                    validate_new_release,
                    validate_rollback=validate_restored_release,
                )
            self.assertTrue(failed)
            self.assert_hashes(old_hashes)

    def test_second_writer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            lock_path = Path(temporary) / "release.lock"
            first = acquire_release_lock(lock_path)
            try:
                with self.assertRaisesRegex(
                    ReleaseError, "another slide publisher is already running"
                ):
                    acquire_release_lock(lock_path)
            finally:
                release_release_lock(first)
            second = acquire_release_lock(lock_path)
            release_release_lock(second)

    def test_success_publishes_all_eleven_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan, _, new_hashes = self.make_plan(root)
            backup = root / "backup"
            backup.mkdir()

            def validate_public() -> str:
                self.assert_hashes(new_hashes)
                return "VALIDATION PASSED"

            receipt = publish_with_rollback(plan, backup, validate_public)
            self.assertIn("VALIDATION PASSED", receipt)
            self.assert_hashes(new_hashes)

    def test_interrupt_message_reports_restored_hashes(self) -> None:
        before = {"slides/deck.pptx": "old"}
        with (
            mock.patch(
                "scripts.publish_slides.public_release_hashes",
                return_value=before,
            ),
            mock.patch("scripts.publish_slides.run_with_receipt") as validator,
        ):
            message = describe_interrupted_release(before, None, False)
        self.assertEqual(message, "the public release is unchanged or restored")
        validator.assert_not_called()

    def test_interrupt_message_reports_validated_commit(self) -> None:
        with (
            mock.patch(
                "scripts.publish_slides.public_release_hashes",
                return_value={"slides/deck.pptx": "new"},
            ),
            mock.patch(
                "scripts.publish_slides.run_with_receipt",
                return_value="VALIDATION PASSED",
            ),
        ):
            message = describe_interrupted_release(
                {"slides/deck.pptx": "old"}, None, True
            )
        self.assertEqual(
            message,
            "the public release was published and validated before interruption",
        )

    def test_interrupt_message_does_not_claim_unverified_state(self) -> None:
        with (
            mock.patch(
                "scripts.publish_slides.public_release_hashes",
                return_value={"slides/deck.pptx": "new"},
            ),
            mock.patch(
                "scripts.publish_slides.run_with_receipt",
                side_effect=ReleaseError("forced validation failure"),
            ),
        ):
            message = describe_interrupted_release(
                {"slides/deck.pptx": "old"}, None, False
            )
        self.assertIn("changed but could not be validated", message)


if __name__ == "__main__":
    unittest.main()
