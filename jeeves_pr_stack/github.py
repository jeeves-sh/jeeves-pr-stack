import json
import os

import funcy
from networkx import DiGraph, edge_dfs
from sh import gh, git

from jeeves_pr_stack.models import ChecksStatus, PullRequest, RawPullRequest


def construct_checks_status(raw_pull_request: RawPullRequest) -> ChecksStatus:
    """Analyze checks for PR and express their status as one value."""
    raw_status_values = set(
        funcy.pluck(
            'conclusion',
            raw_pull_request['statusCheckRollup'],
        ),
    )

    # This one is not informative
    raw_status_values.discard('SUCCESS')

    # No idea what to do with this one
    raw_status_values.discard('NEUTRAL')

    try:
        raw_status_values.remove('FAILURE')
    except KeyError:
        # No failures detected, we are fine
        pass
    else:
        return ChecksStatus.FAILURE

    if raw_status_values:
        raise ValueError(f'Unknown check statuses: {raw_status_values}')

    return ChecksStatus.SUCCESS


def construct_stack_for_branch(
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
        for source, destination, _reverse
        in edge_dfs(graph, source=branch, orientation='reverse')
    ]
    predecessors = list(edge_dfs(graph, source=branch))
    edges = predecessors + successors

    return [
        pull_request_by_branch[branch]
        for branch, _base_branch in edges
    ]


def retrieve_stack() -> list[PullRequest]:
    """Retrieve the current PR stack."""
    current_branch = git.branch('--show-current').strip()

    fields = [
        'number',
        'baseRefName',
        'headRefName',
        'id',
        'isDraft',
        'mergeable',
        'title',
        'url',
        'reviewDecision',
        'reviewRequests',
        'statusCheckRollup',
    ]

    raw_pull_requests: list[RawPullRequest] = json.loads(
        gh.pr.list(
            json=','.join(fields),
            _env={
                **os.environ,
                'NO_COLOR': '1',
            },
        ),
    )

    pull_requests = [
        PullRequest(
            is_current=raw_pull_request['headRefName'] == current_branch,
            number=raw_pull_request['number'],
            base_branch=raw_pull_request['baseRefName'],
            branch=raw_pull_request['headRefName'],
            title=raw_pull_request['title'],
            url=raw_pull_request['url'],
            is_draft=raw_pull_request['isDraft'],
            mergeable=raw_pull_request['mergeable'],
            review_decision=raw_pull_request['reviewDecision'],
            reviewers=funcy.pluck('login', raw_pull_request['reviewRequests']),
            checks_status=construct_checks_status(raw_pull_request),
        )
        for raw_pull_request in raw_pull_requests
    ]

    return construct_stack_for_branch(
        branch=current_branch,
        pull_requests=pull_requests,
    )
