import funcy
from rich.console import Console, RenderableType
from rich.prompt import Prompt
from rich.style import Style
from rich.table import Table
from rich.text import Text
from sh import gh
from typer import Typer, Exit

from jeeves_pr_stack import github
from jeeves_pr_stack.models import (
    ChecksStatus, PullRequest, State,
    PRStackContext,
)

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
            ' → ',
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

    console = Console()
    console.print(table)

    if len(stack) > 1:
        console.print(
            'Use [code]gh pr checkout <number>[/code] to switch to another PR.',
        )


@app.callback()
def print_current_stack(context: PRStackContext):
    """Print current PR stack."""
    current_branch = github.retrieve_current_branch()
    stack = github.retrieve_stack(current_branch=current_branch)

    context.obj = State(
        current_branch=current_branch,
        stack=stack,
    )

    if stack:
        _print_stack(stack)
        return

    console = Console()
    console.print(
        '∅ No PRs associated with current branch.\n',
        style=Style(color='white', bold=True),
    )
    console.print('• Use [code]gh pr create[/code] to create one,')
    console.print(
        '• Or [code]j stack append[/code] to stack it onto another PR.',
    )


@app.command()
def rebase():
    """Rebase current stack."""
    raise NotImplementedError()


@app.command()
def merge(context: PRStackContext):
    """Merge current stack, starting from the top."""


@app.command()
def comment():
    """Comment on each PR of current stack with a navigation table."""
    raise NotImplementedError()


@app.command()
def split():
    """Split current PR which is deemed to be too large."""
    raise NotImplementedError()


@app.command()
def append(context: PRStackContext):   # noqa: WPS210
    """Direct current branch/PR to an existing PR."""
    console = Console()
    state = context.obj

    if state.stack:
        console.print(
            '\n🚫 This PR is already part of a stack.\n',
            style=Style(color='red', bold=True),
        )
        raise Exit(1)

    console.print(f'Current branch:\n  {state.current_branch}\n')

    pull_requests = github.retrieve_pull_requests_to_append(
        current_branch=state.current_branch,
    )

    _print_stack(pull_requests)

    choices = [str(pr.number) for pr in pull_requests]
    number = int(
        Prompt.ask(
            'Select the PR',
            choices=choices,
            show_choices=True,
            default=funcy.first(choices),
        ),
    )

    pull_request_by_number = {pr.number: pr for pr in pull_requests}
    base_pull_request = pull_request_by_number[number]

    gh.pr.create(base=base_pull_request.branch, assignee='@me', _fg=True)
