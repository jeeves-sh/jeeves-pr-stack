from dataclasses import dataclass

from documented import DocumentedError


@dataclass
class DivergentBranches(DocumentedError):
    """
    Branches are not in sync.

    Please ensure that `{self.branch}` is in sync with `origin`.
    """

    branch: str
