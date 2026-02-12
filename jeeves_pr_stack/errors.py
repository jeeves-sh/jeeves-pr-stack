from dataclasses import dataclass

from documented import DocumentedError


@dataclass
class DivergentBranches(DocumentedError):
    """
    Branches are not in sync.

    Please ensure that `{self.branch}` is in sync with `origin`.
    """

    branch: str


@dataclass
class NoPullRequestOnBranch(DocumentedError):
    """
    The branch does not have a Pull Request attached to it.

    Branch: {self.branch}
    """

    branch: str


class MergeConflicts(DocumentedError):
    """
    Merge conflicts detected.

    Please resolve conflicts and issue

    `j stack rebase`

    …once again.
    """


class GhPrEditDeprecationError(DocumentedError):
    """
    Failed to update the PR base branch.

    The gh CLI hit a GraphQL deprecation error (Projects classic).
    This is a known issue: https://github.com/cli/cli/issues/11983

    Please upgrade gh via your package manager
    (e.g. brew upgrade gh, sudo apt install gh).
    See https://github.com/cli/cli#installation
    """
