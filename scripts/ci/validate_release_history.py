"""
Make sure the latest release tag is part of the current history before releasing.

python-semantic-release computes the next version from the commits since the
latest ``vX.Y.Z`` tag. If history was rewritten after a release (force push,
rebase), that tag no longer points into HEAD's history and the computed
version and changelog would be wrong. This script fails the release early
with a clear message instead.

Uses only git and the Python standard library, so it runs before any
dependencies are installed.

Exit codes:
    0: no release tags yet, or the latest tag is an ancestor of HEAD.
    1: the latest tag is not in the history of HEAD.
    2: git is unavailable or the repository is not usable.
"""

import re
import subprocess  # noqa: S404 - only runs git with fixed arguments
import sys

TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


def git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command and capture its output."""
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)  # noqa: S603, S607


def latest_release_tag() -> str | None:
    """Return the highest ``vX.Y.Z`` tag by version order, or None if there is none."""
    result = git("tag", "--list", "v*", "--sort=-v:refname")
    if result.returncode != 0:
        print(f"error: cannot list tags: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    return next((tag for tag in result.stdout.split() if TAG_PATTERN.match(tag)), None)


def main() -> int:
    """Validate that the latest release tag is an ancestor of HEAD."""
    tag = latest_release_tag()
    if tag is None:
        print("No release tags yet: nothing to validate.")
        return 0

    result = git("merge-base", "--is-ancestor", tag, "HEAD")
    if result.returncode == 0:
        print(f"OK: {tag} is in the history of HEAD.")
        return 0
    if result.returncode == 1:
        print(
            f"error: release tag {tag} is not in the history of HEAD.\n"
            "History was probably rewritten after that release (force push or rebase).\n"
            "Restore the tagged commit into the branch history, or move the tag, before releasing.",
            file=sys.stderr,
        )
        return 1
    print(f"error: git merge-base failed: {result.stderr.strip()}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
