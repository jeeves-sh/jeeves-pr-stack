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
        'Current',
        'Number',
        'PR',
        'Status',
        show_header=False,
        show_lines=False,
        show_edge=False,
        box=None,
    )

    for pr in stack:
        is_current = '➤' if pr.is_current else ''

        heading = Text()
        heading.append(
            pr.title,
            style=Style(link=pr.url, bold=True),
        )
        heading.append(
            f'\n{pr.branch}',
            style=Style(color='magenta'),
        )
        heading.append(
            f' → ',
            style=None,
        )
        heading.append(
            f'{pr.base_branch}\n',
            style=Style(color='magenta'),
        )

        table.add_row(
            is_current,
            str(pr.number),
            heading,
        )

    console = Console()

    console.print(table)
    console.print(
        'Use [code]gh pr checkout <number>[/code] to switch to another PR.\n',
    )
