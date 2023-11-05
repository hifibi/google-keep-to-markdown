import json
from typing import List
from jinja2 import Environment, FileSystemLoader
from slugify import slugify

def to_pretty_json(value):
    #jinja function
    return json.dumps(value, sort_keys=True, default=str,
                      indent=4, separators=(',', ': '))

def get_jinja_env() -> Environment:
    fileLoader = FileSystemLoader("templates")
    env = Environment(loader=fileLoader)
    env.filters['tojson_pretty'] = to_pretty_json
    env.filters['slugify'] = slugify
    return env

def get_note_markdown(note: dict, template_file: str = 'keep.md.jinja') -> str:
    env = get_jinja_env()
    rtn = env.get_template(template_file).render(note = note)
    return rtn

def get_tagfile_markdown(data: List[dict], template_file: str = 'tagfile.md.jinja') -> str:
    env = get_jinja_env()
    rtn = env.get_template(template_file).render(data = data)
    return rtn