import os

import click


@click.group("flask")
@click.option("--app", "app")
@click.option("--env")
@click.pass_context
def flask_group(ctx: click.Context, app: str, env: str) -> None:
    os.environ["FLASK_RUN_FROM_CLI"] = "true"
    # info = ctx.ensure_object(ScriptInfo)


@flask_group.command("run")
def run_command():
    click.echo("run")
