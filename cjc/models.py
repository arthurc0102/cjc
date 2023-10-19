import pydantic


def to_lower_camel(name: str) -> str:
    upper = "".join(word.capitalize() for word in name.split("_"))
    return upper[:1].lower() + upper[1:]


class BaseResponseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(alias_generator=to_lower_camel)


class Group(BaseResponseModel):
    id_: int = pydantic.Field(alias="id")
    name: str


class Exercise(BaseResponseModel):
    name: str
    problem_set_id: int
    problem_set_type: str


class Problem(BaseResponseModel):
    class Locale(BaseResponseModel):
        title: str
        description: str
        locale_code: str

    class EditFile(BaseResponseModel):
        file_name: str
        extension: str
        file_stream: str

    tags: list[str]
    locales: list[Locale]
    edit_files: list[EditFile]


class ProblemSet(BaseResponseModel):
    name: str
    problems: list[Problem]


class Activity(BaseResponseModel):
    activity_type: str
    problem_set: ProblemSet
