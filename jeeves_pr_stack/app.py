from typer import Typer
from sh import gh


app = Typer(
    help='Manage stacks of GitHub PRs.',
    name='stack',
    invoke_without_command=True,
)


@app.callback()
def print_stack():
    fields = [
        'baseRefName', 'headRefName', 'id', 'isDraft', 'mergeable', 'title',
        'url',
    ]
    response = gh.pr.status(json=','.join(fields))
    print(response)
