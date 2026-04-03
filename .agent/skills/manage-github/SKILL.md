---
name: manage-github
description: Uses the GitHub MCP server to manage the arxiv_assistant repository — create issues, open pull requests, check CI status, review code, and manage branches. Use when the user asks about GitHub issues, PRs, CI/CD, or repository management.
---

# Manage GitHub Repository

Use the **github** MCP tool to interact with the arxiv_assistant GitHub repository directly.

## Common Operations

### Issues

**Create an issue** when:
- A bug is discovered during development
- A feature idea comes up during a session
- A TODO is found that should be tracked rather than left as a comment

Issue format:
- Title: Short, actionable description
- Body: Steps to reproduce (for bugs), acceptance criteria (for features)
- Labels: `bug`, `feature`, `enhancement`, `chore`, `documentation`

**Search issues** before creating duplicates. Check if the bug or feature has already been reported.

### Pull Requests

**Create a PR** when:
- A feature branch is ready for review
- A bug fix is complete and tested

PR format:
- Title: Conventional commit style (`feat: add citation export`, `fix: worker timeout`)
- Body: Summary of changes, test plan, screenshots if UI changes
- Base branch: `main`

**Check PR status** to see if CI passes before merging.

### Branches

Branch naming convention for arxiv_assistant:
- `feat/<short-description>` — new features
- `fix/<short-description>` — bug fixes
- `refactor/<short-description>` — code reorganization
- `chore/<short-description>` — maintenance tasks

### CI Status

Check if the latest commit passes CI before:
- Deploying to Khadas production (`./deploy.sh`)
- Merging a PR
- Tagging a release

### Code Review

Use GitHub MCP to:
- List files changed in a PR
- Check diff sizes (PRs should be reviewable in under 10 minutes)
- Look for common issues: missing tests, hardcoded values, API key exposure

## Workflow Integration

This skill works well in combination with:
- `/verify` workflow — run quality gates before creating a PR
- `/deploy` workflow — check CI status before deploying
- `inspect-database` skill — verify data state when closing bug issues

## Guidelines

- Never force-push to `main` via the GitHub API.
- Always check if a branch exists before creating one with the same name.
- When creating issues for bugs found during development, include the file path and line number.
- Link related issues and PRs using `Fixes #123` or `Related to #456` in PR descriptions.
