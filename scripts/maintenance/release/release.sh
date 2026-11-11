#!/usr/bin/env bash
#
# Prepare a release of cosmicjellyfish: changelog commit + annotated git tag.
#
# WHAT THIS SCRIPT DOES
#   1. Reads the version from cosmicjellyfish/version.py (you bump it yourself first).
#   2. Refuses to continue unless the repository is in a safe state (see checks below).
#   3. Turns the "## Unreleased" section of CHANGELOG.md into a dated "## [vX.Y.Z]" section
#      (scripts/maintenance/release/prepare_changelog.py) and commits ONLY CHANGELOG.md.
#   4. Creates the annotated tag vX.Y.Z on that commit.
#   5. Prints the two push commands. IT NEVER PUSHES: you do that, on purpose.
#
# WHAT HAPPENS WHEN YOU PUSH THE TAG (.github/workflows/main.yml)
#   * tag contains "rc"  (e.g. v2.0.0rc1) -> published to TestPyPI, GitHub pre-release.
#   * any other tag      (e.g. v2.0.0)    -> published to PyPI after the reviewers of the
#                                            "pypi" GitHub environment approve it.
#   The workflow fails on purpose if the tag is not "v" + VERSION from version.py.
#   A PyPI/TestPyPI version can never be re-uploaded: if a release is broken, bump the
#   version (e.g. rc1 -> rc2, 2.0.0 -> 2.0.1) instead of re-tagging.
#
# HOW TO RELEASE
#   1. Merge everything you want to ship into main (through a pull request).
#   2. git checkout main && git pull
#   3. Edit _MAJOR/_MINOR/_PATCH/_SUFFIX in cosmicjellyfish/version.py and the
#      "version:" line in CITATION.cff (CI checks they agree). Final releases use an
#      empty _SUFFIX; release candidates use e.g. "rc1".
#   4. Commit that bump (it must be committed: the working tree has to be clean).
#   5. Run this script:   scripts/maintenance/release/release.sh
#      Use --dry-run to run all the checks and see what would happen without changing
#      anything.
#   6. Push as printed at the end. If main is protected and does not accept direct
#      pushes, open a pull request for the changelog commit first and tag the merged
#      commit instead (git tag -a vX.Y.Z -m vX.Y.Z <merge-commit>).
#
# Environment: PYTHON overrides the interpreter used for prepare_changelog.py
# (default: python; for example PYTHON="uv run python").

set -euo pipefail

RELEASE_BRANCH="main"
REMOTE="origin"
# Split into an array so that multi-word commands such as "uv run python" work.
read -r -a PYTHON <<< "${PYTHON:-python}"
DRY_RUN=0

for arg in "$@"; do
    case "$arg" in
        -n|--dry-run) DRY_RUN=1 ;;
        -h|--help)
            sed -n '2,/^set -euo/p' "${BASH_SOURCE[0]}" | sed '$d' | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Error, unknown argument: $arg (use --dry-run or --help)" >&2
            exit 2
            ;;
    esac
done

fail() {
    echo "Error, $*" >&2
    exit 1
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

# --- Safety checks: nothing is modified until all of them pass -------------------------

[[ "$(git rev-parse --abbrev-ref HEAD)" == "${RELEASE_BRANCH}" ]] \
    || fail "releases are made from '${RELEASE_BRANCH}', but you are on '$(git rev-parse --abbrev-ref HEAD)'."

[[ -z "$(git status --porcelain)" ]] \
    || fail "the working tree is not clean. Commit or stash your changes first (including the version bump)."

git fetch --quiet "${REMOTE}" "${RELEASE_BRANCH}" --tags
[[ "$(git rev-parse HEAD)" == "$(git rev-parse "${REMOTE}/${RELEASE_BRANCH}")" ]] \
    || fail "local '${RELEASE_BRANCH}' differs from '${REMOTE}/${RELEASE_BRANCH}'. Run 'git pull' (or push your commits) first."

# Read the version without importing the package (no dependencies needed).
VERSION="$("${PYTHON[@]}" -c 'import runpy; print(runpy.run_path("cosmicjellyfish/version.py")["VERSION"])')"
[[ -n "${VERSION}" ]] || fail "could not read VERSION from cosmicjellyfish/version.py."
TAG="v${VERSION}"

# version.py and CITATION.cff must agree (the same check that CI runs).
"${PYTHON[@]}" scripts/maintenance/release/check_version_consistency.py

if git rev-parse --quiet --verify "refs/tags/${TAG}" >/dev/null; then
    fail "tag ${TAG} already exists locally or on ${REMOTE}. Bump the version in version.py instead of re-using a tag."
fi

if [[ "${TAG}" == *rc* ]]; then
    TARGET="TestPyPI (pre-release)"
else
    TARGET="PyPI (needs approval by the 'pypi' environment reviewers)"
fi

echo "Release ${TAG} from ${RELEASE_BRANCH} at $(git rev-parse --short HEAD)"
echo "Pushing the tag will publish to: ${TARGET}"

if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "Dry run: all checks passed, nothing was changed."
    exit 0
fi

read -r -p "Create the changelog commit and tag ${TAG} locally? [y/N] " answer
[[ "${answer}" =~ ^([yY]|[yY][eE][sS])$ ]] || { echo "Cancelled."; exit 1; }

# --- Changes (all local) ---------------------------------------------------------------

# Moves the notes under "## Unreleased" into a dated "## [vX.Y.Z]" heading, the format that
# release_notes.py needs to build the GitHub release text. Does nothing if it already exists.
"${PYTHON[@]}" scripts/maintenance/release/prepare_changelog.py

grep -q "^## \[${TAG}\]" CHANGELOG.md \
    || fail "CHANGELOG.md has no '## [${TAG}]' section after prepare_changelog.py."

if ! git diff --quiet -- CHANGELOG.md; then
    git add CHANGELOG.md   # only the changelog, never 'git add -A'
    git commit -m "Prepare changelog for ${TAG}"
fi

git tag -a "${TAG}" -m "${TAG}"

echo
echo "Done. Nothing has been pushed. Review with: git log --oneline -3 && git show ${TAG} --stat"
echo "When you are happy, publish with:"
echo "    git push ${REMOTE} ${RELEASE_BRANCH}"
echo "    git push ${REMOTE} ${TAG}"
echo "To undo before pushing: git tag -d ${TAG} && git reset --hard HEAD~1  (only if a changelog commit was made)"
