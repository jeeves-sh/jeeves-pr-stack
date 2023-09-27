from rich.style import Style
from rich.table import Table
from rich.text import Text

from jeeves_pr_stack.models import ChecksStatus, PullRequest

bullet_point = '◉'
vertical_line = '│'


def format_status(pr: PullRequest) -> Text | str:
    """Format PR status."""
    if pr.is_draft:
        return Text(
            '📝 Draft',
            style=Style(color='bright_black'),
        )

    if pr.checks_status == ChecksStatus.FAILURE:
        return Text(
            '❌ Checks failed',
            style=Style(color='red'),
        )

    if pr.review_decision == 'REVIEW_REQUIRED':
        formatted_reviewers = ', '.join(pr.reviewers)
        return Text(
            f'👀 Review required: {formatted_reviewers}',
            style=Style(color='yellow'),
        )

    return Text(
        '✅ Ready to merge',
        style=Style(
            color='green',
        ),
    )


def format_branch(name: str, is_default: bool, is_current: bool) -> Text:
    pointer = ' '
    if is_current:
        color = 'bright_blue'
        pointer = '➡️'

    elif is_default:
        color = 'red'

    else:
        color = 'bright_yellow'

    return Text(
        f' {pointer}  {bullet_point} {name}\n',
        style=f'bold {color}',
    )


def pull_request_stack_as_table(
    stack: list[PullRequest],
    current_branch: str,
    default_branch: str,
):
    output = Text()
    stack = list(reversed(stack))

    output.append(
        format_branch(
            name=stack[0].branch,
            is_current=stack[0].branch == current_branch,
            is_default=stack[0].branch == default_branch,
        ),
    )

    for pull_request in stack:
        output.append(f'\n    {vertical_line}\n')
        output.append(f'    {vertical_line}   ')
        output.append(f'{pull_request.number:>#5} ', style='bold magenta')
        output.append(pull_request.title, style=Style(link=pull_request.url))
        output.append(f'\n')

        output.append(f'    {vertical_line}         ')
        output.append(format_status(pull_request))
        output.append(f'\n    {vertical_line}\n')

        output.append('    🭭 \n')

        output.append(
            format_branch(
                name=pull_request.base_branch,
                is_current=pull_request.base_branch == current_branch,
                is_default=pull_request.base_branch == default_branch,
            ),
        )

    return output


def pull_request_list_as_table(stack: list[PullRequest]):
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

    return table
