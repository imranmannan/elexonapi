# Changelog

All notable changes to this project will be documented in this file.

## [0.1.4] - 2026-01-13

### Fixed
- cleaned up README and corrected examples
- changed CI / publish workflows to use uv
- changed linting from flake8 and black to ruff
- changed dev packages to be contained in .toml and not requirements-dev.txt
- added *.ipynb to .gitignore for ipynb test files

## [0.1.3] - 2026-01-11 [versions 0.1.1 and 0.1.2 were non-public]
### Fixed
- Fix: Corrected output determination from the API specification — the client now correctly maps outputs to the spec-defined types and determines output behaviour.

## [0.1.0] - 2026-01-11
### Initial Release
- Initial work: registry builder, datasets, download utilities.
- Prepare project for PyPI publishing (src layout, packaging metadata).
- Added `ElexonClient` class, tests, and CI workflow for testing.
- Added README, changelog, and release instructions.
- Automatically create a GitHub Release from the publish workflow and attach distribution artifacts.
- Added a local `scripts/create_release.sh` helper to create releases from `CHANGELOG.md`.
- Minor README and release documentation improvements.