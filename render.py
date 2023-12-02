import json
from pathlib import Path
from typing import List
from jinja2 import Environment, FileSystemLoader
from slugify import slugify
from appconfig import keep_convert_config as kcfg

def to_pretty_json(value):
    #jinja function
    return json.dumps(value, sort_keys=True, default=str,
                      indent=4, separators=(',', ': '))

def get_jinja_env() -> Environment:
    fileLoader = FileSystemLoader(kcfg.get('templates_folder'))
    env = Environment(loader=fileLoader)
    env.filters['tojson_pretty'] = to_pretty_json
    env.filters['slugify'] = slugify
    return env

def get_note_markdown(note: dict, template_file: str = None) -> str:
    if not template_file:
        template_file = kcfg.get('notes_template_file')
    env = get_jinja_env()
    rtn = env.get_template(template_file).render(note = note)
    return rtn

def get_tagfile_markdown(data: List[dict], template_file: str = None) -> str:
    if not template_file:
        template_file = kcfg.get('tag_toc_template_file')
    env = get_jinja_env()
    rtn = env.get_template(template_file).render(data = data)
    return rtn