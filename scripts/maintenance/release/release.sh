#!/usr/bin/env bash
#
# Guided release helper for cosmicjellyfish: changelog commit + annotated git tag.
#
# It walks through the release one step at a time, explains each step before doing it
# and waits for you. IT NEVER PUSHES: at the end it prints the exact push commands, and
# you run them on purpose. Full guide: docs/source/releasing.md
#
# USAGE
#   scripts/maintenance/release/release.sh --dry-run   checks only, changes nothing
#   scripts/maintenance/release/release.sh             guided release, step by step
#   scripts/maintenance/release/release.sh --yes       same, without pauses or questions
#
# BEFORE YOU RUN IT
#   1. Everything you want to ship is merged into main (through a pull request).
#   2. git switch main && git pull --ff-only
#   3. You bumped _MAJOR/_MINOR/_PATCH/_SUFFIX in cosmicjellyfish/version.py and the
#      "version:" line in CITATION.cff (CI checks that they agree), and committed that
#      bump: the working tree has to be clean. Final releases use an empty _SUFFIX,
#      release candidates use e.g. "rc1".
#
# WHAT HAPPENS WHEN YOU PUSH THE TAG (.github/workflows/main.yml)
#   * tag contains "rc"  (e.g. v2.0.0rc1) -> published to TestPyPI, GitHub pre-release.
#   * any other tag      (e.g. v2.0.0)    -> published to PyPI after the reviewers of the
#                                            "pypi" GitHub environment approve it.
#   The workflow fails on purpose if the tag is not "v" + VERSION from version.py.
#   A TestPyPI/PyPI version can never be uploaded twice: if a release is broken, bump
#   the version (rc1 -> rc2, 2.0.0 -> 2.0.1) instead of re-tagging.
#
# Environment: PYTHON overrides the interpreter used for the helper scripts
# (default: python; for example PYTHON="uv run python").

set -euo pipefail

RELEASE_BRANCH="main"
REMOTE="origin"
ACTIONS_URL="https://github.com/santiagocasas/cosmicjellyfish/actions"
# Build an array so that multi-word commands such as "uv run python" work, while an
# existing executable path (even one containing spaces) stays a single argument.
PYTHON_CMD="${PYTHON:-python}"
if [[ -x "$PYTHON_CMD" && ! -d "$PYTHON_CMD" ]]; then
    PYTHON=("$PYTHON_CMD")
else
    read -r -a PYTHON <<< "$PYTHON_CMD"
fi
DRY_RUN=0
ASSUME_YES=0
TOTAL_STEPS=5

for arg in "$@"; do
    case "$arg" in
        -n|--dry-run) DRY_RUN=1 ;;
        -y|--yes) ASSUME_YES=1 ;;
        -h|--help)
            sed -n '2,/^set -euo/p' "${BASH_SOURCE[0]}" | sed '$d' | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Error, unknown argument: $arg (use --dry-run, --yes or --help)" >&2
            exit 2
            ;;
    esac
done

fail() {
    echo "Error, $*" >&2
    exit 1
}

step() {   # step N "title"
    echo
    echo "=== Step $1/${TOTAL_STEPS}: $2"
}

pause() {  # wait for Enter before moving on
    [[ "${ASSUME_YES}" -eq 1 ]] && return 0
    local answer
    read -r -p "    Press Enter to continue (Ctrl-C to stop) " answer \
        || fail "no input available. Run in a terminal, or use --yes."
}

