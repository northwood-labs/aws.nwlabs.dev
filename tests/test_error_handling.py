"""
Unit tests for error handling in the generate CLI.

Validates: Requirements 1.3, 1.4, 1.5, 2.3, 2.4, 2.5, 4.3, 4.4, 4.5, 5.3,
5.4, 5.5, 7.5, 9.4
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from generate.cli import (
    clean_output_dirs,
    generate_redirects,
    main,
    render_index_template,
    run_terraform_version,
    run_tfschema,
)

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
# TERRAFORM VERSION COMMAND ERRORS


def test_run_terraform_version_file_not_found() -> None:
    """
    When terraform executable is not found on PATH,
    run_terraform_version shall raise SystemExit.
    """

    with patch("generate.cli.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(SystemExit):
            run_terraform_version()


def test_run_terraform_version_timeout() -> None:
    """
    When terraform --version exceeds the timeout,
    run_terraform_version shall raise SystemExit.
    """

    with patch(
        "generate.cli.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="terraform", timeout=30),
    ):
        with pytest.raises(SystemExit):
            run_terraform_version()


def test_run_terraform_version_non_zero_exit() -> None:
    """
    When terraform --version returns a non-zero exit code,
    run_terraform_version shall raise SystemExit.
    """

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("generate.cli.subprocess.run", return_value=mock_result):
        with pytest.raises(SystemExit):
            run_terraform_version()


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
        patch(
            "generate.cli.run_terraform_version",
            return_value="+ provider registry.terraform.io/hashicorp/aws v6.52.0\n",
        ),
        patch("generate.cli.clean_output_dirs"),
        patch("generate.cli.generate_redirects", return_value=2),
        patch("generate.cli.render_index_template"),
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
        patch(
            "generate.cli.run_terraform_version",
            return_value="+ provider registry.terraform.io/hashicorp/aws v6.52.0\n",
        ),
        patch("generate.cli.clean_output_dirs"),
        patch("generate.cli.Environment") as mock_env_class,
    ):
        mock_env = MagicMock()
        mock_env.get_template.side_effect = TemplateNotFound("redirect.html.j2")
        mock_env_class.return_value = mock_env

        with pytest.raises(SystemExit):
            main()


# ------------------------------------------------------------------------------
# RENDER INDEX TEMPLATE ERRORS


def test_render_index_template_not_found(tmp_path: Path) -> None:
    """
    When the named template does not exist in the Jinja2 environment,
    render_index_template shall raise SystemExit.

    Validates: Requirements 4.3, 5.3
    """

    from jinja2 import Environment, FileSystemLoader

    # Use an empty directory as the template source — no templates exist
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    output_path = tmp_path / "output" / "index.html"
    context: dict[str, object] = {"items": []}

    with pytest.raises(SystemExit):
        render_index_template(env, "nonexistent.html.j2", output_path, context)


def test_render_index_template_render_failure(tmp_path: Path) -> None:
    """
    When the template fails to render due to an undefined variable error,
    render_index_template shall raise SystemExit.

    Validates: Requirements 5.4
    """

    from jinja2 import Environment, FileSystemLoader, StrictUndefined

    # Create a template that references an undefined variable
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "bad.html.j2"
    template_file.write_text("{{ undefined_var }}", encoding="utf-8")

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,
    )

    output_path = tmp_path / "output" / "index.html"
    context: dict[str, object] = {}

    with pytest.raises(SystemExit):
        render_index_template(env, "bad.html.j2", output_path, context)


def test_render_index_template_write_failure(tmp_path: Path) -> None:
    """
    When writing the rendered output raises an OSError,
    render_index_template shall raise SystemExit.

    Validates: Requirements 4.4, 5.5
    """

    from jinja2 import Environment, FileSystemLoader

    # Create a valid template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "good.html.j2"
    template_file.write_text("<html>{{ title }}</html>", encoding="utf-8")

    env = Environment(loader=FileSystemLoader(str(template_dir)))
    output_path = tmp_path / "output" / "index.html"
    context: dict[str, object] = {"title": "Test Page"}

    with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
        with pytest.raises(SystemExit):
            render_index_template(env, "good.html.j2", output_path, context)


def test_render_index_template_empty_list_succeeds(tmp_path: Path) -> None:
    """
    When the context contains an empty list, render_index_template shall
    render the template successfully without raising SystemExit.

    Validates: Requirements 4.5
    """

    from jinja2 import Environment, FileSystemLoader

    # Create a template that iterates over a list
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "listing.html.j2"
    template_file.write_text(
        "<ul>{% for item in resources %}<li>{{ item.full_name }}</li>{% endfor %}</ul>",
        encoding="utf-8",
    )

    env = Environment(loader=FileSystemLoader(str(template_dir)))
    output_path = tmp_path / "output" / "index.html"
    context: dict[str, object] = {
        "resources": [],
        "provider_version": "6.52.0",
    }

    # Should NOT raise SystemExit
    render_index_template(env, "listing.html.j2", output_path, context)

    # Verify the file was written
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert content == "<ul></ul>"
