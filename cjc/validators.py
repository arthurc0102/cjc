import typing as t

import questionary
from prompt_toolkit import document


class RequiredValidator(questionary.Validator):
    def validate(self, document: document.Document):
        if len(document.text) == 0:
            raise questionary.ValidationError(
                message="Please enter a value",
                cursor_position=len(document.text),
            )


def required_choice_validator(choices: list[t.Any]):
    if len(choices):
        return True

    return "Please at least one value."
