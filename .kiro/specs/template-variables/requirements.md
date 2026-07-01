# Requirements Document

## Introduction

This feature extends the redirect generator to render the index/listing templates (`r.html.j2` and `d.html.j2`) with populated template variables. The generator will pass a `resources` list, a `datasources` list, and a `provider_version` string to these templates. The provider version is extracted by parsing the output of `terraform --version`.

## Glossary

* **Generator**: The Python CLI application (`src/generate/cli.py`) that orchestrates template rendering and file generation.
* **Resource_List**: The list of AWS Terraform resource type names returned by `tfschema resource list aws`.
* **Datasource_List**: The list of AWS Terraform data source type names returned by `tfschema data list aws`.
* **Provider_Version**: The semantic version string (e.g., `6.52.0`) of the `hashicorp/aws` Terraform provider, extracted from `terraform --version` output.
* **Resource_Entry**: An object with an `href` field (the Terraform Registry URL) and a `full_name` field (the original `aws_`-prefixed name).
* **Datasource_Entry**: An object with an `href` field (the Terraform Registry URL) and a `full_name` field (the original `aws_`-prefixed name).
* **Index_Template**: A Jinja2 template (`r.html.j2` or `d.html.j2`) that renders a listing page of all resources or data sources.

## Requirements

### Requirement 1: extract provider version

**User Story:** As a site maintainer, I want the generator to extract the AWS provider version from `terraform --version` output, so that the listing pages display the current provider version.

#### Acceptance criteria

1. WHEN the Generator executes `terraform --version` and the output contains a line matching the pattern `+ provider registry.terraform.io/hashicorp/aws v<version>`, THE Generator SHALL extract the `<version>` portion as a dot-separated numeric string (e.g., `6.52.0`) and store it as the Provider_Version.
2. WHEN the `terraform --version` command completes successfully, THE Generator SHALL use only the first matching line for `registry.terraform.io/hashicorp/aws` to determine the Provider_Version.
3. IF the `terraform` executable is not found on PATH, THEN THE Generator SHALL print an error message to stderr indicating the missing executable and exit with a non-zero status code.
4. IF the `terraform --version` output does not contain a line for `registry.terraform.io/hashicorp/aws`, THEN THE Generator SHALL print an error message to stderr indicating the missing provider and exit with a non-zero status code.
5. IF the `terraform --version` command exits with a non-zero status code, THEN THE Generator SHALL print an error message to stderr indicating the command failure and exit with a non-zero status code.
6. IF the `terraform --version` command does not complete within 30 seconds, THEN THE Generator SHALL terminate the process, print an error message to stderr indicating the timeout, and exit with a non-zero status code.

### Requirement 2: build resources variable

**User Story:** As a site maintainer, I want the generator to build a `resources` template variable containing all AWS resources with their registry URLs, so that `r.html.j2` can render a complete listing.

#### Acceptance criteria

1. THE Generator SHALL construct a list of Resource_Entry objects from the Resource_List, preserving the order in which entries appear in the Resource_List.
2. WHEN building each Resource_Entry, THE Generator SHALL set the `href` field to `https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/<stripped_name>`, where `<stripped_name>` is the resource name with the `aws_` prefix removed.
3. WHEN building each Resource_Entry, THE Generator SHALL set the `full_name` field to the original resource name including the `aws_` prefix.
4. IF a resource name produces an empty string after stripping `aws_`, THEN THE Generator SHALL skip that entry and not include it in the resources list.
5. IF a resource name does not start with the `aws_` prefix, THEN THE Generator SHALL include it in the resources list using the full name as the `stripped_name` portion of the `href` URL.

### Requirement 3: build datasources variable

**User Story:** As a site maintainer, I want the generator to build a `datasources` template variable containing all AWS data sources with their registry URLs, so that `d.html.j2` can render a complete listing.

#### Acceptance criteria

1. THE Generator SHALL construct a list of Datasource_Entry objects from the Datasource_List, preserving the order in which entries appear in the Datasource_List.
2. WHEN building each Datasource_Entry, THE Generator SHALL set the `href` field to `https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/<stripped_name>`, where `<stripped_name>` is the data source name with the `aws_` prefix removed.
3. WHEN building each Datasource_Entry, THE Generator SHALL set the `full_name` field to the original data source name including the `aws_` prefix.
4. IF a data source name produces an empty string after stripping `aws_`, THEN THE Generator SHALL skip that entry and not include it in the datasources list.
5. IF a data source name does not start with the `aws_` prefix, THEN THE Generator SHALL include it in the datasources list using the full name as the `stripped_name` portion of the `href` URL.

### Requirement 4: render resources index template

**User Story:** As a site maintainer, I want the generator to render `r.html.j2` with the resources list and provider version, so that a complete resources listing page is generated.

#### Acceptance criteria

1. THE Generator SHALL render the `r.html.j2` template with the `resources` variable set to the list of Resource_Entry objects, the `provider_version` variable set to the Provider_Version string, and any additional variables required by the template (such as `target_url`, `original_name`, and `stripped_name`).
2. THE Generator SHALL write the rendered output to `docs/r/index.html` relative to the project root, creating the `docs/r/` directory if it does not already exist, using UTF-8 encoding.
3. IF the `r.html.j2` template is not found in the `src/generate/templates/` directory, THEN THE Generator SHALL print an error message to stderr and exit with a non-zero status code.
4. IF writing the output file fails due to a filesystem error, THEN THE Generator SHALL print an error message to stderr and exit with a non-zero status code.
5. IF the resources list is empty, THEN THE Generator SHALL still render the template and write the output file with an empty listing.

### Requirement 5: render datasources index template

**User Story:** As a site maintainer, I want the generator to render `d.html.j2` with the datasources list and provider version, so that a complete data sources listing page is generated.

#### Acceptance criteria

1. THE Generator SHALL render the `d.html.j2` template with the `datasources` variable set to the list of Datasource_Entry objects and the `provider_version` variable set to the Provider_Version string.
2. THE Generator SHALL create any missing parent directories and write the rendered output to `docs/d/index.html` relative to the project root, encoded as UTF-8.
3. IF the `d.html.j2` template is not found, THEN THE Generator SHALL print an error message to stderr and immediately halt execution with a non-zero status code without processing any remaining tasks.
4. IF the `d.html.j2` template is found but fails to render due to a syntax or variable error, THEN THE Generator SHALL print an error message indicating the rendering failure to stderr and immediately halt execution with a non-zero status code.
5. IF writing the output file fails due to a filesystem error, THEN THE Generator SHALL print an error message to stderr and immediately halt execution with a non-zero status code.

### Requirement 6: version parsing Round-Trip

**User Story:** As a developer, I want confidence that the version parsing logic correctly extracts versions from valid `terraform --version` output, so that regressions are caught early.

#### Acceptance criteria

1. WHEN the Generator's version parsing function receives a `terraform --version` output string containing a line matching the pattern `+ provider registry.terraform.io/hashicorp/aws v<major>.<minor>.<patch>` where major, minor, and patch are non-negative integers, THE Generator's version parsing function SHALL return a string equal to `<major>.<minor>.<patch>` with the `v` prefix removed.
2. IF the Generator's version parsing function receives a `terraform --version` output string that does not contain a line matching `+ provider registry.terraform.io/hashicorp/aws v<major>.<minor>.<patch>`, THEN THE Generator's version parsing function SHALL return None.
3. IF the `terraform --version` output string contains multiple lines matching the `hashicorp/aws` provider pattern, THEN THE Generator's version parsing function SHALL return the version from the first matching line.
