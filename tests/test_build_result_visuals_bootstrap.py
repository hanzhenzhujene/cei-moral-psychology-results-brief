from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_result_visuals.py"


class ResultVisualBootstrapTests(unittest.TestCase):
    def test_source_replacement_during_startup_cannot_rebind_old_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            test_builder = Path(temporary) / "build_result_visuals.py"
            test_builder.write_bytes(BUILDER.read_bytes())
            environment = os.environ.copy()
            environment["CEI_RESULT_VISUAL_BOOTSTRAP_DELAY"] = "1"
            process = subprocess.Popen(
                [sys.executable, str(test_builder)],
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(0.2)
            test_builder.write_text("raise SystemExit(77)\n", encoding="utf-8")
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 77, stdout + stderr)
            self.assertNotIn("Built 10 result figures", stdout)


if __name__ == "__main__":
    unittest.main()
