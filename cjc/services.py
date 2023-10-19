import base64
import collections
import pathlib
import re

import httpx
import pydantic
import typer

from cjc import config, models

WINDOWS_LINE_ENDING = "\r\n"
UNIX_LINE_ENDING = "\n"


class CodeJudgeService:
    def __init__(self, account: str, password: str):
        self.account = account
        self.password = password
        self.settings = config.get_settings()

    def login(self):
        response = httpx.post(
            f"{self.settings.BASE_URL}/api/v2/User/Login",
            json={"account": self.account, "password": self.password},
        )
        response.raise_for_status()
        return response.text

    @property
    def token(self):
        if not hasattr(self, "_token"):
            self._token = self.login()

        return self._token

    async def get_groups(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.settings.BASE_URL}/api/v2/User/Groups",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            response.raise_for_status()

        return pydantic.TypeAdapter(list[models.Group]).validate_json(response.content)

    async def get_exercises(self, group_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.settings.BASE_URL}/api/v2/Group/Exercise/List",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"GroupId": group_id},
            )
            response.raise_for_status()

        return pydantic.TypeAdapter(list[models.Exercise]).validate_json(
            response.content,
        )

    async def get_problem_set(self, group_id: int, problem_set_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.settings.BASE_URL}/api/v2/Group/Exercise/Problems",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "ActivityId": None,
                    "GroupId": group_id,
                    "ProblemSetId": problem_set_id,
                },
            )
            response.raise_for_status()

        return (
            pydantic.TypeAdapter(models.Activity)
            .validate_json(response.content)
            .problem_set
        )


def filter_and_group_exercises_by_type(exercises: list[models.Exercise]):
    pattern = re.compile(r"^TQC\+ (?P<type>.+) 第.*$")
    exercises_group_by_type: dict[str, list[models.Exercise]] = collections.defaultdict(
        list,
    )

    for exercise in exercises:
        matched = pattern.match(exercise.name)
        if not matched:
            continue

        exercises_group_by_type[matched.group("type")].append(exercise)

    return exercises_group_by_type


def save_problem_set(problem_set: models.ProblemSet, output_path: pathlib.Path):
    for problem in problem_set.problems:
        if not problem.locales:
            typer.echo("No locales for problem.")
            continue

        target_locale = problem.locales[0]
        for locale in problem.locales[1:]:
            if locale.locale_code.lower() != "zh-hant":
                continue

            target_locale = locale

        category, code, name = target_locale.title.rsplit(" ", maxsplit=2)

        problem_dir = (
            output_path
            / category
            / problem_set.name.lstrip(category).strip()
            / f"{code}_{name}"
        )
        problem_dir.mkdir(parents=True, exist_ok=True)

        md_content = target_locale.description.replace(
            WINDOWS_LINE_ENDING,
            UNIX_LINE_ENDING,
        )
        with (problem_dir / f"{code}.md").open("w") as f:
            f.write(f"# {target_locale.title}\n\n")
            f.write(md_content)

        parse_in_and_out_file_from_markdown(md_content, problem_dir)

        for file in problem.edit_files:
            b64_content = file.file_stream.split(",", maxsplit=1)[1]
            file_content = base64.b64decode(b64_content).replace(
                WINDOWS_LINE_ENDING.encode(),
                UNIX_LINE_ENDING.encode(),
            )
            with (problem_dir / file.file_name).open("wb") as f:
                f.write(file_content)


def parse_in_and_out_file_from_markdown(content: str, output_path: pathlib.Path):
    count = 0
    in_code_block = False
    file_name = None
    file_ext = "txt"

    lines = []
    for line in content.splitlines():
        if not file_name and "# 範例輸入" in line:
            file_name = "in"
            continue

        if not file_name and "# 範例輸出" in line:
            file_name = "out"
            continue

        if "```" in line and file_name:
            if not in_code_block:
                in_code_block = True
                continue

            _file_name = f"{file_name}{count}.{file_ext}"

            with (output_path / _file_name).open("w") as f:
                f.write(UNIX_LINE_ENDING.join(lines))

            if file_name == "out":
                count += 1

            file_name = None
            in_code_block = False
            lines = []
            continue

        if in_code_block:
            lines.append(line)
            continue
