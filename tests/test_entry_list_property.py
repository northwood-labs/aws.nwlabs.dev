# Feature: template-variables, Property 4: Entry list preserves input order
# Feature: template-variables, Property 5: Entry fields are correctly constructed
#
# **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 3.1, 3.2, 3.3, 3.5**

from hypothesis import given, settings
from hypothesis import strategies as st

from generate.cli import build_entry_list, build_target_url

# ------------------------------------------------------------------------------
# STRATEGIES

# Valid Terraform resource/data source names: lowercase letters, digits, and
# underscores, starting with a letter, length 1–50.
_name_strategy = st.from_regex(r"[a-z][a-z0-9_]{0,49}", fullmatch=True)

# Names with the aws_ prefix
_aws_prefixed_name = _name_strategy.map(lambda s: f"aws_{s}")

# Names without the aws_ prefix (filtered to exclude aws_ start)
_non_prefixed_name = st.from_regex(r"[a-z][a-z0-9_]{0,49}", fullmatch=True).filter(lambda s: not s.startswith("aws_"))

# Mixed names: either prefixed or non-prefixed
_any_valid_name = st.one_of(_aws_prefixed_name, _non_prefixed_name)

# Category: either "resources" or "data-sources"
_category_strategy = st.sampled_from(["resources", "data-sources"])


# ------------------------------------------------------------------------------
# PROPERTY 4: ENTRY LIST PRESERVES INPUT ORDER


@settings(max_examples=100)
@given(
    names=st.lists(_any_valid_name, min_size=0, max_size=20),
    category=_category_strategy,
)
def test_property_4_entry_list_preserves_input_order(
    names: list[str],
    category: str,
) -> None:
    """
    For any list of valid resource or data source names and either category
    ("resources" or "data-sources"), build_entry_list shall produce an output
    list whose elements appear in the same order as the input names.

    **Validates: Requirements 2.1, 3.1**
    """

    # Feature: template-variables, Property 4: Entry list preserves input order

    # Build parallel stripped/original lists the same way the main code does
    stripped_names: list[str] = []
    original_names: list[str] = []

    for name in names:
        if name.startswith("aws_"):
            stripped = name[4:]
        else:
            stripped = name

        stripped_names.append(stripped)
        original_names.append(name)

    result = build_entry_list(stripped_names, original_names, category)

    # Output length must match input length
    assert len(result) == len(names)

    # Each entry's full_name must match the original name at the same index
    for i, entry in enumerate(result):
        assert entry["full_name"] == original_names[i], (
            f"Entry at index {i} has full_name '{entry['full_name']}' but expected '{original_names[i]}'"
        )


# ------------------------------------------------------------------------------
# PROPERTY 5: ENTRY FIELDS ARE CORRECTLY CONSTRUCTED


@settings(max_examples=100)
@given(
    names=st.lists(_any_valid_name, min_size=1, max_size=20),
    category=_category_strategy,
)
def test_property_5_entry_fields_are_correctly_constructed(
    names: list[str],
    category: str,
) -> None:
    """
    For any valid name (with or without aws_ prefix) and either category, each
    entry produced by build_entry_list shall have an href equal to
    build_target_url(stripped_name, category) and a full_name equal to the
    original input name.

    **Validates: Requirements 2.2, 2.3, 2.5, 3.2, 3.3, 3.5**
    """

    # Feature: template-variables, Property 5: Entry fields are correctly constructed

    # Build parallel stripped/original lists
    stripped_names: list[str] = []
    original_names: list[str] = []

    for name in names:
        if name.startswith("aws_"):
            stripped = name[4:]
        else:
            stripped = name

        stripped_names.append(stripped)
        original_names.append(name)

    result = build_entry_list(stripped_names, original_names, category)

    for i, entry in enumerate(result):
        expected_href = build_target_url(stripped_names[i], category)
        assert entry["href"] == expected_href, (
            f"Entry at index {i} has href '{entry['href']}' but expected '{expected_href}'"
        )
        assert entry["full_name"] == original_names[i], (
            f"Entry at index {i} has full_name '{entry['full_name']}' but expected '{original_names[i]}'"
        )
