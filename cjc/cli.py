import itertools
import pathlib
import typing as t

import questionary
import typer
from rich import progress

from cjc import models, services, utils, validators

app = typer.Typer()


@app.command()
@utils.async_to_sync
async def download(
    account: t.Annotated[str, typer.Option(help="Login account (email)")] = "",
    password: t.Annotated[str, typer.Option(help="Login password")] = "",
    output_dir: t.Annotated[str, typer.Option(help="Output path")] = "",
):
    account = account or (
        await questionary.text(
            "Login account (email):",
            validate=validators.RequiredValidator,
        ).unsafe_ask_async()
    )

    password = (
        password
        or await questionary.password(
            "Login password:",
            validate=validators.RequiredValidator,
        ).unsafe_ask_async()
    )

    output_path = pathlib.Path(
        output_dir
        or await questionary.path(
            "Output path:",
            default=str(pathlib.Path.cwd() / "output"),
        ).unsafe_ask_async(),
    )

    code_judge_service = services.CodeJudgeService(account, password)

    groups = await code_judge_service.get_groups()
    if not groups:
        typer.echo("No group found.")
        return

    target_group: models.Group = await questionary.select(
        "Choice a group:",
        [questionary.Choice(title=group.name, value=group) for group in groups],
    ).unsafe_ask_async()

    exercises_group_by_type = services.filter_and_group_exercises_by_type(
        await code_judge_service.get_exercises(target_group.id_),
    )

    exercises_of_types: list[list[models.Exercise]] = await questionary.checkbox(
        "Choice types:",
        [
            questionary.Choice(title=t, value=es)
            for t, es in exercises_group_by_type.items()
        ],
        validate=validators.required_choice_validator,
    ).unsafe_ask_async()

    target_exercises: list[models.Exercise] = await questionary.checkbox(
        "Choice exercises:",
        [
            questionary.Choice(title=e.name, value=e)
            for e in itertools.chain.from_iterable(exercises_of_types)
        ],
        validate=validators.required_choice_validator,
    ).unsafe_ask_async()

    for exercise in progress.track(target_exercises, description="Downloading..."):
        problem_set = await code_judge_service.get_problem_set(
            group_id=target_group.id_,
            problem_set_id=exercise.problem_set_id,
        )

        services.save_problem_set(problem_set, output_path)
