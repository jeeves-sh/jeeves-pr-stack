from typer import Typer
from sh import gh


app = Typer(help='Manage stacks of GitHub PRs.')


@app.callback()
def print_stack():
    fields = [
        'baseRefName', 'headRefName', 'id', 'isDraft', 'mergeable', 'title',
        'url',
    ]
    gh.pr.status(json=','.join(fields))
