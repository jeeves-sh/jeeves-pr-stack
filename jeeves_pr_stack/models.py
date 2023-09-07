from typing import TypedDict


class CurrentBranch(TypedDict):
    """Section of gh CLI output."""

    title: str
    url: str
    baseRefName: str
    id: str


class CreatedBy(TypedDict):
    baseRefName: str
    headRefName: str
    title: str
    url: str
    id: str


class PullRequestStatus(TypedDict):
    """Raw output from gh CLI."""

    createdBy: list[CreatedBy]
    currentBranch: CurrentBranch
