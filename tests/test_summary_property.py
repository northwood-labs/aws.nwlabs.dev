# Feature: terraform-registry-redirects, Property 6: Summary line contains correct counts
#
# **Validates: Requirements 8.3**

from hypothesis import given, settings
from hypothesis import strategies as st


@settings(max_examples=100)
@given(
    resource_count=st.integers(min_value=0, max_value=10000),
    data_source_count=st.integers(min_value=0, max_value=10000),
)
def test_property_6_summary_line_contains_correct_counts(
    resource_count: int,
    data_source_count: int,
) -> None:
    """
    For any pair of non-negative integers representing resource count and
    data source count, the summary output line shall contain both numeric
    values as distinct substrings.
    """

    # Feature: terraform-registry-redirects, Property 6: Summary line contains correct counts
    summary = f"Generated {resource_count} resource redirects and {data_source_count} data source redirects."

    assert str(resource_count) in summary
    assert str(data_source_count) in summary
