"""
Unit tests for error handling in the generate CLI.

Validates: Requirements 1.3, 1.4, 1.5, 2.3, 2.4, 2.5, 4.4, 5.4, 7.5, 9.4
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from generate.cli import clean_output_dirs, generate_redirects, main, run_tfschema

# ------------------------------------------------------------------------------
# TFSCHEMA COMMAND ERRORS


def test_run_tfschema_file_not_found() -> None:
    """
    When tfschema executable is not found on PATH, run_tfschema shall raise
    SystemExit.
    """

    with patch("generate.cli.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(SystemExit):
            run_tfschema(["resource", "list", "aws"])


def test_run_tfschema_non_zero_exit() -> None:
    """
    When tfschema returns a non-zero exit code, run_tfschema shall raise
    SystemExit.
    """

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("generate.cli.subprocess.run", return_value=mock_result):
        with pytest.raises(SystemExit):
            run_tfschema(["resource", "list", "aws"])


def test_run_tfschema_timeout() -> None:
    """
    When tfschema exceeds the timeout, run_tfschema shall raise SystemExit.
    """

    with patch(
        "generate.cli.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="tfschema", timeout=30),
    ):
        with pytest.raises(SystemExit):
            run_tfschema(["resource", "list", "aws"])


# ------------------------------------------------------------------------------
# EMPTY OUTPUT HANDLING


def test_main_empty_resources_exits() -> None:
    """
    When run_tfschema returns an empty resource list, main shall raise
    SystemExit with a non-zero status.
    """

    with patch("generate.cli.run_tfschema", return_value=[]):
        with pytest.raises(SystemExit):
            main()


def test_main_empty_data_sources_warns_continues(capsys: pytest.CaptureFixture[str]) -> None:
    """
    When run_tfschema returns data for resources but an empty list for data
    sources, main shall print a warning to stderr but continue execution.
    """

    def mock_run_tfschema(args: list[str], timeout: int = 30) -> list[str]:
        """
        Return a small resource list for resource calls, empty for data
        source calls.
        """

        if args[0] == "resource":
            return ["aws_instance", "aws_vpc"]

        return []

    with (
        patch("generate.cli.run_tfschema", side_effect=mock_run_tfschema),
        patch("generate.cli.clean_output_dirs"),
        patch("generate.cli.generate_redirects", return_value=2),
        patch("generate.cli.Environment") as mock_env_class,
    ):
        mock_env = MagicMock()
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        mock_env_class.return_value = mock_env

        result = main()

    captured = capsys.readouterr()
    assert "warning" in captured.err.lower() or "no data sources" in captured.err.lower()
    assert result == 0


# ------------------------------------------------------------------------------
# FILESYSTEM ERRORS


def test_clean_output_dirs_filesystem_error(tmp_path: Path) -> None:
    """
    When shutil.rmtree raises OSError during directory cleanup,
    clean_output_dirs shall raise SystemExit.
    """

    # Create the directory so the existence check passes
    target_dir = tmp_path / "docs" / "r"
    target_dir.mkdir(parents=True)

    with patch("generate.cli.shutil.rmtree", side_effect=OSError("Permission denied")):
        with pytest.raises(SystemExit):
            clean_output_dirs(tmp_path)


def test_generate_redirects_write_error(tmp_path: Path) -> None:
    """
    When writing a redirect file raises OSError, generate_redirects shall
    raise SystemExit.
    """

    mock_template = MagicMock()
    mock_template.render.return_value = "<html></html>"

    with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
        with pytest.raises(SystemExit):
            generate_redirects(["instance"], "resources", mock_template, tmp_path)


# ------------------------------------------------------------------------------
# TEMPLATE ERRORS


def test_main_template_not_found() -> None:
    """
    When the Jinja2 template cannot be found, main shall raise SystemExit.
    """

    from jinja2 import TemplateNotFound

    def mock_run_tfschema(args: list[str], timeout: int = 30) -> list[str]:
        """
        Return a valid resource list so execution reaches template loading.
        """

        if args[0] == "resource":
            return ["aws_instance"]

        return ["aws_ami"]

    with (
        patch("generate.cli.run_tfschema", side_effect=mock_run_tfschema),
        patch("generate.cli.clean_output_dirs"),
        patch("generate.cli.Environment") as mock_env_class,
    ):
        mock_env = MagicMock()
        mock_env.get_template.side_effect = TemplateNotFound("redirect.html.j2")
        mock_env_class.return_value = mock_env

        with pytest.raises(SystemExit):
            main()
