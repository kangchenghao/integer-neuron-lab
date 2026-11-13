"""Small end-to-end checks of the offline launcher and saved evidence files."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class OfflineCLITests(unittest.TestCase):
    def invoke(self, directory, *arguments):
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(PROJECT / "run.py"), *arguments],
            cwd=directory, env=environment, capture_output=True, text=True,
            encoding="utf-8", timeout=60, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

    def test_verify_one_case_saves_reproducible_numerical_record(self):
        # A different working directory and no PYTHONPATH confirm that run.py
        # supplies its own src location; an installed parent package is unused.
        with tempfile.TemporaryDirectory() as directory:
            first = self.invoke(directory, "verify", "--cases", "1", "--output", "nested/first.json")
            self.assertEqual(first.returncode, 0, first.stderr)
            summary = json.loads(first.stdout)
            record = json.loads((Path(directory) / "nested/first.json").read_text(encoding="utf-8"))
            self.assertTrue(summary["passed"])
            self.assertEqual(record["cases"], 1)
            self.assertEqual(len(record["records"]), 1)
            self.assertRegex(record["records"][0]["output_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(set(record["environment"]), {"python", "implementation", "system", "machine"})
            for relative, digest in record["source_sha256"].items():
                self.assertFalse(Path(relative).is_absolute())
                self.assertNotIn("..", Path(relative).parts)
                self.assertEqual(hashlib.sha256((PROJECT / relative).read_bytes()).hexdigest(), digest)
            second = self.invoke(directory, "verify", "--cases", "1", "--output", "nested/second.json")
            self.assertEqual(second.returncode, 0, second.stderr)
            repeated = json.loads((Path(directory) / "nested/second.json").read_text(encoding="utf-8"))
            self.assertEqual(record["records"], repeated["records"])

    def test_small_experiment_writes_json_and_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = self.invoke(directory, "experiment", "--neurons", "2", "--horizon", "8",
                                    "--repeats", "1", "--output", "evidence/small.json")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            report = json.loads((Path(directory) / "evidence/small.json").read_text(encoding="utf-8"))
            self.assertTrue(summary["passed"])
            self.assertEqual(summary["configurations"], 36)
            self.assertEqual(summary["model_invocations"], 72)
            self.assertEqual(report["parameters"], {"neurons": 2, "horizon": 8, "repeats": 1})
            self.assertTrue(report["all_outputs_exact"])
            self.assertEqual(len(report["rows"]), 36)
            for row in report["rows"]:
                self.assertTrue(row["all_outputs_exact"])
                self.assertEqual(len(row["dense_ns"]), 1)
                self.assertEqual(len(row["event_ns"]), 1)
                self.assertGreater(row["dense_ns"][0], 0)
                self.assertGreater(row["event_ns"][0], 0)
                self.assertEqual(row["dense_median_ns"], row["dense_ns"][0])
                self.assertEqual(row["event_median_ns"], row["event_ns"][0])
                self.assertRegex(row["fixture_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(row["output_sha256"], r"^[0-9a-f]{64}$")
            with (Path(directory) / "evidence/small.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 36)
            self.assertEqual(rows[0]["fixture_sha256"], report["rows"][0]["fixture_sha256"])

    def test_invalid_counts_and_experiment_sizes_are_rejected(self):
        invalid = (
            ("verify", "--cases", "0"),
            ("experiment", "--repeats", "0"),
            ("experiment", "--repeats", "-1"),
            ("experiment", "--neurons", "0"),
            ("experiment", "--horizon", "0"),
            ("experiment", "--neurons", "1024", "--horizon", "1025"),
        )
        with tempfile.TemporaryDirectory() as directory:
            for arguments in invalid:
                with self.subTest(arguments=arguments):
                    completed = self.invoke(directory, *arguments)
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn("error:", completed.stderr)
                    self.assertFalse((Path(directory) / "results").exists())

    def test_csv_destination_is_rejected_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "keep.csv"
            for command in ("verify", "experiment"):
                destination.write_text("existing evidence must survive\n", encoding="utf-8")
                arguments = (["--cases", "1"] if command == "verify" else
                             ["--neurons", "2", "--horizon", "8", "--repeats", "1"])
                completed = self.invoke(directory, command, *arguments, "--output", "keep.csv")
                self.assertEqual(completed.returncode, 2, completed.stdout)
                self.assertEqual(destination.read_text(encoding="utf-8"), "existing evidence must survive\n")
                self.assertEqual(list(Path(directory).iterdir()), [destination])


if __name__ == "__main__":
    unittest.main()
