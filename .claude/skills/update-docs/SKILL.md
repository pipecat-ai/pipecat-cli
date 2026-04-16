---
name: update-docs
description: Update CLI documentation pages to match source code changes
---

Update documentation pages in the pipecat-ai/docs repository to reflect source code changes in pipecat-cli. Analyzes the diff, maps changed source files to their corresponding doc pages, and makes targeted edits.

## Instructions

### Step 1: Detect changed source files

Identify changed files from the PR diff. Filter to files that could affect documentation:

- `src/pipecat_cli/commands/**` (CLI command definitions)
- `src/pipecat_cli/registry/service_metadata.py` (service definitions)
- `src/pipecat_cli/prompts/**` (interactive prompt flow)
- `src/pipecat_cli/generators/**` (project generation logic)
- `src/pipecat_cli/templates/**` (Jinja2 project templates)
- `src/pipecat_cli/config_validator.py` (non-interactive config validation)
- `src/pipecat_cli/main.py` (top-level CLI app and global options)

Ignore files on the skip list: `__init__.py`, `registry/_configs.py`, `registry/_imports.py`, `registry/service_loader.py`.

### Step 2: Map source files to doc pages

Read the mapping file at `.claude/skills/update-docs/SOURCE_DOC_MAPPING.md`. Use the direct mapping table to find which doc page each changed source file corresponds to.

### Step 3: Analyze each source-doc pair

For each mapped pair:

1. **Read the diff** for the source file
2. **Read the current doc page** in full

Identify what changed by category:

- **CLI flags/options added or removed** (from `commands/init.py` or `main.py`): Look for new `typer.Option()` calls, removed parameters, changed defaults or help text
- **Service options changed** (from `service_metadata.py`): New services added, services removed, renamed enum values, new categories, changed pip extras
- **Interactive flow changes** (from `prompts/questions.py`): New prompts added, prompts removed, changed prompt text or choices
- **Config validation changes** (from `config_validator.py`): New validation rules, changed error messages, new accepted config keys
- **Generated project structure changes** (from `generators/project.py` or `templates/`): New files generated, changed file contents, new template variables

### Step 4: Make targeted edits

For each doc page that needs updates, edit **only the sections that need changes**. Preserve all other content exactly as-is.

#### Section-specific guidance

**Options** (`<ParamField>` entries):
- Add new CLI flags with correct types, defaults, and descriptions
- Remove flags that no longer exist in source
- Update types, defaults, or descriptions that changed

**Examples** (CLI usage examples):
- Update command examples if flag names or valid values changed
- Don't rewrite working examples just to add new optional flags

**"Discover Available Options" JSON**:
- If `service_metadata.py` changed (services added/removed/renamed), update the sample `--list-options` JSON output to reflect the current service list

**"Generated Project Structure"** (file tree diagram):
- If templates or `generators/project.py` changed the set of generated files, update the tree diagram

**Interactive Setup** (bullet list of prompts):
- If `prompts/questions.py` changed the prompt flow, update the bullet list describing the interactive setup steps

**Non-interactive / Config file sections**:
- If `config_validator.py` or `commands/init.py` changed accepted config keys or flag names, update the config file example and flag reference

### Step 5: Update guides

After completing reference doc edits, check if any guides need updates.

For each changed source file, collect changed flag names, service names, and config keys from the diff. Search the guides directory:
```bash
grep -rl "flag_name\|service_name" DOCS_PATH/guides/
```

For each guide that references changed CLI content:
1. Read the full guide
2. Update flag names, service values, command examples, and config snippets that are now incorrect
3. Don't rewrite prose -- only fix the specific references that changed
4. Leave guides alone if they reference the CLI generally but don't use any changed values

### Step 6: Output summary

After all edits are complete, print a summary:

```
## Documentation Updates

### Updated reference pages
- `api-reference/cli/init.mdx` -- Updated Options (added `--new-flag`), updated service list in examples

### Updated guides
- `guides/features/some-guide.mdx` -- Updated CLI example (renamed `--old-flag` to `--new-flag`)

### Skipped files
- `src/pipecat_cli/registry/_configs.py` -- auto-generated
```

## Guidelines

- **Be conservative** -- only change what the diff warrants. Don't "improve" docs beyond what changed in source.
- **Read before editing** -- always read the full doc page before making changes so you understand the existing structure.
- **Preserve voice** -- match the writing style of the existing doc page, don't impose a different tone.
- **Parallel analysis** -- when multiple source files map to the same doc page, collect all changes before editing to avoid multiple passes.

## Checklist

Before finishing, verify:

- [ ] All changed source files were checked against the mapping table
- [ ] Each doc page edit matches the actual source code change (not guessed)
- [ ] No content was removed unless the corresponding source was removed
- [ ] New flags/options have accurate types and defaults from source
- [ ] Formatting matches the existing page style
- [ ] Guides referencing changed CLI content were checked and updated