ask() {    # ask "question": must answer yes, default is no
    [[ "${ASSUME_YES}" -eq 1 ]] && return 0
    local answer
    read -r -p "    $1 [y/N] " answer || fail "no input available. Run in a terminal, or use --yes."
    [[ "${answer}" =~ ^([yY]|[yY][eE][sS])$ ]] || { echo "    Stopped. Nothing further was changed."; exit 1; }
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"
# The helper scripts import cosmicjellyfish.version: make that work without an install.
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

# --- Step 1: safety checks (read-only) --------------------------------------------------

step 1 "Safety checks (nothing is modified)"
echo "    The release must start from a clean, up-to-date '${RELEASE_BRANCH}' with a version"
echo "    that has not been tagged yet."

[[ "$(git rev-parse --abbrev-ref HEAD)" == "${RELEASE_BRANCH}" ]] \
    || fail "releases are made from '${RELEASE_BRANCH}', but you are on '$(git rev-parse --abbrev-ref HEAD)'. Run: git switch ${RELEASE_BRANCH}"
echo "    ok   on branch ${RELEASE_BRANCH}"

[[ -z "$(git status --porcelain)" ]] \
    || fail "the working tree is not clean. Commit or stash your changes first (including the version bump)."
echo "    ok   working tree is clean"

git fetch --quiet "${REMOTE}" "${RELEASE_BRANCH}" --tags
[[ "$(git rev-parse HEAD)" == "$(git rev-parse "${REMOTE}/${RELEASE_BRANCH}")" ]] \
    || fail "local '${RELEASE_BRANCH}' differs from '${REMOTE}/${RELEASE_BRANCH}'. Run 'git pull --ff-only' (or push your commits) first."
echo "    ok   ${RELEASE_BRANCH} matches ${REMOTE}/${RELEASE_BRANCH}"

# Read the version without importing the package (no dependencies needed).
VERSION="$("${PYTHON[@]}" -c 'import runpy; print(runpy.run_path("cosmicjellyfish/version.py")["VERSION"])')"
[[ -n "${VERSION}" ]] || fail "could not read VERSION from cosmicjellyfish/version.py."
TAG="v${VERSION}"

# version.py and CITATION.cff must agree (the same check that CI runs).
"${PYTHON[@]}" scripts/maintenance/release/check_version_consistency.py
echo "    ok   version.py and CITATION.cff agree on ${VERSION}"

if git rev-parse --quiet --verify "refs/tags/${TAG}" >/dev/null; then
    fail "tag ${TAG} already exists locally or on ${REMOTE}. Bump the version in version.py instead of re-using a tag."
fi
echo "    ok   tag ${TAG} does not exist yet"

if [[ "${TAG}" == *rc* ]]; then
    KIND="release candidate"
    TARGET="TestPyPI (pre-release)"
else
    KIND="final release"
    TARGET="PyPI (needs approval by the 'pypi' environment reviewers)"
fi

# --- Step 2: summary --------------------------------------------------------------------

step 2 "What will be released"
echo "    Version : ${VERSION} (${KIND})"
echo "    Tag     : ${TAG}"
echo "    Commit  : $(git rev-parse --short HEAD) on ${RELEASE_BRANCH}"
echo "    Publish : pushing the tag will publish to ${TARGET}"

if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo
    echo "Dry run: all checks passed, nothing was changed. A real run would now:"
    echo "    3. move '## Unreleased' in CHANGELOG.md into '## [${TAG}]' and commit only that file"
    echo "    4. create the annotated tag ${TAG}"
    echo "    5. print the push commands and what to check afterwards"
    exit 0
fi
pause

# --- Step 3: changelog commit -----------------------------------------------------------

step 3 "Changelog commit"
echo "    CHANGELOG.md: the notes under '## Unreleased' move into a dated '## [${TAG}]'"
echo "    heading. The GitHub release text is built from that heading. Only CHANGELOG.md"
echo "    is committed; nothing else is staged."
ask "Update and commit CHANGELOG.md?"

"${PYTHON[@]}" scripts/maintenance/release/prepare_changelog.py

grep -q "^## \[${TAG}\]" CHANGELOG.md \
    || fail "CHANGELOG.md has no '## [${TAG}]' section after prepare_changelog.py."

CHANGELOG_COMMITTED=0
if ! git diff --quiet -- CHANGELOG.md; then
    git add CHANGELOG.md   # only the changelog, never 'git add -A'
    git commit --quiet -m "Prepare changelog for ${TAG}"
    CHANGELOG_COMMITTED=1
    echo "    committed: $(git log --oneline -1)"
else
    echo "    CHANGELOG.md already had a '## [${TAG}]' section, nothing to commit."
fi
pause

# --- Step 4: tag ------------------------------------------------------------------------

step 4 "Annotated tag"
echo "    Creates ${TAG} on $(git rev-parse --short HEAD) (git tag -a ${TAG} -m ${TAG})."
echo "    The tag is local only until you push it."
ask "Create tag ${TAG}?"

git tag -a "${TAG}" -m "${TAG}"
echo "    created: ${TAG} -> $(git rev-parse --short "${TAG}^{commit}")"
pause

# --- Step 5: what you do next -----------------------------------------------------------

step 5 "Your turn: review, push, verify (the script never pushes)"
echo
echo "  A. Review what will be published:"
echo "       git log --oneline -3"
echo "       git show ${TAG} --stat"
echo
echo "  B. Push the commit and the tag:"
if [[ "${CHANGELOG_COMMITTED}" -eq 1 ]]; then
    echo "       git push ${REMOTE} ${RELEASE_BRANCH}"
fi
echo "       git push ${REMOTE} ${TAG}"
echo "     If ${RELEASE_BRANCH} refuses direct pushes, open a pull request for the changelog"
echo "     commit first and tag the merged commit instead:"
echo "       git tag -d ${TAG} && git tag -a ${TAG} -m ${TAG} <merge-commit>"
echo
echo "  C. Watch the workflow: ${ACTIONS_URL}"
if [[ "${TAG}" == *rc* ]]; then
    echo "     It publishes to TestPyPI: https://test.pypi.org/project/cosmicjellyfish/${VERSION}/"
    echo
    echo "  D. Test the install in a fresh environment, away from this checkout:"
    echo "       uv venv /tmp/cj-check --python 3.12"
    echo "       uv pip install --python /tmp/cj-check/bin/python \\"
    echo "         --index-url https://test.pypi.org/simple/ \\"
    echo "         --extra-index-url https://pypi.org/simple/ \\"
    echo "         --index-strategy unsafe-best-match cosmicjellyfish==${VERSION}"
    echo "       cd /tmp && /tmp/cj-check/bin/python -c 'import cosmicjellyfish; print(cosmicjellyfish.__file__)'"
    echo
    echo "  E. If it is good, repeat with an empty _SUFFIX for the final release. If not,"
    echo "     fix it, bump to the next rc (a used version cannot be uploaded again) and rerun."
else
    echo "     It waits for an approval of the 'pypi' environment: approve it in the Actions run."
    echo "     Then it publishes to https://pypi.org/project/cosmicjellyfish/${VERSION}/"
    echo
    echo "  D. Test the install in a fresh environment, away from this checkout:"
    echo "       uv venv /tmp/cj-check --python 3.12"
    echo "       uv pip install --python /tmp/cj-check/bin/python cosmicjellyfish==${VERSION}"
    echo "       cd /tmp && /tmp/cj-check/bin/python -c 'import cosmicjellyfish; print(cosmicjellyfish.__file__)'"
fi
echo
echo "  To undo before pushing:"
if [[ "${CHANGELOG_COMMITTED}" -eq 1 ]]; then
    echo "       git tag -d ${TAG} && git reset --hard HEAD~1"
else
    echo "       git tag -d ${TAG}"
fi
echo
echo "Done. Nothing has been pushed."
