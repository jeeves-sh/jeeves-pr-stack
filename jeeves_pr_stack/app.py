from rich.console import Console, RenderableType
from rich.style import Style
from rich.table import Table
from rich.text import Text
from typer import Typer

from jeeves_pr_stack import github
from jeeves_pr_stack.models import PullRequest, ChecksStatus

app = Typer(
    help='Manage stacks of GitHub PRs.',
    name='stack',
    invoke_without_command=True,
)


def format_status(pr: PullRequest) -> RenderableType:
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


@app.callback()
def print_stack():
    """Print current PR stack."""
    stack = github.retrieve_stack()

    console = Console()
    if not stack:
        console.print(
            '∅ No PRs associated with current branch.\n',
            style=Style(color='white', bold=True),
        )
        console.print('Use [code]gh pr create[/code] to create one.')
        return

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
            format_status(pr),
        )

    console.print(table)

    if len(stack) > 1:
        console.print(
            'Use [code]gh pr checkout <number>[/code] '
            'to switch to another PR.\n',
        )
