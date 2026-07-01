# Integration test: end-to-end run with mocked tfschema output.
#
# **Validates: Requirements 4.1, 4.2, 4.5, 5.1, 5.2, 7.1, 7.2, 7.3, 8.2, 8.3**

import shutil
from pathlib import Path
from unittest.mock import patch

from generate.cli import main

# ------------------------------------------------------------------------------
# HELPERS


TEMPLATE_SOURCE = Path(__file__).resolve().parent.parent / "src" / "generate" / "templates" / "redirect.html.j2"
R_TEMPLATE_SOURCE = Path(__file__).resolve().parent.parent / "src" / "generate" / "templates" / "r.html.j2"
D_TEMPLATE_SOURCE = Path(__file__).resolve().parent.parent / "src" / "generate" / "templates" / "d.html.j2"
INDEX_TEMPLATE_SOURCE = Path(__file__).resolve().parent.parent / "src" / "generate" / "templates" / "index.html.j2"


def setup_project(tmp_path: Path) -> None:
    """
    Set up a temporary project directory with the template and docs structure.
    """

    # Copy actual templates into expected location
    template_dir = tmp_path / "src" / "generate" / "templates"
    template_dir.mkdir(parents=True)
    shutil.copy(TEMPLATE_SOURCE, template_dir / "redirect.html.j2")
    shutil.copy(R_TEMPLATE_SOURCE, template_dir / "r.html.j2")
    shutil.copy(D_TEMPLATE_SOURCE, template_dir / "d.html.j2")
    shutil.copy(INDEX_TEMPLATE_SOURCE, template_dir / "index.html.j2")

    # Create docs directory with preserved files
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "404.html").write_text("not found")
    (docs_dir / ".nojekyll").write_text("")
    (docs_dir / "CNAME").write_text("aws.nwlabs.dev")

    # Create stale files that should be removed
    stale_resource = docs_dir / "r" / "old_resource"
    stale_resource.mkdir(parents=True)
    (stale_resource / "index.html").write_text("stale resource")

    stale_data = docs_dir / "d" / "old_data_source"
    stale_data.mkdir(parents=True)
    (stale_data / "index.html").write_text("stale data source")


# ------------------------------------------------------------------------------
# INTEGRATION TESTS


@patch("generate.cli.run_terraform_version")
@patch("generate.cli.run_tfschema")
def test_end_to_end_generates_correct_files(
    mock_tfschema: object,
    mock_terraform_version: object,
    tmp_path: Path,
) -> None:
    """
    Full end-to-end test: mock tfschema output and verify file creation,
    content, directory structure, stale file cleanup, and preserved files.
    """

    setup_project(tmp_path)

    # Mock tfschema: first call returns resources, second returns data sources
    mock_tfschema.side_effect = [  # type: ignore[attr-defined]
        ["aws_instance", "aws_vpc"],
        ["aws_ami"],
    ]

    # Mock terraform --version output
    mock_terraform_version.return_value = (  # type: ignore[attr-defined]
        "Terraform v1.15.1\non darwin_arm64\n+ provider registry.terraform.io/hashicorp/aws v6.52.0\n"
    )

    # Patch project_root and template_dir to use tmp_path
    with patch("generate.cli.Path") as mock_path_cls:
        # Path(__file__).resolve().parent.parent.parent -> tmp_path
        mock_file_path = mock_path_cls.return_value
        mock_file_path.resolve.return_value.parent.parent.parent = tmp_path

        # Path(__file__).parent / "templates" -> actual template dir
        mock_file_path.parent.__truediv__ = lambda self, other: tmp_path / "src" / "generate" / other

        exit_code = main()

    assert exit_code == 0

    docs_dir = tmp_path / "docs"

    # Verify resource redirect files exist
    instance_html = docs_dir / "r" / "instance" / "index.html"
    vpc_html = docs_dir / "r" / "vpc" / "index.html"
    assert instance_html.exists(), "docs/r/instance/index.html should exist"
    assert vpc_html.exists(), "docs/r/vpc/index.html should exist"

    # Verify data source redirect file exists
    ami_html = docs_dir / "d" / "ami" / "index.html"
    assert ami_html.exists(), "docs/d/ami/index.html should exist"

    # Verify HTML content of a resource redirect
    content = instance_html.read_text()
    assert '<meta charset="utf-8">' in content
    assert "meta http-equiv=\"refresh\" content=\"0;URL='" in content
    assert "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance" in content
    assert '<link rel="canonical"' in content
    assert "<body>" in content
    assert "<a href=" in content

    # Verify HTML content of a data source redirect
    ami_content = ami_html.read_text()
    assert "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ami" in ami_content

    # Verify stale files were cleaned
    assert not (docs_dir / "r" / "old_resource").exists(), "Stale resource directory should be removed"
    assert not (docs_dir / "d" / "old_data_source").exists(), "Stale data source directory should be removed"

    # Verify preserved files still exist
    assert (docs_dir / "404.html").exists(), "docs/404.html should be preserved"
    assert (docs_dir / ".nojekyll").exists(), "docs/.nojekyll should be preserved"
    assert (docs_dir / "CNAME").exists(), "docs/CNAME should be preserved"
    assert (docs_dir / "404.html").read_text() == "not found"
    assert (docs_dir / "CNAME").read_text() == "aws.nwlabs.dev"


