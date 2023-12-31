from typing import Annotated, Optional

import funcy
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.style import Style
from sh import gh, git
from typer import Argument, Exit, Typer

from jeeves_pr_stack import github
from jeeves_pr_stack.errors import NoPullRequestOnBranch
from jeeves_pr_stack.format import (
    pull_request_list_as_table,
    pull_request_stack_as_table,
)
from jeeves_pr_stack.logic import JeevesPullRequestStack
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

    current_pull_request: PullRequest | None
    try:
        [current_pull_request] = [pr for pr in stack if pr.is_current]
    except ValueError:
        current_pull_request = None

    context.obj = State(
        current_branch=current_branch,
        stack=stack,
        gh=github.construct_gh_command(),
        current_pull_request=current_pull_request,
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

    application = JeevesPullRequestStack(  # noqa: F841
        gh=context.obj.gh,
        git=git,
    )

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
    application = JeevesPullRequestStack(
        gh=context.obj.gh,
        git=git,
    )

    console = Console()
    for is_not_first, pr in enumerate(application.rebase()):
        if is_not_first:
            console.print('OK', style='green')

        console.print(
            f'#{pr.number} {pr.title}… ',
            end='',
        )

    console.print('OK', style='green')
    console.print()
    console.print('✔ Stack 🥞 rebased.', style='green')


@app.command()
def split(context: PRStackContext):   # noqa: WPS210
    """Split current PR by commit."""
    application = JeevesPullRequestStack(
        gh=context.obj.gh,
        git=git,
    )

    console = Console()

    commits = application.list_commits()
    enumerated_commits = list(enumerate(commits, start=1))

    original_pull_request = context.obj.current_pull_request
    if original_pull_request is None:
        raise NoPullRequestOnBranch(branch=context.obj.current_branch)

    console.print('Commits:')
    for commit_number, commit in enumerated_commits:
        console.print(f'#{commit_number} {commit.title}')

    choices = [str(number) for number, _commit in enumerated_commits]
    splitting_commit_number = Prompt.ask(
        prompt='Please choose the commit by which to split the PR',
        default=funcy.first(choices),
        choices=choices,
        show_choices=True,
    )

    splitting_commit = dict(enumerated_commits)[int(splitting_commit_number)]

    console.print('Current branch:')
    console.print(context.obj.current_branch)
    new_branch_name = Prompt.ask(prompt='Enter the new branch name')

    application.split(
        splitting_commit=splitting_commit,
        new_pr_branch_name=new_branch_name,
        pull_request_to_split=original_pull_request,
    )
