import json
import os

import rich
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text
from sh import gh
from typer import Typer

from jeeves_pr_stack.models import PullRequestStatus

app = Typer(
    help='Manage stacks of GitHub PRs.',
    name='stack',
    invoke_without_command=True,
)


@app.callback()
def print_stack():
    """Print current PR stack."""
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
    # rich.print(response)

    table = Table(
        '',
        'PR',
        'Status',
        title='Stack',
    )

    current_pr_id = response['currentBranch']['id']
    for pr in reversed(response['createdBy']):
        is_current = '➤' if pr['id'] == current_pr_id else ''
        table.add_row(
            is_current,
            Text(
                pr['title'],
                style=Style(link=pr['url']),
            ),
        )

    Console().print(table)
