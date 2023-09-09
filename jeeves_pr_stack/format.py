from rich.console import RenderableType
from rich.style import Style
from rich.table import Table
from rich.text import Text

from jeeves_pr_stack.models import PullRequest, ChecksStatus


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
