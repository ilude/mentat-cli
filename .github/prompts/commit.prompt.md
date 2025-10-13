# Commit workflow prompt

Note: GitHub prompt files are recognized when stored as YAML with the extension `.prompt.yml` or `.prompt.yaml`. See: https://docs.github.com/en/github-models/use-github-models/storing-prompts-in-github-repositories

This Markdown file documents the intent and usage. The actual runnable prompt file is `commit.prompt.yaml` in the same folder.

## Purpose
Run the pre-commit workflow locally, then create a Conventional Commits message and commit:

1) Run:
   - `make lint`
   - `make test`
2) If anything fails, fix the issues minimally and rerun the checks until both pass.
3) Stage changes: `git add -A`
4) Create a Conventional Commits message (e.g., `feat: ...`, `fix: ...`, `chore: ...`).
5) Commit with `git commit -m "<message>"`.

## Parameters
- `scope` (optional) — additional scope in the commit subject
- `subject` (optional) — override the generated subject
- `body` (optional) — extra commit body notes

## How to use in Copilot Chat
Reference the YAML prompt by name and pass optional variables:

```text
/commit-workflow scope="cli" subject="wire ruff/mypy" body="- update pyproject\n- fix B008 and E501"
```

If your client doesn’t support direct prompt invocation, open the YAML file and ask Copilot to run the described workflow.