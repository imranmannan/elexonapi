#!/usr/bin/env sh
set -euo pipefail

# create_release.sh <tag>
# Example: ./scripts/create_release.sh v0.1.1

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <tag> (e.g., v0.1.1)" >&2
  exit 2
fi

TAG="$1"
VERSION="${TAG#v}"

# Check for gh
if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh (GitHub CLI) not found. Install and authenticate it first: https://cli.github.com/" >&2
  exit 3
fi

# Ensure tag exists
if ! git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Error: tag $TAG not found locally. Create and push it first." >&2
  exit 4
fi

CHANGELOG="CHANGELOG.md"
if [ ! -f "$CHANGELOG" ]; then
  echo "Error: $CHANGELOG not found in repo root." >&2
  exit 5
fi

NOTES_FILE="release-notes-${VERSION}.md"
awk -v ver="$VERSION" '
  /^## \[/{
    if ($0 ~ "^## \[" ver "\]") {found=1; next}
    if (found && $0 ~ /^## \[/) {exit}
  }
  found {print}
' "$CHANGELOG" > "$NOTES_FILE"

if [ ! -s "$NOTES_FILE" ]; then
  echo "Warning: no changelog entry found for version $VERSION. Creating empty notes file." >&2
  printf "Release %s\n\nNo changelog entry found." "$VERSION" > "$NOTES_FILE"
fi

# Build distributions
echo "Building distributions..."
python -m pip install --upgrade build twine
python -m build

# Create release and upload artifacts (if any)
ARTIFACTS="dist/*"

echo "Creating GitHub release $TAG..."
# gh will create the release and upload provided artifacts
gh release create "$TAG" --title "elexonapi $TAG" --notes-file "$NOTES_FILE" $ARTIFACTS

RC=$?
if [ $RC -ne 0 ]; then
  echo "gh release create failed with exit code $RC" >&2
  exit $RC
fi

echo "Release $TAG created successfully. Notes written to $NOTES_FILE"