from typer import Typer
from sh import gh


app = Typer()


@app.callback()
def print_stack():
    ...
