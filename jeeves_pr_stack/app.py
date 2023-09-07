from rich.console import Console, RenderableType
from rich.style import Style
from rich.table import Table
from rich.text import Text
from typer import Typer

from jeeves_pr_stack import github
from jeeves_pr_stack.models import ChecksStatus, PullRequest

app = Typer(
    help='Manage stacks of GitHub PRs.',
    name='stack',
    invoke_without_command=True,
)


def format_status(pr: PullRequest) -> RenderableType:
    """Format PR status."""
    if pr.checks_status == ChecksStatus.FAILURE:
        return Text(
            '❌ Checks failed',
            style=Style(color='red'),
        )

    if pr.review_decision == 'REVIEW_REQUIRED':
        formatted_reviewers = ', '.join(pr.reviewers)
        return Text(
            f'👀 Review required\n{formatted_reviewers}',
            style=Style(color='yellow'),
        )

    if pr.is_draft:
        return Text(
            '📝 Draft',
            style=Style(color='bright_black'),
        )

    return Text(
        '✅ Ready to merge',
        style=Style(
            color='green',
        ),
    )


def _print_stack(stack: list[PullRequest]):
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

    for index, pr in enumerate(stack):
        is_current = '➤' if pr.is_current else ''
        is_top_pr = (index == 0)

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
            ' → ',
            style=None,
        )
        heading.append(
            f'{pr.base_branch}\n',
            style=Style(color='magenta'),
        )

        if is_top_pr:
            heading.append('Top PR', style=Style(
                bold=True,
                reverse=True,
            ))
            heading.append(' Start merging the stack from here.\n')

        table.add_row(
            is_current,
            str(pr.number),
            heading,
            format_status(pr),
        )

    console = Console()
    console.print(table)

    if len(stack) > 1:
        console.print(
            'Use [code]gh pr checkout <number>[/code] to switch to another PR.',
        )


@app.callback()
def print_current_stack():
    """Print current PR stack."""
    stack = github.retrieve_stack()

    if stack:
        _print_stack(stack)
        return

    console = Console()
    console.print(
        '∅ No PRs associated with current branch.\n',
        style=Style(color='white', bold=True),
    )
    console.print('Use [code]gh pr create[/code] to create one.')


@app.command()
def rebase():
    """Rebase current stack."""
    raise NotImplementedError()


@app.command()
def merge():
    """Merge current stack, starting from the top."""
    raise NotImplementedError()


@app.command()
def comment():
    """
    Add or update a comment with a navigation table to each PR in current stack.
    """
    raise NotImplementedError()


@app.command()
def fork():
    """Fork from current branch, adding another item to the stack."""
    raise NotImplementedError()
