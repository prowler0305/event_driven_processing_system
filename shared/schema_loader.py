import json
from importlib import resources
from shared import schemas


def load_schema(name: str) -> dict:
    """
    Loads a schema definition and returns it as a dictionary.
    :param name:
    :return:
    """
    with resources.files(schemas).joinpath(name).open("r") as f:
        return json.load(f)