@patch("generate.cli.run_terraform_version")
@patch("generate.cli.run_tfschema")
def test_index_templates_rendered_with_correct_content(
    mock_tfschema: object,
    mock_terraform_version: object,
    tmp_path: Path,
) -> None:
    """
    Verify that docs/r/index.html and docs/d/index.html are created
    with the correct provider version and resource/datasource entries.

    **Validates: Requirements 4.1, 4.2, 4.5, 5.1, 5.2**
    """

    setup_project(tmp_path)

    # Mock tfschema: resources and data sources
    mock_tfschema.side_effect = [  # type: ignore[attr-defined]
        ["aws_instance", "aws_vpc"],
        ["aws_ami"],
    ]

    # Mock terraform --version output
    mock_terraform_version.return_value = (  # type: ignore[attr-defined]
        "Terraform v1.15.1\non darwin_arm64\n+ provider registry.terraform.io/hashicorp/aws v6.52.0\n"
    )

    # Patch project_root and template_dir to use tmp_path
    with patch("generate.cli.Path") as mock_path_cls:
        mock_file_path = mock_path_cls.return_value
        mock_file_path.resolve.return_value.parent.parent.parent = tmp_path
        mock_file_path.parent.__truediv__ = lambda self, other: tmp_path / "src" / "generate" / other

        exit_code = main()

    assert exit_code == 0

    docs_dir = tmp_path / "docs"

    # ------------------------------------------------------------------
    # VERIFY docs/r/index.html

    r_index = docs_dir / "r" / "index.html"
    assert r_index.exists(), "docs/r/index.html should be created"

    r_content = r_index.read_text()

    # Contains links to resources with correct href values
    assert 'href="https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance"' in r_content, (
        "docs/r/index.html should link to aws_instance resource"
    )

    assert 'href="https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc"' in r_content, (
        "docs/r/index.html should link to aws_vpc resource"
    )

    # Contains full_name entries
    assert "instance" in r_content, "docs/r/index.html should display instance"
    assert "vpc" in r_content, "docs/r/index.html should display vpc"

    # ------------------------------------------------------------------
    # VERIFY docs/d/index.html

    d_index = docs_dir / "d" / "index.html"
    assert d_index.exists(), "docs/d/index.html should be created"

    d_content = d_index.read_text()

    # Contains links to data sources with correct href values
    assert 'href="https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ami"' in d_content, (
        "docs/d/index.html should link to aws_ami data source"
    )

    # Contains full_name entries
    assert "ami" in d_content, "docs/d/index.html should display ami"

    # ------------------------------------------------------------------
    # VERIFY individual redirect files still work

    instance_html = docs_dir / "r" / "instance" / "index.html"
    assert instance_html.exists(), "Individual redirect files should still be generated"

    instance_content = instance_html.read_text()
    assert "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance" in instance_content, (
        "Redirect should point to the correct registry URL"
    )

    # ------------------------------------------------------------------
    # VERIFY docs/index.html (root index page)

    root_index = docs_dir / "index.html"
    assert root_index.exists(), "docs/index.html should be created"

    root_content = root_index.read_text()

    # Contains provider version string
    assert "6.52.0" in root_content, "docs/index.html should contain the provider version"

    # Contains expected static content from the template
    assert "hashicorp/aws" in root_content, "docs/index.html should reference hashicorp/aws"
