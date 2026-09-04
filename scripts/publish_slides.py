#!/usr/bin/env python3
"""Build, render, validate, and publish the complete slide release."""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path
from types import FrameType
from typing import TextIO

import img2pdf
from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "slides"
DECK_NAME = "cei-moral-psychology-results-deck.pptx"
PDF_NAME = "cei-moral-psychology-results-deck.pdf"
PUBLIC_DECK = SLIDES / DECK_NAME
PUBLIC_PDF = SLIDES / PDF_NAME
PUBLIC_RENDER_DIR = SLIDES / "rendered"
PUBLIC_MANIFEST = SLIDES / "RENDER_MANIFEST.csv"
VALIDATOR = ROOT / "scripts" / "validate_site.py"
BUILDER = ROOT / "scripts" / "build_slides.mjs"
RELEASE_LOCK = ROOT / ".codex-slides-build" / "release.lock"
EXPECTED_SIZE = (2560, 1440)
PAGE_SIZE = (960, 540)
MANIFEST_COLUMNS = [
    "path",
    "kind",
    "bytes",
    "sha256",
    "width_px",
    "height_px",
    "pages",
    "source_pptx_sha256",
]
ROLLBACK_GUARD_SIGNALS = {signal.SIGINT, signal.SIGTERM}


class ReleaseError(RuntimeError):
    """Raised when a slide release cannot be completed safely."""


class TerminationRequested(BaseException):
    """Raised when SIGTERM arrives during the protected release transaction."""

    def __init__(self, signum: int) -> None:
        self.signum = signum
        super().__init__(f"received signal {signum}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def public_release_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): sha256(path)
        for path in [
            PUBLIC_DECK,
            PUBLIC_PDF,
            *sorted(PUBLIC_RENDER_DIR.glob("slide-*.png")),
            PUBLIC_MANIFEST,
        ]
        if path.is_file()
    }


def required_path(name: str, *, directory: bool) -> Path:
    raw = os.environ.get(name, "")
    path = Path(raw).expanduser() if raw else Path()
    if not raw or not path.is_absolute() or not path.exists():
        kind = "directory" if directory else "file"
        raise ReleaseError(f"{name} must name an existing absolute {kind} path")
    if directory != path.is_dir():
        kind = "directory" if directory else "file"
        raise ReleaseError(f"{name} must name an existing absolute {kind} path")
    return path.resolve()


def acquire_release_lock(lock_path: Path = RELEASE_LOCK) -> TextIO:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        handle.close()
        raise ReleaseError("another slide publisher is already running") from error
    return handle


def release_release_lock(handle: TextIO) -> None:
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    handle.close()


def block_rollback_signals() -> set[int | signal.Signals] | None:
    if not hasattr(signal, "pthread_sigmask"):
        return None
    return signal.pthread_sigmask(signal.SIG_BLOCK, ROLLBACK_GUARD_SIGNALS)


def restore_termination_signals(previous: set[int | signal.Signals] | None) -> None:
    if previous is not None:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def raise_on_sigterm(signum: int, _frame: FrameType | None) -> None:
    raise TerminationRequested(signum)


def run_checked(command: list[str], *, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout).strip()
        raise ReleaseError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n{details}"
        )
    return completed.stdout


def run_with_receipt(command: list[str], phrase: str) -> str:
    receipt = run_checked(command)
    if phrase not in receipt:
        raise ReleaseError(f"command exited without the expected receipt: {phrase}")
    return receipt


def render_deck(
    deck: Path,
    raw_render_dir: Path,
    workspace_python: Path,
    presentations_skill_dir: Path,
    env: dict[str, str],
) -> list[Path]:
    render_script = presentations_skill_dir / "container_tools" / "render_slides.py"
    if not render_script.is_file():
        raise ReleaseError(f"presentation renderer is missing: {render_script}")
    run_checked(
        [
            str(workspace_python),
            str(render_script),
            str(deck),
            "--output_dir",
            str(raw_render_dir),
            "--width",
            str(EXPECTED_SIZE[0]),
            "--height",
            str(EXPECTED_SIZE[1]),
        ],
        env=env,
    )
    rendered = sorted(
        raw_render_dir.glob("slide-*.png"),
        key=lambda path: int(path.stem.split("-")[-1]),
    )
    if len(rendered) != 8:
        raise ReleaseError(f"renderer produced {len(rendered)} slide PNGs; expected 8")
    for index, path in enumerate(rendered, start=1):
        if path.name != f"slide-{index}.png":
            raise ReleaseError(f"unexpected renderer output order: {path.name}")
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.size != EXPECTED_SIZE:
                raise ReleaseError(
                    f"{path.name} is {image.size}; expected {EXPECTED_SIZE}"
                )
    return rendered


