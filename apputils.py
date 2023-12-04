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


def write_text_file(contents: str, target: Path) -> None:
    with open(target, 'w+', encoding="utf-8") as outfile:
        outfile.write(contents)


def write_json_file(json_val: dict, target: Path) -> None:
    with open(target, 'w') as json_file:
            json.dump(json_val, json_file, indent=2)    


def convert_values_to_string(data):
    """
    Recursively convert values in a dictionary to strings.

    Parameters:
    - data (dict or list): Dictionary or list containing values to be converted.

    Returns:
    - dict or list: Resulting dictionary or list with values converted to strings.
    """
    if isinstance(data, dict):
        return {key: convert_values_to_string(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_values_to_string(item) for item in data]
    elif isinstance(data, datetime):
        return data.strftime('%Y-%m-%d_%H%M%S')
    elif isinstance(data, Path):
        return str(data)
    else:
        return data