import json
import os

from jeeves_pr_stack.models import PullRequest, PullRequestStatus
from sh import gh


def retrieve_stack() -> list[PullRequest]:
    """Retrieve the current PR stack."""
    fields = [
        'baseRefName',
        'headRefName',
        'id',
        'isDraft',
        'mergeable',
        'title',
        'url',
    ]
    response: PullRequestStatus = json.loads(
        gh.pr.status(
            json=','.join(fields),
            _env={
                **os.environ,
                'NO_COLOR': '1',
            },
        ),
    )

    current_pr_id = response['currentBranch']['id']
    return [
        PullRequest(
            title=pr['title'],
            branch=pr['headRefName'],
            url=pr['url'],
            is_current=pr['id'] == current_pr_id,
        )
        for pr in reversed(response['createdBy'])
    ]