def make_pdf(pngs: list[Path], output: Path) -> None:
    if getattr(img2pdf, "__version__", "") != "0.6.1":
        raise ReleaseError("img2pdf 0.6.1 is required for a reproducible share PDF")
    run_checked(
        [
            str(Path(sys.executable).resolve()),
            "-m",
            "img2pdf",
            "-D",
            "-S",
            f"{PAGE_SIZE[0]}x{PAGE_SIZE[1]}",
            *[str(path) for path in pngs],
            "-o",
            str(output),
        ]
    )
    reader = PdfReader(output)
    if len(reader.pages) != 8:
        raise ReleaseError(f"slide PDF has {len(reader.pages)} pages; expected 8")
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if (width, height) != PAGE_SIZE:
            raise ReleaseError(
                f"PDF page {index} is {width} × {height}; expected 960 × 540 points"
            )


def write_manifest(deck: Path, pdf: Path, pngs: list[Path], output: Path) -> None:
    deck_hash = sha256(deck)
    rows: list[list[str | int]] = [
        [
            f"slides/{PDF_NAME}",
            "pdf",
            pdf.stat().st_size,
            sha256(pdf),
            "",
            "",
            8,
            deck_hash,
        ]
    ]
    for index, path in enumerate(pngs, start=1):
        rows.append(
            [
                f"slides/rendered/slide-{index:02d}.png",
                "png",
                path.stat().st_size,
                sha256(path),
                EXPECTED_SIZE[0],
                EXPECTED_SIZE[1],
                1,
                deck_hash,
            ]
        )
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(MANIFEST_COLUMNS)
        writer.writerows(rows)


def validator_command(
    deck: Path,
    pdf: Path,
    render_dir: Path,
    manifest: Path,
    source_repo: Path | None,
) -> list[str]:
    command = [
        str(Path(sys.executable).resolve()),
        str(VALIDATOR),
        "--slide-deck",
        str(deck),
        "--slide-pdf",
        str(pdf),
        "--slide-render-dir",
        str(render_dir),
        "--slide-export-manifest",
        str(manifest),
    ]
    if source_repo is not None:
        command.extend(["--source-repo", str(source_repo)])
    return command


def public_validator_command(source_repo: Path | None) -> list[str]:
    command = [str(Path(sys.executable).resolve()), str(VALIDATOR)]
    if source_repo is not None:
        command.extend(["--source-repo", str(source_repo)])
    return command


def public_integrity_command() -> list[str]:
    return [
        str(Path(sys.executable).resolve()),
        str(VALIDATOR),
        "--slide-export-integrity-only",
    ]


def describe_interrupted_release(
    before: dict[str, str],
    source_repo: Path | None,
    publication_committed: bool,
) -> str:
    try:
        current = public_release_hashes()
    except OSError as error:
        return f"the public release state could not be read: {error}"
    if before and current == before:
        return "the public release is unchanged or restored"
    try:
        run_with_receipt(
            public_validator_command(source_repo),
            "VALIDATION PASSED",
        )
    except (OSError, ReleaseError, subprocess.SubprocessError, ValueError) as error:
        return f"the public release changed but could not be validated: {error}"
    if publication_committed:
        return "the public release was published and validated before interruption"
    if before:
        return (
            "the public release changed and passes validation; publication may have "
            "completed before interruption"
        )
    return "the public release passes validation, but the interruption timing is unknown"


