import json
from typing import List
from jinja2 import Environment, FileSystemLoader
import judo_utils

def to_pretty_json(value):
    #jinja function
    return json.dumps(value, sort_keys=True, default=str,
                      indent=4, separators=(',', ': '))

def get_jinja_env() -> Environment:
    fileLoader = FileSystemLoader("templates")
    env = Environment(loader=fileLoader)
    env.filters['tojson_pretty'] = to_pretty_json
    env.filters['slugify'] = judo_utils.slugify
    return env

def get_note_markdown(note: dict) -> str:
    env = get_jinja_env()
    rtn = env.get_template("keep.md.jinja").render(note = note)
    return rtn

def get_tagfile_markdown(data_by_tag: List[dict]) -> str:
    env = get_jinja_env()
    rtn = env.get_template("tagfile.md.jinja").render(data_by_tag = data_by_tag)
    return rtn