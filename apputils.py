import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger()

def read_json_file(filepath: Path) -> json:
    with open(filepath, 'r', encoding='utf-8') as p:
        rtn = json.load(p)
        logger.debug('got unconverted json')
        return rtn


def convert_usec_to_datetime(usec: int) -> datetime:
    rtn = datetime.fromtimestamp(timedelta(microseconds = usec).total_seconds())
    return rtn


def write_markdown_file(contents: str, target: Path) -> None:
    with open(target, 'w+', encoding="utf-8") as outfile:
        outfile.write(contents)


def write_json_toc(json_val: dict, target: Path) -> None:
    with open(target, 'w') as json_file:
            json.dump(json_val, json_file, indent=2)    
