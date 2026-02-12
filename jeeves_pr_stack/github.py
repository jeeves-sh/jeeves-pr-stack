import json
import os

from networkx import DiGraph, edge_dfs
from sh import Command, ErrorReturnCode, gh, git

from jeeves_pr_stack.errors import GhPrEditDeprecationError
from jeeves_pr_stack.models import ChecksStatus, PullRequest, RawPullRequest


def construct_checks_status(raw_pull_request: RawPullRequest) -> ChecksStatus:
    """Analyze checks for PR and express their status as one value."""
    raw_status_values = {
        conclusion
        for check in raw_pull_request['statusCheckRollup']
        if (conclusion := check.get('conclusion'))
    }

    # This one is not informative
    raw_status_values.discard('SUCCESS')

    # No idea what to do with this one
    raw_status_values.discard('NEUTRAL')

    # We do not care
    raw_status_values.discard('SKIPPED')
    raw_status_values.discard('CANCELLED')

    try:
        raw_status_values.remove('')
    except KeyError:
        pass   # noqa: WPS420
    else:
        return ChecksStatus.RUNNING

    try:
        raw_status_values.remove('FAILURE')
    except KeyError:
        # No failures detected, we are fine
        pass   # noqa: WPS420
    else:
        return ChecksStatus.FAILURE

    if raw_status_values:
        raise ValueError(f'Unknown check statuses: {raw_status_values}')

    return ChecksStatus.SUCCESS


def construct_stack_for_branch(   # noqa: WPS210
    branch: str,
    pull_requests: list[PullRequest],
) -> list[PullRequest]:
    """Construct sequence of PRs that covers the given branch."""
    pull_request_by_branch = {
        pr.branch: pr
        for pr in pull_requests
    }

    graph = DiGraph(
        incoming_graph_data=[
            # PR is directed from its head branch → to its base branch.
            (pr.branch, pr.base_branch)
            for pr in pull_requests
        ],
    )

    successors = [
        (source, destination)
        for source, destination, _reverse   # noqa: WPS361
        in edge_dfs(graph, source=branch, orientation='reverse')
    ]
    predecessors = list(reversed(list(edge_dfs(graph, source=branch))))
    edges = predecessors + successors

    return [
        pull_request_by_branch[branch]
        for branch, _base_branch in edges
    ]


def retrieve_current_branch() -> str:
    """Retrieve current git branch name."""
    return git.branch('--show-current').strip()


def _construct_gh_env() -> dict[str, str]:
    return {
        **os.environ,
        'NO_COLOR': '1',
    }


def construct_gh_command() -> Command:
    """Construct the GitHub CLI command."""
    return gh.bake(
        _long_sep=None,
        _env={
            **os.environ,
            'NO_COLOR': '1',
        },
    )


def retrieve_default_branch() -> str:
    """Get default branch of current repository."""
    return json.loads(
        gh.repo.view(
            json='defaultBranchRef',
            _env=_construct_gh_env(),
        ),
    )['defaultBranchRef']['name']


def update_pr_base(gh_cmd, pr_number: int, base_branch: str) -> None:
    """Update a PR's base branch. Raises GhPrEditDeprecationError on deprecation."""  # noqa: E501
    try:
        gh_cmd.pr.edit(pr_number, base=base_branch)
    except ErrorReturnCode as err:
        stderr_raw = err.stderr
        if isinstance(stderr_raw, bytes):
            stderr = stderr_raw.decode()
        else:
            stderr = str(stderr_raw)
        projects_classic = 'Projects (classic)' in stderr
        project_cards = 'repository.pullRequest.projectCards' in stderr
        if projects_classic and project_cards:
            raise GhPrEditDeprecationError() from err
        raise
