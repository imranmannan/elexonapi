# Releasing elexonapi

This document describes how to perform a manual release and how to set up
GitHub Actions to publish automatically.

## Manual release (Test PyPI recommended first)

1. Update the `version` in `pyproject.toml` (e.g., `0.1.1 -> 0.1.2`).
2. Add an entry to `CHANGELOG.md` under the new version with notable changes.
3. Commit the changes and push to the repository:

   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.1.2"
   git push origin main
   ```

4. Build distributions locally:

   ```bash
   python -m pip install --upgrade build twine
   python -m build
   python -m twine check dist/*
   ```

5. Upload to Test PyPI (optional, recommended):

   ```bash
   python -m twine upload --repository testpypi dist/* --repository-url https://test.pypi.org/legacy/ -u __token__ -p <TEST_PYPI_TOKEN>
   ```

6. After validating the package on TestPyPI, upload to production PyPI:

   ```bash
   python -m twine upload dist/* -u __token__ -p <PYPI_API_TOKEN>
   ```

7. Tag the release and push the tag:

   ```bash
   git tag v0.1.2
   git push origin v0.1.2
   ```

## Automating release with GitHub Actions

1. Create a project-scoped API token on PyPI:
   - https://pypi.org/manage/account/#api-tokens
   - Save token in GitHub as `PYPI_API_TOKEN` (Repository → Settings → Secrets → Actions).

2. Add a workflow that builds and publishes when a tag `v*.*.*` is pushed. See `.github/workflows/publish.yml`.

## Creating a GitHub Release from CHANGELOG (optional helper)

A convenience script is provided to create a GitHub Release from the `CHANGELOG.md` entry for a version tag and upload distribution artifacts.

Usage:

```bash
# ensure you have gh (GitHub CLI) installed and authenticated
# create a tag locally, push it to origin (if you haven't already):
# git tag v0.1.1 && git push origin v0.1.1

# then run:
./scripts/create_release.sh v0.1.1
```

The script will:
- extract the `## [0.1.1]` section from `CHANGELOG.md` into `release-notes-0.1.1.md`
- build source and wheel distributions (python -m build)
- create the GitHub Release and upload the `dist/*` artifacts

If `gh` is not installed you'll need to install and authenticate it first: https://cli.github.com/

## Notes
- Use `__token__` as the username when uploading with twine and provide the token as the password.
- Consider publishing to TestPyPI first to validate distribution behaviour.
