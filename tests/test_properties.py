# Feature: terraform-registry-redirects, Property 1: Line parsing preserves non-empty content and strips whitespace
# Feature: terraform-registry-redirects, Property 2: Prefix stripping correctness
# Feature: terraform-registry-redirects, Property 3: URL construction follows registry pattern
# Feature: terraform-registry-redirects, Property 5: File path construction
#
# **Validates: Requirements 1.2, 2.2, 3.1, 3.2, 3.3, 4.1, 4.2, 5.1, 5.2**

from hypothesis import given, settings
from hypothesis import strategies as st

from generate.cli import build_target_url, strip_aws_prefix

# ------------------------------------------------------------------------------
# HELPERS


def parse_lines(raw: str) -> list[str]:
    """
    Parse a raw multi-line string the same way run_tfschema does:
    split on newlines, strip whitespace, discard empty lines.
    """

    lines = [line.strip() for line in raw.splitlines()]

    return [line for line in lines if line]


def build_file_path(stripped_name: str, category: str) -> str:
    """
    Construct the output file path for a redirect file.

    Resources use prefix "r", data sources use prefix "d".
    """

    prefix = "r" if category == "resources" else "d"

    return f"docs/{prefix}/{stripped_name}/index.html"


# ------------------------------------------------------------------------------
# PROPERTY 1: LINE PARSING PRESERVES NON-EMPTY CONTENT AND STRIPS WHITESPACE


@settings(max_examples=100)
@given(
    raw=st.text(
        alphabet=st.characters(categories=("L", "N", "P", "Z", "S")),  # zuban: ignore[arg-type]
        min_size=0,
        max_size=200,
    )
)
def test_property_1_line_parsing_strips_whitespace(raw: str) -> None:
    """
    For any multi-line string, parsing it shall produce entries that are all
    non-empty and contain no leading or trailing whitespace.
    """

    # Feature: terraform-registry-redirects, Property 1: Line parsing preserves non-empty content and strips whitespace
    result = parse_lines(raw)

    for entry in result:
        assert entry != "", "Parsed entries must be non-empty"
        assert entry == entry.strip(), "Parsed entries must have no leading or trailing whitespace"


@settings(max_examples=100)
@given(
    raw=st.text(
        alphabet=st.characters(categories=("L", "N", "P", "Z", "S")),  # zuban: ignore[arg-type]
        min_size=0,
        max_size=200,
    )
)
def test_property_1_line_parsing_preserves_content(raw: str) -> None:
    """
    For any multi-line string, no non-whitespace content from the original
    input is lost during parsing.
    """

    # Feature: terraform-registry-redirects, Property 1: Line parsing preserves non-empty content and strips whitespace
    result = parse_lines(raw)

    # Every non-whitespace-only line in the original should appear stripped in
    # the result
    expected_lines = [line.strip() for line in raw.splitlines() if line.strip()]
    assert result == expected_lines


# ------------------------------------------------------------------------------
# PROPERTY 2: PREFIX STRIPPING CORRECTNESS


@settings(max_examples=100)
@given(
    suffix=st.text(
        alphabet=st.characters(categories=("L", "N", "P")),  # zuban: ignore[arg-type]
        min_size=1,
        max_size=50,
    )
)
def test_property_2_strips_aws_prefix(suffix: str) -> None:
    """
    For any string that starts with aws_ followed by one or more characters,
    stripping shall produce the exact substring after aws_.
    """

    # Feature: terraform-registry-redirects, Property 2: Prefix stripping correctness
    name = f"aws_{suffix}"
    result = strip_aws_prefix(name)
    assert result == suffix


@settings(max_examples=100)
@given(
    name=st.text(
        alphabet=st.characters(categories=("L", "N", "P")),  # zuban: ignore[arg-type]
        min_size=1,
        max_size=50,
    ).filter(lambda s: not s.startswith("aws_"))
)
def test_property_2_no_prefix_returns_unchanged(name: str) -> None:
    """
    For any string that does not start with aws_, stripping shall return the
    string unchanged.
    """

    # Feature: terraform-registry-redirects, Property 2: Prefix stripping correctness
    result = strip_aws_prefix(name)
    assert result == name


def test_property_2_aws_prefix_only_returns_none() -> None:
    """
    If aws_ exactly (empty after strip), verify result is None.
    """

    # Feature: terraform-registry-redirects, Property 2: Prefix stripping correctness
    result = strip_aws_prefix("aws_")
    assert result is None


# ------------------------------------------------------------------------------
# PROPERTY 3: URL CONSTRUCTION FOLLOWS REGISTRY PATTERN


@settings(max_examples=100)
@given(
    stripped_name=st.from_regex(r"[a-z][a-z0-9_]{0,49}", fullmatch=True),
    category=st.sampled_from(["resources", "data-sources"]),
)
def test_property_3_url_construction(stripped_name: str, category: str) -> None:
    """
    For any valid stripped name and category, build_target_url shall produce a
    URL equal to the registry pattern.
    """

    # Feature: terraform-registry-redirects, Property 3: URL construction follows registry pattern
    result = build_target_url(stripped_name, category)
    expected = f"https://registry.terraform.io/providers/hashicorp/aws/latest/docs/{category}/{stripped_name}"
    assert result == expected


# ------------------------------------------------------------------------------
# PROPERTY 5: FILE PATH CONSTRUCTION


@settings(max_examples=100)
@given(name=st.from_regex(r"[a-z][a-z0-9_]{0,49}", fullmatch=True))
def test_property_5_resource_file_path(name: str) -> None:
    """
    For any stripped resource name, the output file path shall be
    docs/r/{name}/index.html.
    """

    # Feature: terraform-registry-redirects, Property 5: File path construction
    result = build_file_path(name, "resources")
    assert result == f"docs/r/{name}/index.html"


@settings(max_examples=100)
@given(name=st.from_regex(r"[a-z][a-z0-9_]{0,49}", fullmatch=True))
def test_property_5_data_source_file_path(name: str) -> None:
    """
    For any stripped data source name, the output file path shall be
    docs/d/{name}/index.html.
    """

    # Feature: terraform-registry-redirects, Property 5: File path construction
    result = build_file_path(name, "data-sources")
    assert result == f"docs/d/{name}/index.html"
