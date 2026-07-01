# Feature: terraform-registry-redirects, Property 4: Template rendering produces complete HTML structure
#
# **Validates: Requirements 4.2, 4.3, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 9.2, 9.3**

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from jinja2 import Environment, FileSystemLoader

# ------------------------------------------------------------------------------
# HELPERS


def load_template() -> Environment:
    """
    Load the Jinja2 environment pointing at the project's template directory.
    """

    template_dir = Path(__file__).resolve().parent.parent / "src" / "generate" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    return env


# Strategy: generate alphanumeric resource names for URL path segments
_name_strategy = st.from_regex(r"[a-z][a-z0-9_]{0,49}", fullmatch=True)


# ------------------------------------------------------------------------------
# PROPERTY 4: TEMPLATE RENDERING PRODUCES COMPLETE HTML STRUCTURE


@settings(max_examples=100)
@given(name=_name_strategy)
def test_property_4_template_rendering_complete_html(name: str) -> None:
    """
    For any valid target URL, original name, and stripped name, rendering the
    redirect template shall produce output containing a complete HTML structure
    with all required elements.
    """

    # Feature: terraform-registry-redirects, Property 4: Template rendering produces complete HTML structure
    env = load_template()
    template = env.get_template("redirect.html.j2")

    target_url = f"https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/{name}"
    original_name = f"aws_{name}"
    stripped_name = name

    html = template.render(
        target_url=target_url,
        original_name=original_name,
        stripped_name=stripped_name,
    )

    # meta charset
    assert '<meta charset="utf-8">' in html, "Output must contain <meta charset=\"utf-8\"> tag"

    # meta refresh redirect
    expected_refresh = f"<meta http-equiv=\"refresh\" content=\"0;URL='{target_url}'\">"
    assert expected_refresh in html, "Output must contain meta http-equiv refresh tag with target_url"

    # canonical link
    expected_canonical = f'<link rel="canonical" href="{target_url}">'
    assert expected_canonical in html, "Output must contain canonical link with target_url"

    # title element with non-empty text
    title_start = html.find("<title>")
    title_end = html.find("</title>")
    assert title_start != -1, "Output must contain a <title> element"
    assert title_end != -1, "Output must contain a closing </title> tag"
    title_text = html[title_start + len("<title>") : title_end].strip()
    assert len(title_text) > 0, "Title element must contain non-empty text"

    # body with anchor element
    assert "<body>" in html, "Output must contain a <body> element"
    body_start = html.find("<body>")
    body_end = html.find("</body>")
    body_content = html[body_start:body_end]

    # anchor href equals target_url
    expected_href = f'<a href="{target_url}">'
    assert expected_href in body_content, "Body must contain an <a> element with href equal to target_url"

    # anchor has non-empty link text
    anchor_start = body_content.find(expected_href)
    anchor_text_start = anchor_start + len(expected_href)
    anchor_end = body_content.find("</a>", anchor_text_start)
    link_text = body_content[anchor_text_start:anchor_end].strip()
    assert len(link_text) > 0, "Anchor element must contain non-empty link text"
