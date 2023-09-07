from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text
from typer import Typer

from jeeves_pr_stack import github

app = Typer(
    help='Manage stacks of GitHub PRs.',
    name='stack',
    invoke_without_command=True,
)


@app.callback()
def print_stack():
    """Print current PR stack."""
    stack = github.retrieve_stack()

    table = Table(
        '',
        'PR',
        'Status',
        title='Stack',
    )

    for pr in stack:
        is_current = '➤' if pr.is_current else ''
        table.add_row(
            is_current,
            Text(
                pr.title,
                style=Style(link=pr.url),
            ),
        )

    Console().print(table)
