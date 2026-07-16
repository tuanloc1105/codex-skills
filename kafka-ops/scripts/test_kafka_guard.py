#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import kafka_guard


LOCAL_PWSH = Path(r"D:\dev-kit\PS7\pwsh.exe")
PWSH_EXECUTABLE = str(LOCAL_PWSH) if LOCAL_PWSH.is_file() else shutil.which("pwsh.exe")
POWERSHELL_HOSTS = (("Windows PowerShell 5.1", "powershell.exe"),)
if PWSH_EXECUTABLE:
    POWERSHELL_HOSTS += (("PowerShell 7", PWSH_EXECUTABLE),)


def kafka_tool(name: str) -> str:
    if os.name == "nt":
        return str(Path("C:/Apache Kafka/bin/windows") / f"{name}.bat")
    return f"/opt/kafka/bin/{name}.sh"


def absolute_fixture(name: str) -> str:
    return str(Path(tempfile.gettempdir()).resolve() / name)


class ClassifyTests(unittest.TestCase):
    def assert_class(
        self,
        expected: str,
        command: list[str],
        platform: str | None = None,
    ) -> dict[str, object]:
        result = kafka_guard.classify(command, platform)
        self.assertEqual(expected, result["classification"], result)
        return result

    def test_topic_reads_and_mutations(self) -> None:
        self.assert_class("READ", [kafka_tool("kafka-topics"), "--list", "--bootstrap-server", "broker:9092"])
        created = self.assert_class("MUTATION", [kafka_tool("kafka-topics"), "--create", "--topic", "orders"])
        self.assertEqual("standard", created["risk"])
        deleted = self.assert_class("MUTATION", [kafka_tool("kafka-topics"), "--delete", "--topic", "orders"])
        self.assertEqual("high", deleted["risk"])

    def test_config_and_acl_rules(self) -> None:
        self.assert_class("READ", [kafka_tool("kafka-configs"), "--describe", "--entity-type", "topics"])
        self.assert_class("MUTATION", [kafka_tool("kafka-configs"), "--alter", "--entity-type", "topics"])
        self.assert_class("SENSITIVE_READ", [kafka_tool("kafka-acls"), "--list", "--topic", "orders"])
        self.assert_class("MUTATION", [kafka_tool("kafka-acls"), "--add", "--topic", "orders"])

    def test_offset_reset_preview_and_execute(self) -> None:
        base = [kafka_tool("kafka-consumer-groups"), "--reset-offsets", "--group", "billing", "--topic", "orders"]
        self.assert_class("PREVIEW", base)
        result = self.assert_class("MUTATION", [*base, "--execute"])
        self.assertEqual("high", result["risk"])

    def test_bounded_console_consumer(self) -> None:
        safe = [
            kafka_tool("kafka-console-consumer"),
            "--bootstrap-server",
            "broker:9092",
            "--topic",
            "orders",
            "--partition",
            "0",
            "--offset",
            "42",
            "--max-messages",
            "10",
            "--timeout-ms",
            "5000",
            "--consumer-property",
            "enable.auto.commit=false",
            "--consumer-property",
            "allow.auto.create.topics=false",
        ]
        self.assert_class("SENSITIVE_READ", safe)
        self.assert_class("UNKNOWN", [arg for arg in safe if arg != "--partition" and arg != "0"])
        self.assert_class("MUTATION", [kafka_tool("kafka-console-consumer"), "--group", "billing", "--topic", "orders"])

    def test_high_risk_tools_and_unknowns(self) -> None:
        self.assert_class("MUTATION", [kafka_tool("kafka-console-producer"), "--topic", "orders"])
        self.assert_class(
            "MUTATION",
            [
                kafka_tool("kafka-reassign-partitions"),
                "--verify",
                "--reassignment-json-file",
                absolute_fixture("plan.json"),
            ],
        )
        self.assert_class("UNKNOWN", [kafka_tool("kafka-topics"), "--list", "|", "head"])
        self.assert_class("UNKNOWN", ["vendor-kafka-tool", "--list"])
        self.assert_class("UNKNOWN", ["/opt/kafka/bin/kafka-future-tool", "--help"])
        self.assert_class("UNKNOWN", [kafka_tool("kafka-broker-api-versions"), "--delete"])
        self.assert_class("UNKNOWN", [kafka_tool("kafka-topics"), "--list", "--command-config", "relative.properties"])
        self.assert_class("UNKNOWN", [kafka_tool("kafka-topics"), "--list", "--command-config", "~/client.properties"])
        self.assert_class("UNKNOWN", [kafka_tool("kafka-configs"), "--alter", "--add-config", "password=secret"])
        self.assert_class("MUTATION", [kafka_tool("kafka-server-stop"), "--version"])
        self.assert_class("UNKNOWN", [kafka_tool("kafka-server-start"), "relative-server.properties"])

    def test_windows_batch_argv_hardening(self) -> None:
        binary = r"C:\Kafka Home ü\bin\windows\kafka-topics.bat"
        for safe in ("orders.eu", "orders'west", "orders$(west)", "orders`west", "orders\\"):
            with self.subTest(safe=safe):
                self.assert_class("READ", [binary, "--describe", "--topic", safe], "nt")
        for unsafe in ("orders&whoami", "%TEMP%", "orders!x", 'orders"x'):
            with self.subTest(unsafe=unsafe):
                result = self.assert_class("UNKNOWN", [binary, "--describe", "--topic", unsafe], "nt")
                if '"' in unsafe:
                    self.assertIn("embedded quotes", str(result["reason"]))
                else:
                    self.assertIn("cmd.exe metacharacter", str(result["reason"]))
        for control in ("orders\twest", "orders\x1fwest", "orders\x7fwest"):
            with self.subTest(control=repr(control)):
                self.assert_class("UNKNOWN", [binary, "--describe", "--topic", control], "nt")
        empty = self.assert_class("UNKNOWN", [binary, "--describe", "--topic", ""], "nt")
        self.assertIn("empty token", str(empty["reason"]))

    def test_help_and_version_policy_is_explicit_for_every_known_tool(self) -> None:
        local_read = {
            "kafka-acls",
            "kafka-broker-api-versions",
            "kafka-client-metrics",
            "kafka-cluster",
            "kafka-configs",
            "kafka-consumer-groups",
            "kafka-features",
            "kafka-get-offsets",
            "kafka-groups",
            "kafka-log-dirs",
            "kafka-metadata-quorum",
            "kafka-reassign-partitions",
            "kafka-share-groups",
            "kafka-storage",
            "kafka-topics",
            "kafka-transactions",
        }
        always_mutation = {
            "kafka-console-producer",
            "kafka-delete-records",
            "kafka-leader-election",
            "kafka-producer-perf-test",
            "kafka-server-start",
            "kafka-server-stop",
            "kafka-verifiable-producer",
        }
        unknown_or_unbounded = kafka_guard.KNOWN_KAFKA_TOOLS - local_read - always_mutation
        self.assertEqual(kafka_guard.KNOWN_KAFKA_TOOLS, local_read | always_mutation | unknown_or_unbounded)

        for flag in ("--help", "--version"):
            for tool in sorted(local_read):
                with self.subTest(tool=tool, flag=flag):
                    self.assert_class("LOCAL_READ", [kafka_tool(tool), flag])
            for tool in sorted(always_mutation):
                with self.subTest(tool=tool, flag=flag):
                    result = self.assert_class("MUTATION", [kafka_tool(tool), flag])
                    self.assertEqual("high", result["risk"])
            for tool in sorted(unknown_or_unbounded):
                with self.subTest(tool=tool, flag=flag):
                    self.assert_class("UNKNOWN", [kafka_tool(tool), flag])

    def test_client_metrics_mutations_are_high_risk(self) -> None:
        for flag in ("--alter", "--delete"):
            with self.subTest(flag=flag):
                result = self.assert_class("MUTATION", [kafka_tool("kafka-client-metrics"), flag, "--name", "clients"])
                self.assertEqual("high", result["risk"])

    def test_console_producer_custom_reader_and_reader_config_fail_closed(self) -> None:
        custom_reader = [
            kafka_tool("kafka-console-producer"),
            "--topic",
            "orders",
            "--line-reader",
            "com.example.CustomReader",
        ]
        self.assert_class("UNKNOWN", custom_reader)
        self.assert_class(
            "UNKNOWN",
            [kafka_tool("kafka-console-producer"), "--topic", "orders", "--reader-config", "relative.properties"],
        )


