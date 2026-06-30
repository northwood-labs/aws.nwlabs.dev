# Implementation Plan: Terraform Registry Redirects

## Overview

Implement a Python CLI tool that generates static HTML redirect pages for Terraform AWS provider resources and data sources. The tool executes `tfschema` to discover type names, strips the `aws_` prefix, cleans output directories, renders Jinja2 templates, and writes redirect files to `docs/r/` and `docs/d/`.

## Tasks

* [x] 1. Set up project structure and Jinja2 template
  * [x] 1.1 Create the redirect HTML template
    * Create `src/generate/templates/redirect.html.j2` with a valid HTML5 document
    * Include `<!DOCTYPE html>`, `<html lang="en">`, `<meta charset="UTF-8">`
    * Include `<meta http-equiv="refresh" content="0;URL='{{ target_url }}'">` in `<head>`
    * Include `<link rel="canonical" href="{{ target_url }}">` in `<head>`
    * Include a `<title>` element with non-empty text
    * Include a `<body>` with an `<a href="{{ target_url }}">` fallback link with non-empty text
    * Template variables: `target_url`, `original_name`, `stripped_name`
    * _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2, 9.3_

  * [x] 1.2 Add dev dependencies for testing
    * Run `uv add --dev hypothesis pytest`
    * _Requirements: (testing infrastructure)_

* [x] 2. Implement helper functions in `src/generate/cli.py`
  * [x] 2.1 Implement `run_tfschema(args, timeout)` function
    * Execute `tfschema` with given args via `subprocess.run`, capture stdout
    * Parse output as newline-delimited list, strip whitespace, discard empty lines
    * Handle `FileNotFoundError` (missing executable), non-zero exit code, and `TimeoutExpired`
    * Print error messages to stderr and raise `SystemExit` on failure
    * _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

  * [x] 2.2 Implement `strip_aws_prefix(name)` function
    * Case-sensitive match and strip of leading `aws_` prefix
    * Return `None` if stripping would produce an empty string, log warning to stderr
    * Return the full name unchanged if it does not start with `aws_`
    * _Requirements: 3.1, 3.2, 3.3, 3.4_

  * [x] 2.3 Implement `build_target_url(stripped_name, category)` function
    * Construct URL: `https://registry.terraform.io/providers/hashicorp/aws/latest/docs/{category}/{stripped_name}`
    * Category is either `"resources"` or `"data-sources"`
    * _Requirements: 4.2, 5.2_

  * [x] 2.4 Implement `clean_output_dirs(base)` function
    * Remove all contents of `docs/r/` and `docs/d/` under the given base path
    * Preserve other files in `docs/` (e.g., `404.html`, `.nojekyll`, `CNAME`)
    * Silently skip directories that do not exist
    * Raise `SystemExit` on filesystem errors
    * _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  * [x] 2.5 Implement `generate_redirects(names, category, template, base)` function
    * For each stripped name, create parent directories and write `index.html`
    * Resource paths: `docs/r/{name}/index.html`
    * Data source paths: `docs/d/{name}/index.html`
    * Render template with `target_url`, `original_name`, `stripped_name`
    * Return count of files written
    * Raise `SystemExit` on filesystem write errors
    * _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 9.2, 9.3_

  * [x] 2.6 Write property tests for helper functions
    * **Property 1: Line parsing preserves non-empty content and strips whitespace**
    * **Property 2: Prefix stripping correctness**
    * **Property 3: URL construction follows registry pattern**
    * **Property 5: File path construction**
    * **Validates: Requirements 1.2, 2.2, 3.1, 3.2, 3.3, 4.1, 4.2, 5.1, 5.2**

* [x] 3. Implement `main()` orchestration
  * [x] 3.1 Implement `main()` function pipeline
    * Call `run_tfschema(["resource", "list", "aws"])` and validate non-empty result (exit non-zero if empty)
    * Call `run_tfschema(["data", "list", "aws"])` and allow empty result with warning
    * Strip `aws_` prefix from all names, skipping invalid entries
    * Call `clean_output_dirs` to remove stale redirects
    * Load Jinja2 template from `src/generate/templates/redirect.html.j2`
    * Call `generate_redirects` for resources (category `"resources"`, path prefix `r`)
    * Call `generate_redirects` for data sources (category `"data-sources"`, path prefix `d`)
    * Print summary line with resource and data source counts to stdout
    * Return 0 on success
    * _Requirements: 1.5, 2.5, 8.1, 8.2, 8.3, 8.4, 9.1, 9.4_

  * [x] 3.2 Register CLI entry point in `pyproject.toml`
    * Add `[project.scripts]` section with `generate = "generate.cli:main"` entry
    * Verify `uv run generate` resolves the entry point
    * _Requirements: 8.1_

* [x] 4. Checkpoint
  * Ensure all tests pass, ask the user if questions arise.

* [x] 5. Write tests
  * [x] 5.1 Write property test for template rendering
    * **Property 4: Template rendering produces complete HTML structure**
    * **Validates: Requirements 4.2, 4.3, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 9.2, 9.3**

  * [x] 5.2 Write property test for summary output
    * **Property 6: Summary line contains correct counts**
    * **Validates: Requirements 8.3**

  * [x] 5.3 Write unit tests for error handling
    * Mock `subprocess.run` to simulate non-zero exit codes, `FileNotFoundError`, `TimeoutExpired`
    * Test empty resource list produces non-zero exit
    * Test empty data source list produces warning but continues
    * Test filesystem errors during clean and write operations
    * Test template load failures
    * _Requirements: 1.3, 1.4, 1.5, 2.3, 2.4, 2.5, 4.4, 5.4, 7.5, 9.4_

  * [x] 5.4 Write integration test for end-to-end run
    * Mock `tfschema` output and verify file creation and content
    * Verify correct directory structure (`docs/r/`, `docs/d/`)
    * Verify redirect HTML content matches expected structure
    * _Requirements: 4.1, 5.1, 7.1, 7.2, 7.3, 8.2, 8.3_

* [x] 6. Final checkpoint
  * Ensure all tests pass, ask the user if questions arise.

## Notes

* Tasks marked with `*` are optional and can be skipped for faster MVP
* Each task references specific requirements for traceability
* Checkpoints ensure incremental validation
* Property tests validate universal correctness properties from the design document
* Unit tests validate specific examples and edge cases
* The project uses `uv` as the package manager and `hypothesis` + `pytest` for testing

## Task dependency graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4"] },
    { "id": 2, "tasks": ["2.5", "2.6"] },
    { "id": 3, "tasks": ["3.1", "3.2"] },
    { "id": 4, "tasks": ["5.1", "5.2", "5.3", "5.4"] }
  ]
}
```
