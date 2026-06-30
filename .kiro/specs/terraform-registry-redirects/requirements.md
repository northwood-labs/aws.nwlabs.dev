# Requirements Document

## Introduction

This feature generates URL redirect HTML files for Terraform AWS provider resources and data sources. The CLI tool reads lists of resources and data sources from `tfschema`, then generates static HTML redirect pages in the `docs/` directory. Each redirect page forwards visitors to the corresponding Terraform Registry documentation page, providing short, memorable URLs for AWS provider docs.

## Glossary

* **Generator**: The Python CLI application invoked via `uv run generate` that produces redirect HTML files.
* **Resource_List**: A newline-delimited list of Terraform AWS provider resource type names, produced by `tfschema resource list aws`.
* **Data_Source_List**: A newline-delimited list of Terraform AWS provider data source type names, produced by `tfschema data list aws`.
* **Redirect_File**: A static HTML file that uses an HTTP-equiv meta refresh tag to redirect the browser to an external URL.
* **Output_Directory**: The `docs/` directory at the project root, mapped to the `/` relative URL path when served.
* **Resource_Name**: A Terraform AWS provider resource type name with the `aws_` prefix stripped (e.g., `aws_instance` becomes `instance`).
* **Data_Source_Name**: A Terraform AWS provider data source type name with the `aws_` prefix stripped (e.g., `aws_ami` becomes `ami`).
* **Registry_Base_URL**: The base URL `https://registry.terraform.io/providers/hashicorp/aws/latest/docs`.

## Requirements

### Requirement 1: read resource list from tfschema

**User Story:** As a developer, I want the Generator to read the list of AWS provider resources from `tfschema`, so that redirect files can be generated for every known resource.

#### Acceptance criteria

1. WHEN invoked, THE Generator SHALL execute `tfschema resource list aws` and capture its standard output.
2. WHEN the command output is captured, THE Generator SHALL parse the output as a newline-delimited list, stripping leading and trailing whitespace from each line and treating each resulting non-empty line as a resource type name.
3. IF `tfschema resource list aws` returns a non-zero exit code or the command cannot be found on the system PATH, THEN THE Generator SHALL report an error message indicating the failure to standard error and exit with a non-zero status.
4. IF `tfschema resource list aws` does not complete within 30 seconds, THEN THE Generator SHALL terminate the command, report a timeout error to standard error, and exit with a non-zero status.
5. IF `tfschema resource list aws` succeeds but produces no resource type names after parsing, THEN THE Generator SHALL report a warning to standard error and exit with a non-zero status.

### Requirement 2: read data source list from tfschema

**User Story:** As a developer, I want the Generator to read the list of AWS provider data sources from `tfschema`, so that redirect files can be generated for every known data source.

#### Acceptance criteria

1. WHEN invoked, THE Generator SHALL execute `tfschema data list aws` and capture its standard output.
2. WHEN the command output is captured, THE Generator SHALL parse the output as a newline-delimited list, stripping leading and trailing whitespace from each line and treating lines that are empty or contain only whitespace as non-entries to be discarded.
3. IF `tfschema data list aws` returns a non-zero exit code, THEN THE Generator SHALL treat the command as a complete failure, ignore any output that may have been produced, print an error message to standard error that includes the command name and the exit code, and exit immediately with a non-zero status.
4. IF the `tfschema` executable is not found on the system PATH, THEN THE Generator SHALL print an error message to standard error indicating the missing executable and exit with a non-zero status.
5. IF `tfschema data list aws` succeeds but produces no parseable data source type names, THEN THE Generator SHALL print a warning to standard error and continue execution with an empty data source list.

### Requirement 3: strip AWS prefix from type names

**User Story:** As a developer, I want the `aws_` prefix removed from type names, so that the generated URL paths are concise and readable.

#### Acceptance criteria

1. WHEN processing a resource type name, THE Generator SHALL perform a case-sensitive match and strip the leading `aws_` prefix to produce the Resource_Name used in the URL path.
2. WHEN processing a data source type name, THE Generator SHALL perform a case-sensitive match and strip the leading `aws_` prefix to produce the Data_Source_Name used in the URL path.
3. IF a type name does not start with `aws_`, THEN THE Generator SHALL use the full type name as-is for the URL path.
4. IF stripping the `aws_` prefix would produce an empty string, THEN THE Generator SHALL skip that entry and log a warning to standard error; IF the warning cannot be written to standard error, THEN THE Generator SHALL treat this as a system error and exit with a non-zero status.

### Requirement 4: generate resource redirect files

**User Story:** As a developer, I want redirect files generated for each resource, so that visiting `/r/<resource>` redirects to the Terraform Registry resource documentation.

#### Acceptance criteria