class PortabilityTests(unittest.TestCase):
    def test_canonical_tool_handles_both_path_styles(self) -> None:
        self.assertEqual("kafka-topics", kafka_guard.canonical_tool("/opt/kafka/bin/kafka-topics.sh"))
        self.assertEqual(
            "kafka-topics",
            kafka_guard.canonical_tool(r"C:\Program Files\Kafka\bin\windows\kafka-topics.bat"),
        )
        self.assertEqual("kafka-topics", kafka_guard.canonical_tool(r"C:\Kafka\kafka-topics.exe"))

    def test_absolute_path_recognizes_posix_drive_and_unc(self) -> None:
        self.assertTrue(kafka_guard._is_absolute_path("/opt/kafka/bin/kafka-topics.sh", "posix"))
        self.assertFalse(kafka_guard._is_absolute_path("/opt/kafka/bin/kafka-topics.sh", "nt"))
        self.assertTrue(kafka_guard._is_absolute_path(r"C:\Kafka\bin\windows\kafka-topics.bat", "nt"))
        self.assertTrue(kafka_guard._is_absolute_path(r"\\server\share\Kafka\kafka-topics.bat", "nt"))
        self.assertFalse(kafka_guard._is_absolute_path(r"\rooted\kafka-topics.bat", "nt"))
        self.assertFalse(kafka_guard._is_absolute_path(r"C:Kafka\kafka-topics.bat", "nt"))
        self.assertFalse(kafka_guard._is_absolute_path("kafka-topics.bat", "nt"))

    def test_windows_suffixes_and_batch_version_command(self) -> None:
        self.assertEqual((".bat", ".cmd", ".exe", ""), kafka_guard._tool_suffixes("nt"))
        binary = Path(r"C:\Program Files\Kafka\bin\windows\kafka-topics.bat")
        command = kafka_guard._version_command(binary, "nt", r"C:\Windows\System32\cmd.exe")
        self.assertEqual(r"C:\Windows\System32\cmd.exe", command[0])
        self.assertEqual(["/d", "/s", "/c"], command[1:4])
        self.assertEqual(
            r'""C:\Program Files\Kafka\bin\windows\kafka-topics.bat" "--version""',
            command[4],
        )

    def test_batch_command_line_preserves_trailing_backslashes(self) -> None:
        raw = kafka_guard._cmd_batch_line(
            Path(r"C:\Kafka (local)\bin\windows\kafka-topics.cmd"),
            ["plain", "with space", "trailing\\", "Unicode-ü"],
        )
        self.assertEqual(
            '""C:\\Kafka (local)\\bin\\windows\\kafka-topics.cmd" "plain" "with space" "trailing\\\\" "Unicode-ü""',
            raw,
        )

    def test_windows_native_transport_rejects_embedded_quotes(self) -> None:
        binary = r"C:\Kafka\bin\windows\kafka-topics.exe"
        safe = kafka_guard.classify([binary, "--describe", "--topic", "orders"], "nt")
        self.assertEqual("READ", safe["classification"], safe)
        unsafe = kafka_guard.classify([binary, "--describe", "--topic", 'User:CN="Ops Team"'], "nt")
        self.assertEqual("UNKNOWN", unsafe["classification"], unsafe)
        self.assertIn("cannot be transported losslessly", unsafe["reason"])

    def test_windows_version_command_ignores_comspec(self) -> None:
        binary = Path(r"C:\Kafka\bin\windows\kafka-topics.bat")
        with patch.dict(os.environ, {"COMSPEC": r"C:\poison\cmd.exe"}, clear=False):
            with patch.object(kafka_guard, "_windows_system_cmd", return_value=r"C:\Windows\System32\cmd.exe"):
                command = kafka_guard._version_command(binary, "nt")
                raw, executable, environment = kafka_guard._windows_batch_version_invocation(binary)
        self.assertEqual(r"C:\Windows\System32\cmd.exe", command[0])
        self.assertEqual(
            'cmd.exe /d /s /c ""C:\\Kafka\\bin\\windows\\kafka-topics.bat" "--version""',
            raw,
        )
        self.assertEqual(r"C:\Windows\System32\cmd.exe", executable)
        self.assertEqual(executable, environment["COMSPEC"])

    def test_windows_candidate_dirs_include_bin_windows_first(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            kafka_home = Path(raw_dir) / "Kafka Home"
            with patch.dict(os.environ, {"KAFKA_HOME": str(kafka_home), "PATH": ""}, clear=False):
                candidates = kafka_guard._candidate_dirs(None, "nt")
            self.assertEqual((kafka_home / "bin" / "windows").resolve(), candidates[0])
            self.assertEqual((kafka_home / "bin").resolve(), candidates[1])


class PreflightTests(unittest.TestCase):
    def _fake_tool(
        self,
        directory: Path,
        name: str,
        exit_code: int = 0,
        suffix: str | None = None,
        version: str = "4.3.0",
    ) -> None:
        if os.name == "nt":
            path = directory / f"{name}{suffix or '.bat'}"
            path.write_bytes(
                f"@echo off\r\nchcp 65001 >nul\r\necho {version}\r\nexit /b {exit_code}\r\n".encode("utf-8")
            )
        else:
            path = directory / name
            path.write_text(f"#!/bin/sh\nprintf '{version}\\n'\nexit {exit_code}\n", encoding="utf-8")
            path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def test_explicit_installation_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir) / "Kafka Home ü"
            directory.mkdir()
            self._fake_tool(directory, "kafka-topics")
            self._fake_tool(directory, "kafka-configs")
            result = kafka_guard.preflight(["kafka-topics", "kafka-configs"], str(directory))
            self.assertEqual("ready", result["status"], result)
            self.assertEqual("4.3.0", result["version"])
            self.assertEqual("windows" if os.name == "nt" else "posix", result["platform"])

    def test_missing_required_tool_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            self._fake_tool(directory, "kafka-topics")
            result = kafka_guard.preflight(["kafka-consumer-groups"], str(directory))
            self.assertEqual("missing_required_tools", result["reason"])

    def test_failed_version_check_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            self._fake_tool(directory, "kafka-topics", exit_code=23)
            result = kafka_guard.preflight([], str(directory))
            self.assertEqual("unusable_cli", result["reason"])
            self.assertEqual(23, result["exit_code"])

    def test_multiple_tool_variants_in_one_bin_block(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            self._fake_tool(directory, "kafka-topics")
            if os.name == "nt":
                second = directory / "kafka-topics.cmd"
                second.write_bytes(b"@echo off\r\necho 4.3.0\r\nexit /b 0\r\n")
            else:
                second = directory / "kafka-topics.sh"
                second.write_text("#!/bin/sh\nprintf '4.3.0\\n'\n", encoding="utf-8")
                second.chmod(second.stat().st_mode | stat.S_IXUSR)
            result = kafka_guard.preflight([], str(directory))
            self.assertEqual("ambiguous_cli", result["reason"])
            self.assertEqual(2, len(result["candidates"]))

    def test_missing_installation_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            original_path = os.environ.get("PATH")
            original_home = os.environ.pop("KAFKA_HOME", None)
            os.environ["PATH"] = raw_dir
            try:
                result = kafka_guard.preflight([])
            finally:
                if original_path is None:
                    os.environ.pop("PATH", None)
                else:
                    os.environ["PATH"] = original_path
                if original_home is not None:
                    os.environ["KAFKA_HOME"] = original_home
            self.assertEqual("missing_cli", result["reason"])

    def test_relative_explicit_bin_blocks(self) -> None:
        result = kafka_guard.preflight([], "relative/kafka/bin")
        self.assertEqual("invalid_kafka_bin", result["reason"])

    @unittest.skipUnless(os.name == "nt", "native Windows discovery test")
    def test_kafka_home_discovers_bin_windows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            kafka_home = Path(raw_dir) / "Kafka Home"
            directory = kafka_home / "bin" / "windows"
            directory.mkdir(parents=True)
            self._fake_tool(directory, "kafka-topics")
            with patch.dict(os.environ, {"KAFKA_HOME": str(kafka_home), "PATH": ""}, clear=False):
                result = kafka_guard.preflight([])
            self.assertEqual("ready", result["status"], result)
            self.assertEqual(str(directory.resolve()), result["bin_dir"])

    @unittest.skipUnless(os.name == "nt", "native Windows batch transport test")
    def test_batch_preflight_handles_spaces_unicode_parentheses_and_cmd_suffix(self) -> None:
        for suffix in (".bat", ".cmd"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as raw_dir:
                directory = Path(raw_dir) / "Kafka Home (local) ü"
                directory.mkdir()
                self._fake_tool(directory, "kafka-topics", suffix=suffix, version="4.3.1-ü")
                with patch.dict(os.environ, {"COMSPEC": str(directory / "poisoned.cmd")}, clear=False):
                    result = kafka_guard.preflight([], str(directory))
                self.assertEqual("ready", result["status"], result)
                self.assertEqual("4.3.1-ü", result["version"])

    @unittest.skipUnless(os.name == "nt", "native Windows batch transport test")
    def test_batch_preflight_preserves_nonzero_exit_code_for_cmd(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir) / "Kafka Home (local)"
            directory.mkdir()
            self._fake_tool(directory, "kafka-topics", exit_code=41, suffix=".cmd")
            result = kafka_guard.preflight([], str(directory))
            self.assertEqual("unusable_cli", result["reason"])
            self.assertEqual(41, result["exit_code"])


class CliEncodingTests(unittest.TestCase):
    def test_plan_json_is_utf8_when_initial_stdout_encoding_is_legacy(self) -> None:
        guard = Path(__file__).with_name("kafka_guard.py").resolve()
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "cp1252"
        completed = subprocess.run(
            [
                sys.executable,
                str(guard),
                "plan",
                "--cluster-id",
                "cluster-a",
                "--environment",
                "prod",
                "--kafka-version",
                "4.3.0",
                "--",
                kafka_tool("kafka-topics"),
                "--delete",
                "--topic",
                "orders",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            timeout=15,
        )
        self.assertEqual(0, completed.returncode, completed.stderr.decode(errors="replace"))
        payload = json.loads(completed.stdout.decode("utf-8"))
        self.assertIn("XÁC NHẬN", payload["confirmation_phrase"])

    def test_invalid_minimum_risk_is_rejected_by_argparse(self) -> None:
        guard = Path(__file__).with_name("kafka_guard.py").resolve()
        completed = subprocess.run(
            [
                sys.executable,
                str(guard),
                "plan",
                "--cluster-id",
                "cluster-a",
                "--environment",
                "prod",
                "--kafka-version",
                "4.3.0",
                "--minimum-risk",
                "critical",
                "--",
                kafka_tool("kafka-topics"),
                "--create",
                "--topic",
                "orders",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("invalid choice", completed.stderr)


@unittest.skipUnless(os.name == "nt", "native Windows PowerShell runner tests")
class WindowsPowerShellRunnerTests(unittest.TestCase):
    def test_guard_plan_redirected_stdout_is_utf8(self) -> None:
        guard = Path(__file__).with_name("kafka_guard.ps1").resolve()
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(guard),
                "plan",
                "--cluster-id",
                "cluster-a",
                "--environment",
                "prod",
                "--kafka-version",
                "4.3.0",
                "--",
                kafka_tool("kafka-topics"),
                "--delete",
                "--topic",
                "orders",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        self.assertEqual(0, completed.returncode, completed.stderr.decode(errors="replace"))
        payload = json.loads(completed.stdout.decode("utf-8-sig"))
        self.assertIn("XÁC NHẬN", payload["confirmation_phrase"])

    def test_runner_preserves_safe_argv_and_exit_code(self) -> None:
        runner = Path(__file__).with_name("invoke_kafka.ps1").resolve()
        safe_args = ["plain", "with space", "single'quote", "$(literal)", "`tick", "trailing\\", "Unicode-ü"]
        for suffix in (".bat", ".cmd"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as raw_dir:
                directory = Path(raw_dir) / "Kafka Probe (local) ü"
                directory.mkdir()
                probe = directory / "probe.py"
                output = directory / "argv.json"
                batch = directory / f"kafka-argv-probe{suffix}"
                poisoned_marker = directory / "poisoned-cmd.txt"
                poisoned_comspec = directory / "poisoned-cmd.cmd"
                probe.write_text(
                    "import json, pathlib, sys\n"
                    "pathlib.Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:], ensure_ascii=False), encoding='utf-8')\n",
                    encoding="utf-8",
                )
                batch.write_bytes(
                    b'@echo off\r\nchcp 65001 >nul\r\necho stdout-\xc3\xbc\r\n>&2 echo stderr-\xc3\xbc\r\n'
                    b'"%KAFKA_TEST_PYTHON%" "%~dp0probe.py" "%~dp0argv.json" %*\r\nexit /b 37\r\n'
                )
                poisoned_comspec.write_bytes(b'@echo poisoned>"%~dp0poisoned-cmd.txt"\r\nexit /b 99\r\n')
                environment = os.environ.copy()
                environment["KAFKA_TEST_PYTHON"] = sys.executable
                environment["COMSPEC"] = str(poisoned_comspec)
                for host_name, host in POWERSHELL_HOSTS:
                    with self.subTest(host=host_name):
                        output.unlink(missing_ok=True)
                        completed = subprocess.run(
                            [
                                host,
                                "-NoLogo",
                                "-NoProfile",
                                "-NonInteractive",
                                "-ExecutionPolicy",
                                "Bypass",
                                "-File",
                                str(runner),
                                str(batch),
                                *safe_args,
                            ],
                            check=False,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            env=environment,
                            timeout=15,
                        )
                        self.assertEqual(37, completed.returncode, completed.stderr)
                        self.assertIn("stdout-ü", completed.stdout)
                        self.assertIn("stderr-ü", completed.stderr)
                        self.assertEqual(safe_args, json.loads(output.read_text(encoding="utf-8")))
                        self.assertFalse(poisoned_marker.exists())

    def test_runner_blocks_batch_metacharacters_before_execution(self) -> None:
        runner = Path(__file__).with_name("invoke_kafka.ps1").resolve()
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            marker = directory / "executed.txt"
            batch = directory / "kafka-topics.cmd"
            batch.write_bytes(b'@echo executed>"%~dp0executed.txt"\r\nexit /b 0\r\n')
            for unsafe in (
                "x%TEMP%",
                "x!y",
                "x^y",
                "x&whoami",
                "x|whoami",
                "x>file",
                "x<file",
                'x"y',
                "x\ty",
                "x\x1fy",
                "x\x7fy",
            ):
                with self.subTest(unsafe=unsafe):
                    for host_name, host in POWERSHELL_HOSTS:
                        with self.subTest(host=host_name):
                            marker.unlink(missing_ok=True)
                            completed = subprocess.run(
                                [
                                    host,
                                    "-NoLogo",
                                    "-NoProfile",
                                    "-NonInteractive",
                                    "-ExecutionPolicy",
                                    "Bypass",
                                    "-File",
                                    str(runner),
                                    str(batch),
                                    "--describe",
                                    unsafe,
                                ],
                                check=False,
                                capture_output=True,
                                text=True,
                                timeout=15,
                            )
                            self.assertEqual(2, completed.returncode, completed.stderr)
                            self.assertFalse(marker.exists())


class PlanTests(unittest.TestCase):
    def test_plan_is_stable_and_hashes_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            input_path = Path(raw_dir) / "plan.json"
            input_path.write_text('{"version":1}', encoding="utf-8")
            command = [
                kafka_tool("kafka-reassign-partitions"),
                "--execute",
                "--reassignment-json-file",
                str(input_path),
            ]
            first = kafka_guard.build_plan("cluster-a", "prod", "4.3.0", command, [str(input_path)])
            second = kafka_guard.build_plan("cluster-a", "prod", "4.3.0", command, [str(input_path)])
            self.assertEqual(first["change_id"], second["change_id"])
            self.assertIn("NGUY HIỂM cluster-a", first["confirmation_phrase"])
            input_path.write_text('{"version":2}', encoding="utf-8")
            changed = kafka_guard.build_plan("cluster-a", "prod", "4.3.0", command, [str(input_path)])
            self.assertNotEqual(first["change_id"], changed["change_id"])
            version_changed = kafka_guard.build_plan("cluster-a", "prod", "4.4.0", command, [str(input_path)])
            self.assertNotEqual(changed["change_id"], version_changed["change_id"])

    def test_minimum_risk_only_escalates_and_changes_approval_surface(self) -> None:
        standard_command = [kafka_tool("kafka-topics"), "--create", "--topic", "orders"]
        default = kafka_guard.build_plan("cluster-a", "prod", "4.3.0", standard_command, [])
        explicit_standard = kafka_guard.build_plan(
            "cluster-a", "prod", "4.3.0", standard_command, [], minimum_risk="standard"
        )
        escalated = kafka_guard.build_plan(
            "cluster-a", "prod", "4.3.0", standard_command, [], minimum_risk="high"
        )
        self.assertEqual("standard", default["effective_risk"])
        self.assertEqual(default["change_id"], explicit_standard["change_id"])
        self.assertEqual("high", escalated["effective_risk"])
        self.assertNotEqual(default["change_id"], escalated["change_id"])
        self.assertIn("NGUY HIỂM", escalated["confirmation_phrase"])

        high_command = [kafka_tool("kafka-topics"), "--delete", "--topic", "orders"]
        high = kafka_guard.build_plan(
            "cluster-a", "prod", "4.3.0", high_command, [], minimum_risk="standard"
        )
        self.assertEqual("high", high["effective_risk"])
        self.assertIn("NGUY HIỂM", high["confirmation_phrase"])

        with self.assertRaisesRegex(ValueError, "requires MUTATION"):
            kafka_guard.build_plan(
                "cluster-a",
                "prod",
                "4.3.0",
                [kafka_tool("kafka-topics"), "--unsupported"],
                [],
                minimum_risk="high",
            )

    def test_console_producer_record_count_hash_and_change_id(self) -> None:
        cases = {
            "lf-ended": (b"one\ntwo\n", 2),
            "lf-open": (b"one\ntwo", 2),
            "crlf": (b"one\r\ntwo\r\n", 2),
            "cr": (b"one\rtwo", 2),
            "unicode": ("một\nhai".encode("utf-8"), 2),
        }
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            command = [kafka_tool("kafka-console-producer"), "--topic", "orders"]
            for name, (content, expected_count) in cases.items():
                with self.subTest(name=name):
                    payload = directory / f"{name}.records"
                    payload.write_bytes(content)
                    first = kafka_guard.build_plan("cluster-a", "prod", "4.3.0", command, [str(payload)])
                    second = kafka_guard.build_plan("cluster-a", "prod", "4.3.0", command, [str(payload)])
                    self.assertEqual(expected_count, first["producer_record_count"])
                    self.assertEqual(hashlib.sha256(content).hexdigest(), first["inputs"][0]["sha256"])
                    self.assertEqual(first["change_id"], second["change_id"])

    def test_console_producer_rejects_empty_payload_and_custom_line_reader(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            payload = Path(raw_dir) / "empty.records"
            payload.write_bytes(b"")
            command = [kafka_tool("kafka-console-producer"), "--topic", "orders"]
            with self.assertRaisesRegex(ValueError, "payload.*empty"):
                kafka_guard.build_plan("cluster-a", "prod", "4.3.0", command, [str(payload)])
            with self.assertRaisesRegex(ValueError, "requires MUTATION"):
                kafka_guard.build_plan(
                    "cluster-a",
                    "prod",
                    "4.3.0",
                    [*command, "--line-reader", "com.example.CustomReader"],
                    [str(payload)],
                )

    def test_console_producer_reader_config_is_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            reader_config = directory / "reader.properties"
            payload = directory / "payload.records"
            reader_config.write_text("parse.key=false\n", encoding="utf-8")
            payload.write_text("one\n", encoding="utf-8")
            command = [
                kafka_tool("kafka-console-producer"),
                "--topic",
                "orders",
                "--reader-config",
                str(reader_config),
            ]
            with self.assertRaisesRegex(ValueError, "must be passed via --input-file"):
                kafka_guard.build_plan("cluster-a", "prod", "4.3.0", command, [str(payload)])
            planned = kafka_guard.build_plan(
                "cluster-a", "prod", "4.3.0", command, [str(reader_config), str(payload)]
            )
            self.assertEqual(1, planned["producer_record_count"])
            self.assertEqual(2, len(planned["inputs"]))

    def test_plan_requires_referenced_inputs_and_producer_payload(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir:
            input_path = Path(raw_dir) / "plan.json"
            input_path.write_text('{"version":1}', encoding="utf-8")
            command = [kafka_tool("kafka-reassign-partitions"), "--execute", "--reassignment-json-file", str(input_path)]
            with self.assertRaisesRegex(ValueError, "must be passed via --input-file"):
                kafka_guard.build_plan("cluster-a", "prod", "4.3.0", command, [])
            leader_command = [
                kafka_tool("kafka-leader-election"),
                "--election-type",
                "preferred",
                "--path-to-json-file",
                str(input_path),
            ]
            with self.assertRaisesRegex(ValueError, "must be passed via --input-file"):
                kafka_guard.build_plan("cluster-a", "prod", "4.3.0", leader_command, [])
            leader_plan = kafka_guard.build_plan(
                "cluster-a", "prod", "4.3.0", leader_command, [str(input_path)]
            )
            input_path.write_text('{"version":2}', encoding="utf-8")
            changed_leader_plan = kafka_guard.build_plan(
                "cluster-a", "prod", "4.3.0", leader_command, [str(input_path)]
            )
            self.assertNotEqual(leader_plan["change_id"], changed_leader_plan["change_id"])
            config_command = [
                kafka_tool("kafka-configs"),
                "--alter",
                "--entity-type",
                "topics",
                "--entity-name",
                "orders",
                "--add-config-file",
                str(input_path),
            ]
            with self.assertRaisesRegex(ValueError, "must be passed via --input-file"):
                kafka_guard.build_plan("cluster-a", "prod", "4.3.0", config_command, [])
            perf_command = [
                kafka_tool("kafka-producer-perf-test"),
                "--topic",
                "orders",
                "--num-records",
                "1",
                "--payload-file",
                str(input_path),
            ]
            with self.assertRaisesRegex(ValueError, "must be passed via --input-file"):
                kafka_guard.build_plan("cluster-a", "prod", "4.3.0", perf_command, [])
            client_config = Path(raw_dir) / "client.properties"
            client_config.write_text("security.protocol=SSL\n", encoding="utf-8")
            configured_delete = [
                kafka_tool("kafka-topics"),
                "--delete",
                "--topic",
                "orders",
                "--command-config",
                str(client_config),
            ]
            with self.assertRaisesRegex(ValueError, "must be passed via --input-file"):
                kafka_guard.build_plan("cluster-a", "prod", "4.3.0", configured_delete, [])
            configured_plan = kafka_guard.build_plan(
                "cluster-a", "prod", "4.3.0", configured_delete, [str(client_config)]
            )
            client_config.write_text("security.protocol=SASL_SSL\n", encoding="utf-8")
            changed_configured_plan = kafka_guard.build_plan(
                "cluster-a", "prod", "4.3.0", configured_delete, [str(client_config)]
            )
            self.assertNotEqual(configured_plan["change_id"], changed_configured_plan["change_id"])
            server_command = [kafka_tool("kafka-server-start"), str(input_path)]
            with self.assertRaisesRegex(ValueError, "must be passed via --input-file"):
                kafka_guard.build_plan("cluster-a", "prod", "4.3.0", server_command, [])
            server_plan = kafka_guard.build_plan(
                "cluster-a", "prod", "4.3.0", server_command, [str(input_path)]
            )
            self.assertEqual("server-lifecycle", server_plan["classification"]["action"])
            with self.assertRaisesRegex(ValueError, "requires an absolute positional server config"):
                kafka_guard.build_plan(
                    "cluster-a", "prod", "4.3.0", [kafka_tool("kafka-server-start"), "--version"], []
                )
        with self.assertRaisesRegex(ValueError, "requires exactly one exact payload file"):
            kafka_guard.build_plan(
                "cluster-a", "prod", "4.3.0", [kafka_tool("kafka-console-producer"), "--topic", "orders"], []
            )
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            producer_config = directory / "producer.properties"
            payload = directory / "payload.jsonl"
            producer_config.write_text("acks=all\n", encoding="utf-8")
            payload.write_text('{"event":"created"}\n', encoding="utf-8")
            producer_command = [
                kafka_tool("kafka-console-producer"),
                "--topic",
                "orders",
                "--producer.config",
                str(producer_config),
            ]
            with self.assertRaisesRegex(ValueError, "exactly one exact payload file"):
                kafka_guard.build_plan(
                    "cluster-a", "prod", "4.3.0", producer_command, [str(producer_config)]
                )
            producer_plan = kafka_guard.build_plan(
                "cluster-a",
                "prod",
                "4.3.0",
                producer_command,
                [str(producer_config), str(payload)],
            )
            self.assertEqual(2, len(producer_plan["inputs"]))

    def test_plan_rejects_non_mutation(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires MUTATION"):
            kafka_guard.build_plan("cluster-a", "prod", "4.3.0", [kafka_tool("kafka-topics"), "--list"], [])

    def test_plan_rejects_tilde_input_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "--input-file must be absolute"):
            kafka_guard.build_plan(
                "cluster-a",
                "prod",
                "4.3.0",
                [kafka_tool("kafka-console-producer"), "--topic", "orders"],
                ["~/payload.json"],
            )


if __name__ == "__main__":
    unittest.main()
