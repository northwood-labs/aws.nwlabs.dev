# Implementation Plan: Template Variables

## Overview

Extend the redirect generator (`src/generate/cli.py`) to extract the AWS provider version from `terraform --version` output, build structured entry lists for resources and data sources, and render the `r.html.j2` and `d.html.j2` index templates with populated template variables.

## Tasks

* [x] 1. Implement version extraction functions
  * [x] 1.1 Add `run_terraform_version` and `parse_provider_version` functions to `src/generate/cli.py`
    * Implement `run_terraform_version(timeout: int = 30) -> str` following the same subprocess pattern as `run_tfschema` (handle `FileNotFoundError`, `TimeoutExpired`, non-zero exit)
    * Implement `parse_provider_version(output: str) -> str | None` as a pure function using regex `r"\+\s+provider\s+registry\.terraform\.io/hashicorp/aws\s+v(\d+\.\d+\.\d+)"` to extract the version string
    * Return the first match only, or `None` if no match found
    * _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.1, 6.2, 6.3_

  * [x] 1.2 Write property tests for version extraction
    * **Property 1: Version extraction round-trip**
    * **Property 2: Non-matching output returns None**
    * **Property 3: First match wins for multiple provider lines**
    * **Validates: Requirements 1.1, 1.2, 1.4, 6.1, 6.2, 6.3**

  * [x] 1.3 Write unit tests for `run_terraform_version` error handling
    * Test `FileNotFoundError` raises `SystemExit`
    * Test `TimeoutExpired` raises `SystemExit`
    * Test non-zero exit code raises `SystemExit`
    * _Requirements: 1.3, 1.5, 1.6_

* [x] 2. Implement entry list builder
  * [x] 2.1 Add `build_entry_list` function to `src/generate/cli.py`
    * Implement `build_entry_list(stripped_names: list[str], original_names: list[str], category: str) -> list[dict[str, str]]`
    * Each entry has `href` (from `build_target_url`) and `full_name` (original name)
    * Preserve input order
    * _Requirements: 2.1, 2.2, 2.3, 2.5, 3.1, 3.2, 3.3, 3.5_

  * [x] 2.2 Write property tests for entry list builder
    * **Property 4: Entry list preserves input order**
    * **Property 5: Entry fields are correctly constructed**
    * **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 3.1, 3.2, 3.3, 3.5**

* [x] 3. Implement index template rendering
  * [x] 3.1 Add `render_index_template` function to `src/generate/cli.py`
    * Implement `render_index_template(env: Environment, template_name: str, output_path: Path, context: dict[str, object]) -> None`
    * Load template by name from Jinja2 environment
    * Render with provided context and write to output path (UTF-8)
    * Create parent directories as needed
    * Handle `TemplateNotFound`, template render errors, and filesystem write errors with stderr messages and `sys.exit(1)`
    * _Requirements: 4.2, 4.3, 4.4, 5.2, 5.3, 5.4, 5.5_

  * [x] 3.2 Write unit tests for `render_index_template` error handling
    * Test template-not-found error
    * Test template render failure (syntax/variable error)
    * Test filesystem write failure
    * Test empty list still renders successfully
    * _Requirements: 4.3, 4.4, 4.5, 5.3, 5.4, 5.5_

* [x] 4. Checkpoint - Ensure all tests pass
  * Ensure all tests pass, ask the user if questions arise.

* [x] 5. Wire everything together in `main()`
  * [x] 5.1 Update `main()` in `src/generate/cli.py` to integrate the new functions
    * After fetching resources/data sources and stripping prefixes, call `run_terraform_version()` and `parse_provider_version()` — exit with error if version is `None`
    * Build entry lists using `build_entry_list` for both resources and data sources
    * Load `r.html.j2` and `d.html.j2` templates from the Jinja2 environment
    * Render `r.html.j2` to `docs/r/index.html` with context: `resources`, `provider_version`, `target_url`, `original_name`, `stripped_name`
    * Render `d.html.j2` to `docs/d/index.html` with context: `datasources`, `provider_version`, `target_url`, `original_name`, `stripped_name`
    * Update summary print to include index page generation
    * _Requirements: 1.1, 1.4, 2.1, 2.4, 3.1, 3.4, 4.1, 4.2, 4.5, 5.1, 5.2_

  * [x] 5.2 Write integration tests for the full pipeline with index templates
    * Mock both `run_tfschema` and `run_terraform_version` outputs
    * Verify `docs/r/index.html` and `docs/d/index.html` are created
    * Verify rendered HTML contains the provider version string
    * Verify rendered HTML contains resource/datasource entries with correct `href` values
    * Verify individual redirect files are still generated correctly
    * _Requirements: 4.1, 4.2, 4.5, 5.1, 5.2_

* [x] 6. Final checkpoint - Ensure all tests pass
  * Ensure all tests pass, ask the user if questions arise.

## Notes

* Tasks marked with `*` are optional and can be skipped for faster MVP
* Each task references specific requirements for traceability
* Checkpoints ensure incremental validation
* Property tests validate universal correctness properties from the design document
* Unit tests validate specific examples and edge cases
* The implementation language is Python, matching the existing codebase

## Task dependency graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.2", "3.1"] },
    { "id": 2, "tasks": ["3.2"] },
    { "id": 3, "tasks": ["5.1"] },
    { "id": 4, "tasks": ["5.2"] }
  ]
}
```
