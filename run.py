import os
from pathlib import Path

from github import Auth, Github
from github.ContentFile import ContentFileSearchResult
from github.Organization import Organization
from github.PaginatedList import PaginatedList
from jinja2 import Template

REDIRECT_TEMPLATE = Template(
    """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="go-import" content="go.nwlabs.dev/{{ repo }} git https://github.com/northwood-labs/{{ repo }}">
    <meta http-equiv="refresh" content="0;URL='https://github.com/northwood-labs/{{ repo }}'">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ repo }}</title>
</head>
<body>
    <h1>{{ repo }}</h1>
    <p>Redirecting you to the <a href="https://github.com/northwood-labs/{{ repo }}">northwood-labs/{{ repo }}</a> project page...</p>
</body>
</html>
"""
)

REDIRECT_TEMPLATE_GOMOD = Template(
    """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="go-import" content="go.nwlabs.dev/{{ repo }}/{{ path }} git https://github.com/northwood-labs/{{ repo }} {{ path }}">
    <meta http-equiv="refresh" content="0;URL='https://github.com/northwood-labs/{{ repo }}/tree/main/{{ path }}'">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ repo }}/{{ path }}</title>
</head>
<body>
    <h1>{{ repo }}/{{ path }}</h1>
    <p>Redirecting you to the <a href="https://github.com/northwood-labs/{{ repo }}/tree/main/{{ path }}">northwood-labs/{{ repo }}/{{ path }}</a> project page...</p>
</body>
</html>
"""
)


def main() -> None:
    github_token: str = os.environ["GITHUB_TOKEN"]

    with Github(auth=Auth.Token(github_token)) as g:
        org: Organization = g.get_organization("northwood-labs")

        # Filtered to remove private repos and sorted alphabetically.
        list_of_repos: list[str] = sorted(
            repo.name for repo in org.get_repos() if not repo.private and not repo.name.startswith(".")
        )

        for repo in list_of_repos:
            out_dir: Path = Path("docs") / repo
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(REDIRECT_TEMPLATE.render(repo=repo))

        results: PaginatedList[ContentFileSearchResult] = g.search_code("filename:go.mod user:northwood-labs")

        list_of_gomods: list[str] = sorted(
            f"{item.repository.name}/{item.path}"
            for item in results
            if not item.repository.private and not item.repository.name.startswith(".") and item.path != "go.mod"
        )

        list_of_gomods = [path.removesuffix("/go.mod") for path in list_of_gomods]

        # for gomod_path in list_of_gomods:
        #     repo, path = gomod_path.split("/", 1)
        #     parts: list[str] = path.split("/")
        #
        #     for index in range(1, len(parts) + 1):
        #         path_prefix: str = "/".join(parts[:index])
        #         out_dir: Path = Path("docs") / repo / path_prefix
        #         out_dir.mkdir(parents=True, exist_ok=True)
        #         (out_dir / "index.html").write_text(
        #             REDIRECT_TEMPLATE_GOMOD.render(repo=repo, path=path_prefix)
        #         )

        for gomod_path in list_of_gomods:
            repo, path = gomod_path.split("/", 1)
            out_dir: Path = Path("docs") / repo / path
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(REDIRECT_TEMPLATE_GOMOD.render(repo=repo, path=path))


if __name__ == "__main__":
    main()
