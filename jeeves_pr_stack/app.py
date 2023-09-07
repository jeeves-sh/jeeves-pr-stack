import json
import os

from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text
from sh import gh
from typer import Typer

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
    response = json.loads(
        gh.pr.status(
            json=','.join(fields),
            _env={
                **os.environ,
                'NO_COLOR': '1',
            },
        ),
    )

    table = Table(
        'PR',
        'Status',
    )

    table.add_row(
        Text(
            response['currentBranch']['title'],
            style=Style(link=response['currentBranch']['url']),
        ),
    )

    Console().print(table)
