import shutil
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS


def run_tfschema(args: list[str], timeout: int = 30) -> list[str]:
    """
    Execute a tfschema subcommand, capture stdout, and return parsed lines.

    Raises SystemExit on command failure, timeout, or missing executable.
    """

    cmd = ["tfschema", *args]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    except FileNotFoundError:
        print(
            "Error: 'tfschema' executable not found on PATH.",
            file=sys.stderr,
        )

        sys.exit(1)

    except subprocess.TimeoutExpired:
        print(
            f"Error: '{' '.join(cmd)}' timed out after {timeout} seconds.",
            file=sys.stderr,
        )

        sys.exit(1)

    if result.returncode != 0:
        print(
            f"Error: '{' '.join(cmd)}' exited with code {result.returncode}.",
            file=sys.stderr,
        )

        sys.exit(1)

    lines = [line.strip() for line in result.stdout.splitlines()]

    return [line for line in lines if line]


def strip_aws_prefix(name: str) -> str | None:
    """
    Strip the leading `aws_` prefix from a Terraform type name.

    Returns None if stripping would produce an empty string, logging a warning.
    Returns the name unchanged if it does not start with `aws_`.
    """

    if not name.startswith("aws_"):
        return name

    stripped = name[4:]

    if not stripped:
        print(
            f"Warning: stripping 'aws_' from '{name}' produces an empty string; skipping.",
            file=sys.stderr,
        )

        return None

    return stripped


def build_target_url(stripped_name: str, category: str) -> str:
    """
    Construct the full Terraform Registry URL for a given name and category.

    Category is either "resources" or "data-sources".
    """

    return f"https://registry.terraform.io/providers/hashicorp/aws/latest/docs/{category}/{stripped_name}"


def clean_output_dirs(base: Path) -> None:
    """
    Remove all contents of `docs/r/` and `docs/d/` under the given base path.

    Silently skips directories that do not exist. Raises SystemExit on other
    filesystem errors.
    """

    for subdir in ("r", "d"):
        target = base / "docs" / subdir

        if not target.exists():
            continue

        try:
            shutil.rmtree(target)

        except OSError as exc:
            print(
                f"Error: failed to remove '{target}': {exc}",
                file=sys.stderr,
            )

            sys.exit(1)


def generate_redirects(
    names: list[str],
    category: str,
    template: Template,
    base: Path,
) -> int:
    """
    Render and write redirect HTML files for a list of stripped names.

    Category maps to path prefix: "resources" -> "r", "data-sources" -> "d".
    Returns the count of files written. Raises SystemExit on filesystem write
    errors.
    """

    category_prefix = "r" if category == "resources" else "d"
    count = 0

    for stripped_name in names:
        target_url = build_target_url(stripped_name, category)
        original_name = f"aws_{stripped_name}"

        html = template.render(
            target_url=target_url,
            original_name=original_name,
            stripped_name=stripped_name,
        )

        output_path = base / "docs" / category_prefix / stripped_name / "index.html"

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")

        except OSError as exc:
            print(
                f"Error: failed to write '{output_path}': {exc}",
                file=sys.stderr,
            )

            sys.exit(1)

        count += 1

    return count


# ------------------------------------------------------------------------------
# MAIN


def main() -> int:
    """
    CLI entry point for the redirect generator.

    Orchestrates the full pipeline: fetch type names from tfschema, strip
    prefixes, clean output directories, load template, generate redirects,
    and print a summary.
    """

    project_root = Path(__file__).resolve().parent.parent.parent

    # Fetch resource list (must be non-empty)
    resources = run_tfschema(["resource", "list", "aws"])

    if not resources:
        print(
            "Error: 'tfschema resource list aws' returned no resources.",
            file=sys.stderr,
        )

        sys.exit(1)

    # Fetch data source list (allowed to be empty)
    data_sources = run_tfschema(["data", "list", "aws"])

    if not data_sources:
        print(
            "Warning: 'tfschema data list aws' returned no data sources.",
            file=sys.stderr,
        )

    # Strip aws_ prefix from all names, skipping invalid entries
    stripped_resources: list[str] = []

    for name in resources:
        stripped = strip_aws_prefix(name)

        if stripped is not None:
            stripped_resources.append(stripped)

    stripped_data_sources: list[str] = []

    for name in data_sources:
        stripped = strip_aws_prefix(name)

        if stripped is not None:
            stripped_data_sources.append(stripped)

    # Clean stale output directories
    clean_output_dirs(project_root)

    # Load Jinja2 template
    template_dir = Path(__file__).parent / "templates"

    try:
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("redirect.html.j2")

    except TemplateNotFound as exc:
        print(
            f"Error: template not found: {exc}",
            file=sys.stderr,
        )

        sys.exit(1)

    except Exception as exc:
        print(
            f"Error: failed to load Jinja2 template: {exc}",
            file=sys.stderr,
        )

        sys.exit(1)

    # Generate resource redirects
    resource_count = generate_redirects(stripped_resources, "resources", template, project_root)

    # Generate data source redirects
    data_source_count = generate_redirects(stripped_data_sources, "data-sources", template, project_root)

    # Print summary
    print(f"Generated {resource_count} resource redirects and {data_source_count} data source redirects.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
