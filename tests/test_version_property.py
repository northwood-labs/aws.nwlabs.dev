# Feature: template-variables, Property 1: Version extraction round-trip
# Feature: template-variables, Property 2: Non-matching output returns None
# Feature: template-variables, Property 3: First match wins for multiple provider lines
#
# **Validates: Requirements 1.1, 1.2, 1.4, 6.1, 6.2, 6.3**

import re

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from generate.cli import parse_provider_version

# ------------------------------------------------------------------------------
# STRATEGIES


def terraform_version_output(major: int, minor: int, patch: int) -> str:
    """
    Build a realistic `terraform --version` output string containing a
    hashicorp/aws provider line with the given version components.
    """

    return (
        f"Terraform v1.15.1\non darwin_arm64\n+ provider registry.terraform.io/hashicorp/aws v{major}.{minor}.{patch}\n"
    )


# Pattern that matches the hashicorp/aws provider line
AWS_PROVIDER_PATTERN: re.Pattern[str] = re.compile(
    r"\+\s+provider\s+registry\.terraform\.io/hashicorp/aws\s+v\d+\.\d+\.\d+"
)


# ------------------------------------------------------------------------------
# PROPERTY 1: VERSION EXTRACTION ROUND-TRIP


@settings(max_examples=100)
@given(
    major=st.integers(min_value=0, max_value=999),
    minor=st.integers(min_value=0, max_value=999),
    patch=st.integers(min_value=0, max_value=999),
)
def test_property_1_version_extraction_round_trip(major: int, minor: int, patch: int) -> None:
    """
    For any three non-negative integers (major, minor, patch), if a
    `terraform --version` output string contains the line
    `+ provider registry.terraform.io/hashicorp/aws v<major>.<minor>.<patch>`,
    then `parse_provider_version` shall return the string
    "<major>.<minor>.<patch>" with the `v` prefix removed.

    **Validates: Requirements 1.1, 6.1**
    """

    # Feature: template-variables, Property 1: Version extraction round-trip
    output = terraform_version_output(major, minor, patch)
    result = parse_provider_version(output)
    expected = f"{major}.{minor}.{patch}"
    assert result == expected, f"Expected '{expected}' but got '{result}'"


# ------------------------------------------------------------------------------
# PROPERTY 2: NON-MATCHING OUTPUT RETURNS NONE


@settings(max_examples=100)
@given(
    lines=st.lists(
        st.text(
            alphabet=st.characters(
                categories=("L", "N", "P", "Z", "S"),  # zuban: ignore[arg-type]
                exclude_characters="+",
            ),
            min_size=0,
            max_size=100,
        ),
        min_size=0,
        max_size=10,
    )
)
def test_property_2_non_matching_output_returns_none(
    lines: list[str],
) -> None:
    """
    For any multi-line string that does not contain a line matching the
    pattern `+ provider registry.terraform.io/hashicorp/aws
    v<digits>.<digits>.<digits>`, `parse_provider_version` shall return
    None.

    **Validates: Requirements 1.4, 6.2**
    """

    # Feature: template-variables, Property 2: Non-matching output returns None
    output = "\n".join(lines)

    # Filter out any accidentally matching strings
    assume(not AWS_PROVIDER_PATTERN.search(output))

    result = parse_provider_version(output)
    assert result is None, f"Expected None for non-matching output but got '{result}'"


# ------------------------------------------------------------------------------
# PROPERTY 3: FIRST MATCH WINS FOR MULTIPLE PROVIDER LINES


@settings(max_examples=100)
@given(
    major1=st.integers(min_value=0, max_value=999),
    minor1=st.integers(min_value=0, max_value=999),
    patch1=st.integers(min_value=0, max_value=999),
    major2=st.integers(min_value=0, max_value=999),
    minor2=st.integers(min_value=0, max_value=999),
    patch2=st.integers(min_value=0, max_value=999),
)
def test_property_3_first_match_wins(
    major1: int,
    minor1: int,
    patch1: int,
    major2: int,
    minor2: int,
    patch2: int,
) -> None:
    """
    For any `terraform --version` output containing two or more lines
    matching the `hashicorp/aws` provider pattern with distinct version
    strings, `parse_provider_version` shall return the version from the
    first matching line only.

    **Validates: Requirements 1.2, 6.3**
    """

    # Feature: template-variables, Property 3: First match wins for multiple provider lines
    version1 = f"{major1}.{minor1}.{patch1}"
    version2 = f"{major2}.{minor2}.{patch2}"

    # Ensure versions are distinct so the test is meaningful
    assume(version1 != version2)

    output = (
        f"Terraform v1.15.1\n"
        f"on darwin_arm64\n"
        f"+ provider registry.terraform.io/hashicorp/aws v{version1}\n"
        f"+ provider registry.terraform.io/hashicorp/aws v{version2}\n"
    )

    result = parse_provider_version(output)
    assert result == version1, f"Expected first version '{version1}' but got '{result}'"
