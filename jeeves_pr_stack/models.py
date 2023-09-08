from typing import TypedDict


class CurrentBranch(TypedDict):
    """Section of gh CLI output."""

    title: str
    url: str


class PullRequestStatus(TypedDict):
    """Raw output from gh CLI."""

    currentBranch: CurrentBranch   # noqa: WPS115