1. WHEN generating redirect files, THE Generator SHALL create a Redirect_File at the path `docs/r/<Resource_Name>/index.html` for each entry in the Resource_List, creating parent directories as needed.
2. THE Redirect_File SHALL contain a valid HTML5 document with a `<meta http-equiv="refresh" content="0;URL='<target_url>'">` element redirecting to `https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/<Resource_Name>`.
3. THE Redirect_File SHALL include a `<link rel="canonical" href="<target_url>">` element in the `<head>` section, where `<target_url>` is `https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/<Resource_Name>`.
4. IF a Redirect_File cannot be written due to a filesystem error, THEN THE Generator SHALL report the error to standard error and exit with a non-zero status, even if some redirect files were successfully created prior to the failure.

### Requirement 5: generate data source redirect files

**User Story:** As a developer, I want redirect files generated for each data source, so that visiting `/d/<data-source>` redirects to the Terraform Registry data source documentation.

#### Acceptance criteria

1. FOR EACH Data_Source_Name, THE Generator SHALL create any intermediate directories and a Redirect_File at the path `docs/d/<Data_Source_Name>/index.html`.
2. THE Redirect_File SHALL contain a valid HTML5 document with a `<meta http-equiv="refresh">` tag redirecting to `https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/<Data_Source_Name>`.
3. THE Redirect_File SHALL include a `<link rel="canonical">` element with an `href` attribute set to `https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/<Data_Source_Name>`.
4. IF writing a Redirect_File fails due to a filesystem error, THEN THE Generator SHALL report the error to standard error and exit with a non-zero status.

### Requirement 6: redirect HTML structure

**User Story:** As a developer, I want the generated HTML to follow a consistent structure, so that redirects work across all browsers and are SEO-friendly.

#### Acceptance criteria

1. THE Redirect_File SHALL declare `<!DOCTYPE html>` and use the `lang="en"` attribute on the `<html>` element.
2. THE Redirect_File SHALL include a `<meta charset="UTF-8">` element within the `<head>` element.
3. THE Redirect_File SHALL include a `<meta http-equiv="refresh" content="0;URL='<target_url>'">` element within the `<head>` element with a delay of zero seconds.
4. THE Redirect_File SHALL include a `<body>` containing a hyperlink (`<a>` element) to the target URL with non-empty text content that includes the target URL, serving as a fallback for browsers that do not support meta refresh.
5. THE Redirect_File SHALL include a `<title>` element within the `<head>` element containing non-empty text.

### Requirement 7: clean output directories before generation

**User Story:** As a developer, I want the `docs/r/` and `docs/d/` directories cleaned before generating new files, so that stale redirects for removed resources do not persist.

#### Acceptance criteria

1. WHEN the Generator begins execution and before writing any new Redirect_Files, THE Generator SHALL remove all existing files and subdirectories within `docs/r/`.
2. WHEN the Generator begins execution and before writing any new Redirect_Files, THE Generator SHALL remove all existing files and subdirectories within `docs/d/`.
3. THE Generator SHALL preserve all other files in the `docs/` directory (e.g., `docs/404.html`, `docs/.nojekyll`, `docs/CNAME`).
4. IF either `docs/r/` or `docs/d/` does not exist at the time of cleaning, THEN THE Generator SHALL proceed without error for the missing directory independently of whether the other directory exists.
5. IF removal of `docs/r/` or `docs/d/` fails due to a filesystem error, THEN THE Generator SHALL report the error to standard error and exit with a non-zero status.

### Requirement 8: CLI invocation via uv

**User Story:** As a developer, I want to run the generator with `uv run generate`, so that the tool integrates with the project's existing package management workflow.

#### Acceptance criteria

1. THE Generator SHALL be executable via `uv run generate` from the project root.
2. WHEN execution completes successfully, THE Generator SHALL exit with status code zero.
3. WHEN execution completes successfully, THE Generator SHALL print a summary line to standard output containing the number of resource redirects generated and the number of data source redirects generated as separate numeric values.
4. IF execution fails due to an error, THEN THE Generator SHALL exit with a non-zero status code.

### Requirement 9: template-based HTML generation

**User Story:** As a developer, I want redirect files generated using Jinja2 templates, so that the HTML structure is maintainable and consistent.

#### Acceptance criteria

1. THE Generator SHALL load Jinja2 templates from a `templates/` directory relative to the Generator package source root.
2. THE Generator SHALL pass the target URL, the original type name (e.g., `aws_instance`), and the stripped name (e.g., `instance`) as template variables when rendering a Redirect_File.
3. WHEN the template is rendered, THE Generator SHALL produce an HTML5 document conforming to the structure defined in Requirement 6.
4. IF the Jinja2 template fails to load or render, THEN THE Generator SHALL report an error message indicating the failure reason to standard error and exit with a non-zero status.