def publish_with_rollback(
    plan: list[tuple[Path, Path]],
    backup_dir: Path,
    validate_public: Callable[[], str],
    fail_after: int | None = None,
    validate_rollback: Callable[[], str] | None = None,
) -> str:
    backups: dict[Path, Path | None] = {}
    incoming: dict[Path, Path] = {}
    token = uuid.uuid4().hex
    published: list[Path] = []
    previous_signal_mask: set[int | signal.Signals] | None = None
    mask_needs_restore = False
    previous_sigterm_handler = signal.getsignal(signal.SIGTERM)
    sigterm_handler_needs_restore = False
    try:
        signal.signal(signal.SIGTERM, raise_on_sigterm)
        sigterm_handler_needs_restore = True
        for index, (source, target) in enumerate(plan):
            target.parent.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / f"{index:02d}-{target.name}"
            if target.exists():
                shutil.copy2(target, backup)
                backups[target] = backup
            else:
                backups[target] = None
            candidate = target.parent / f".{target.name}.{token}.new"
            shutil.copyfile(source, candidate)
            if sha256(candidate) != sha256(source):
                raise ReleaseError(f"incoming copy hash drift: {target.name}")
            incoming[target] = candidate

        for _, target in plan:
            os.replace(incoming[target], target)
            published.append(target)
            if fail_after == len(published):
                raise ReleaseError(
                    f"test failpoint: after {len(published)} published file(s)"
                )
        receipt = validate_public()
        for candidate in incoming.values():
            candidate.unlink(missing_ok=True)
        incoming.clear()
        signal.signal(signal.SIGTERM, previous_sigterm_handler)
        sigterm_handler_needs_restore = False
        return receipt
    except BaseException as error:
        # Signal handlers stay active during the public transaction. Once an
        # interrupt enters this path, block both signals so rollback and its
        # validation cannot be interrupted halfway through.
        previous_signal_mask = block_rollback_signals()
        mask_needs_restore = previous_signal_mask is not None
        rollback_errors: list[str] = []
        for target in reversed(published):
            try:
                saved_backup = backups[target]
                if saved_backup is None:
                    target.unlink(missing_ok=True)
                else:
                    restore = target.parent / f".{target.name}.{token}.restore"
                    shutil.copyfile(saved_backup, restore)
                    os.replace(restore, target)
            except (
                Exception
            ) as rollback_error:  # pragma: no cover - catastrophic filesystem failure
                rollback_errors.append(f"{target}: {rollback_error}")
        for target, saved_backup in backups.items():
            if saved_backup is None:
                if target.exists():
                    rollback_errors.append(
                        f"new target remains after rollback: {target}"
                    )
            elif not target.is_file() or sha256(target) != sha256(saved_backup):
                rollback_errors.append(f"restored hash mismatch: {target}")
        try:
            (validate_rollback or validate_public)()
        except Exception as rollback_validation_error:
            rollback_errors.append(
                f"restored public validation failed: {rollback_validation_error}"
            )
        if rollback_errors:
            raise ReleaseError(
                f"{error}\nrollback also failed:\n" + "\n".join(rollback_errors)
            ) from error
        if not isinstance(error, Exception):
            raise
        raise ReleaseError(
            f"{error}\npublic slide files were restored from backup"
        ) from error
    finally:
        try:
            for candidate in incoming.values():
                candidate.unlink(missing_ok=True)
        finally:
            try:
                if mask_needs_restore:
                    restore_termination_signals(previous_signal_mask)
            finally:
                if sigterm_handler_needs_restore:
                    signal.signal(signal.SIGTERM, previous_sigterm_handler)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-repo",
        type=Path,
        help="Optional pinned moral-psychology-benchmark checkout for the source-level validation gate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lock_handle: TextIO | None = None
    before: dict[str, str] = {}
    source_repo: Path | None = None
    publication_committed = False
    try:
        presentations_skill_dir = required_path(
            "PRESENTATIONS_SKILL_DIR", directory=True
        )
        workspace_python = required_path("WORKSPACE_PYTHON", directory=False)
        artifact_tool_dir = required_path("ARTIFACT_TOOL_DIR", directory=True)
        runtime_node_modules = required_path("RUNTIME_NODE_MODULES", directory=True)
        runtime_node = required_path("RUNTIME_NODE", directory=False)
        lock_handle = acquire_release_lock()
        source_repo = (
            args.source_repo.resolve() if args.source_repo is not None else None
        )
        if source_repo is not None and not source_repo.is_dir():
            raise ReleaseError(f"source repo does not exist: {source_repo}")

        failpoint = os.environ.get("SLIDE_RELEASE_TEST_FAILPOINT", "")
        if failpoint not in {
            "",
            "before-publish",
            "after-first-publish",
            "after-publish",
        }:
            raise ReleaseError(f"unsupported SLIDE_RELEASE_TEST_FAILPOINT: {failpoint}")

        run_with_receipt(
            public_integrity_command(),
            "SLIDE EXPORT INTEGRITY PASSED",
        )
        before = public_release_hashes()
        with tempfile.TemporaryDirectory(
            prefix=".codex-slide-release-", dir=ROOT
        ) as temporary:
            staging = Path(temporary)
            staged_slides = staging / "slides"
            staged_render_dir = staged_slides / "rendered"
            raw_render_dir = staging / "raw-render"
            backup_dir = staging / "backup"
            staged_render_dir.mkdir(parents=True)
            raw_render_dir.mkdir()
            backup_dir.mkdir()

            staged_deck = staged_slides / DECK_NAME
            staged_pdf = staged_slides / PDF_NAME
            staged_manifest = staged_slides / "RENDER_MANIFEST.csv"
            build_env = dict(os.environ)
            build_env.update(
                {
                    "PRESENTATIONS_SKILL_DIR": str(presentations_skill_dir),
                    "WORKSPACE_PYTHON": str(workspace_python),
                    "VALIDATION_PYTHON": str(Path(sys.executable).resolve()),
                    "ARTIFACT_TOOL_DIR": str(artifact_tool_dir),
                    "RUNTIME_NODE_MODULES": str(runtime_node_modules),
                    "RUNTIME_NODE": str(runtime_node),
                    "SLIDE_DECK_OUTPUT": str(staged_deck),
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
            )
            builder_receipt = run_checked(
                [str(runtime_node), str(BUILDER)], env=build_env
            )
            if '"semanticValidation": "passed"' not in builder_receipt:
                raise ReleaseError(
                    "deck builder exited without a semantic-validation receipt"
                )

            raw_pngs = render_deck(
                staged_deck,
                raw_render_dir,
                workspace_python,
                presentations_skill_dir,
                build_env,
            )
            staged_pngs: list[Path] = []
            for index, source in enumerate(raw_pngs, start=1):
                target = staged_render_dir / f"slide-{index:02d}.png"
                shutil.copyfile(source, target)
                staged_pngs.append(target)
            make_pdf(staged_pngs, staged_pdf)
            write_manifest(staged_deck, staged_pdf, staged_pngs, staged_manifest)

            staged_receipt = run_checked(
                validator_command(
                    staged_deck,
                    staged_pdf,
                    staged_render_dir,
                    staged_manifest,
                    source_repo,
                )
            )
            if "VALIDATION PASSED" not in staged_receipt:
                raise ReleaseError(
                    "staged release validator exited without a VALIDATION PASSED receipt"
                )
            if failpoint == "before-publish":
                raise ReleaseError("test failpoint: before-publish")

            plan = [
                (staged_deck, PUBLIC_DECK),
                (staged_pdf, PUBLIC_PDF),
                *[(path, PUBLIC_RENDER_DIR / path.name) for path in staged_pngs],
                (staged_manifest, PUBLIC_MANIFEST),
            ]
            fail_after = (
                1
                if failpoint == "after-first-publish"
                else len(plan)
                if failpoint == "after-publish"
                else None
            )
            public_receipt = publish_with_rollback(
                plan,
                backup_dir,
                lambda: run_with_receipt(
                    public_validator_command(source_repo), "VALIDATION PASSED"
                ),
                fail_after=fail_after,
                validate_rollback=lambda: run_with_receipt(
                    public_integrity_command(), "SLIDE EXPORT INTEGRITY PASSED"
                ),
            )
            publication_committed = True

        after = public_release_hashes()
        changed = sorted(
            path for path, digest in after.items() if before.get(path) != digest
        )
        unchanged = sorted(
            path for path, digest in after.items() if before.get(path) == digest
        )
        print(
            json.dumps(
                {
                    "status": "published",
                    "pptx_sha256": after[str(PUBLIC_DECK.relative_to(ROOT))],
                    "changed": changed,
                    "unchanged": unchanged,
                    "staged_validation": "passed",
                    "public_validation": "passed"
                    if "VALIDATION PASSED" in public_receipt
                    else "missing receipt",
                },
                indent=2,
            )
        )
        return 0
    except KeyboardInterrupt:
        print(
            "SLIDE RELEASE INTERRUPTED: "
            + describe_interrupted_release(
                before, source_repo, publication_committed
            ),
            file=sys.stderr,
        )
        return 130
    except TerminationRequested as error:
        print(
            "SLIDE RELEASE TERMINATED: "
            + describe_interrupted_release(
                before, source_repo, publication_committed
            ),
            file=sys.stderr,
        )
        return 128 + error.signum
    except (OSError, ReleaseError, subprocess.SubprocessError, ValueError) as error:
        print(f"SLIDE RELEASE FAILED: {error}", file=sys.stderr)
        return 1
    finally:
        if lock_handle is not None:
            release_release_lock(lock_handle)


if __name__ == "__main__":
    raise SystemExit(main())
