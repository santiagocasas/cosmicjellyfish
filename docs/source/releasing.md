# Releasing

How a new version of cosmicjellyfish gets to TestPyPI and PyPI. The short version: you bump
the version, run `scripts/maintenance/release/release.sh`, and push the tag it creates. The
tag is what starts the publishing workflow.

## How it works

Publishing is done by `.github/workflows/main.yml` using PyPI Trusted Publishing, so there
are no passwords or tokens stored in GitHub. Which index a release goes to depends only on
the tag name:

| Tag | Example | What happens |
| --- | --- | --- |
| contains `rc` | `v2.0.0rc1` | Publishes to **TestPyPI** and creates a GitHub pre-release. |
| anything else | `v2.0.0` | Publishes to **PyPI** after a reviewer approves the `pypi` environment, then creates the GitHub release. |

Two rules the workflow enforces:

- The tag must be exactly `v` plus the version in `cosmicjellyfish/version.py`. A mismatch
  fails the job on purpose.
- A version can be uploaded to an index only once, ever. If a release turns out to be
  broken, bump the version (`rc1` to `rc2`, `2.0.0` to `2.0.1`) instead of re-tagging.

The workflow can also be run by hand (Actions tab, "Main", "Run workflow") to publish the
current version to TestPyPI without a tag.

## One-time setup

This is already done for the main repository, listed here so it can be recreated:

- A pending (or active) trusted publisher on <https://test.pypi.org/manage/account/publishing/>
  and on <https://pypi.org/manage/account/publishing/>: project `cosmicjellyfish`, owner
  `santiagocasas`, repository `cosmicjellyfish`, workflow `main.yml`, environment
  `testpypi` or `pypi` respectively.
- GitHub environments `testpypi` (no rules) and `pypi` (deployment restricted to tags
  `v*`, required reviewers).

## Releasing step by step

1. **Merge everything you want to ship into `main`** through a pull request, then update
   your checkout:

   ```bash
   git switch main
   git pull --ff-only
   ```

2. **Bump the version** in `cosmicjellyfish/version.py` (`_MAJOR`, `_MINOR`, `_PATCH`,
   `_SUFFIX`) and the `version:` line of `CITATION.cff`. Release candidates use a suffix
   such as `rc1`; final releases use an empty `_SUFFIX`. A `Metadata` CI check fails if the
   two files disagree. Commit the bump through a pull request if `main` is protected.

3. **Run the release helper** from a clean, up-to-date `main`:

   ```bash
   scripts/maintenance/release/release.sh --dry-run   # checks only, changes nothing
   scripts/maintenance/release/release.sh             # guided, one step at a time
   ```

   The script explains each step before doing it and waits for you. It refuses to start
   unless you are on `main`, the working tree is clean, `main` matches `origin/main`, the
   tag does not exist yet, and `version.py` and `CITATION.cff` agree. It then:

   - turns `## Unreleased` in `CHANGELOG.md` into a dated `## [vX.Y.Z]` section and commits
     only that file;
   - creates the annotated tag `vX.Y.Z` (the equivalent of `git tag -a vX.Y.Z -m vX.Y.Z`);
   - prints the exact push commands and what to check afterwards.

   It never pushes. Use `--yes` to skip the pauses and questions, `--help` for the options.

4. **Push the commit and the tag**, as printed by the script:

   ```bash
   git push origin main
   git push origin vX.Y.Z
   ```

   If `main` does not accept direct pushes, open a pull request for the changelog commit
   first and tag the merged commit instead: `git tag -a vX.Y.Z -m vX.Y.Z <merge-commit>`.

5. **Watch the workflow** at <https://github.com/santiagocasas/cosmicjellyfish/actions>.
   For a final release, approve the `pypi` environment when GitHub asks.

6. **Check the published package** in a fresh environment, away from your checkout:

   ```bash
   # TestPyPI release candidate
   uv venv /tmp/cj-check --python 3.12
   uv pip install --python /tmp/cj-check/bin/python \
     --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     --index-strategy unsafe-best-match \
     cosmicjellyfish==2.0.0rc1

   # PyPI final release
   uv pip install --python /tmp/cj-check/bin/python cosmicjellyfish==2.0.0

   cd /tmp
   /tmp/cj-check/bin/python -c "import cosmicjellyfish; print(cosmicjellyfish.__file__)"
   ```

   The printed path must be inside `/tmp/cj-check`. The optional `symbolic_pofk` package is
   not on PyPI; install it separately if you want to test `code="symbolic"`.

A typical sequence is `2.0.0rc1` to TestPyPI, check the install, then repeat steps 2 to 6
with an empty `_SUFFIX` for `2.0.0` on PyPI.

## When something goes wrong

**Nothing pushed yet.** Undo the local tag, and the changelog commit if one was made:

```bash
git tag -d vX.Y.Z
git reset --hard HEAD~1    # only if the script made a changelog commit
```

**The workflow failed before anything was uploaded** (for example a failing check). Fix the
problem on `main`, then move the tag. Delete only the broken tag, locally and on GitHub,
and delete the matching GitHub release if one was created:

```bash
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

Then run `release.sh` again.

**The upload already reached TestPyPI or PyPI.** That version is used up. Fix the problem,
bump the version (`rc2`, or the next patch version), and release again. On PyPI you can
also yank a bad release from the project page, which hides it from new installs without
deleting it.
