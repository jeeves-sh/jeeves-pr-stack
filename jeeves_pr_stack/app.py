from typing import Annotated, Optional

import funcy
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.style import Style
from sh import gh, git
from typer import Argument, Exit, Typer

from jeeves_pr_stack import github
from jeeves_pr_stack.format import (
    pull_request_list_as_table,
    pull_request_stack_as_table,
)
from jeeves_pr_stack.models import PRStackContext, State, PullRequest

app = Typer(
    help='Manage stacks of GitHub PRs.',
    name='stack',
    invoke_without_command=True,
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

    console = Console()
    default_branch = github.retrieve_default_branch()
    if stack:
        console.print(
            pull_request_stack_as_table(
                stack,
                default_branch=default_branch,
                current_branch=current_branch,
            ),
        )
        return

    console.print(
        '∅ No PRs associated with current branch.\n',
        style=Style(color='white', bold=True),
    )
    console.print('• Use [code]gh pr create[/code] to create one,')
    console.print(
        '• Or [code]j stack push[/code] to stack it onto another PR.',
    )
    console.print()
    console.print('Get more help with [code]j stack --help[/code].')


@app.command()
def pop(context: PRStackContext):  # noqa: WPS213
    """Merge the bottom-most PR of current stack to the main branch."""
    if not context.obj.stack:
        raise ValueError('Nothing to merge, current stack is empty.')

    top_pr, *remaining_prs = context.obj.stack

    default_branch = github.retrieve_default_branch()
    console = Console()
    if top_pr.base_branch != default_branch:
        raise ValueError('Base branch of the PR ≠ default branch of the repo.')

    dependant_pr = None
    if remaining_prs:
        dependant_pr = funcy.first(remaining_prs)

    console.print('PR to merge: ', top_pr)
    console.print('Dependant PR: ', dependant_pr)

    if not Confirm.ask('Do you confirm?', default=True):
        console.print('Aborted.', style='red')
        raise Exit(1)

    if dependant_pr is not None:
        console.print(f'Changing base of {dependant_pr} to {default_branch}')
        gh.pr.edit('--base', default_branch, dependant_pr.number)

    console.print(f'Merging {top_pr}...')
    gh.pr.merge('--merge', top_pr.number)

    console.print(f'Deleting branch: {top_pr.branch}')
    git.push.origin('--delete', top_pr.branch)
    console.print('OK.')


@app.command()
def comment():
    """Comment on each PR of current stack with a navigation table."""
    raise NotImplementedError()


@app.command()
def split():
    """Split current PR which is deemed to be too large."""
    raise NotImplementedError()


def _ask_for_pull_request_number(pull_requests: list[PullRequest]) -> int:
    Console().print(pull_request_list_as_table(pull_requests))

    choices = [str(pr.number) for pr in pull_requests]

    return int(
        Prompt.ask(
            'Select the PR',
            choices=choices,
            show_choices=True,
            default=funcy.first(choices),
        ),
    )


@app.command()
def push(   # noqa: WPS210
    context: PRStackContext,
    pull_request_id: Annotated[Optional[int], Argument()] = None,
):
    """Direct current branch/PR to an existing PR."""
    console = Console()
    state = context.obj

    console.print(f'Current branch:\n  {state.current_branch}\n')

    pull_requests = github.retrieve_pull_requests_to_append(
        current_branch=state.current_branch,
    )

    if not pull_requests:
        raise ValueError('No PRs found which this branch could refer to.')

    if pull_request_id is None:
        pull_request_id = _ask_for_pull_request_number(pull_requests)

    pull_request_by_number = {pr.number: pr for pr in pull_requests}
    base_pull_request = pull_request_by_number[pull_request_id]

    gh.pr.create(base=base_pull_request.branch, assignee='@me', _fg=True)


@app.command()
def rebase(context: PRStackContext):
    """Rebase each PR in the stack upon its base."""
    with Progress() as progress:
        merging_task = progress.add_task(
            '[cyan]Rebasing PRs...',
            total=len(context.obj.stack),
        )

        for pr in context.obj.stack:
            progress.update(
                merging_task,
                advance=1,
                description=f'[green]Rebasing PR #{pr.number} {pr.title}...',
            )
            gh.pr.merge('--rebase', pr.number)
            progress.update(
                merging_task,
                description=f'[green]Successfully rebased PR #{pr.number}...',
            )
