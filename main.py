from pathlib import Path
import json
import logging
from logging.config import fileConfig
import shutil
from datetime import datetime, timedelta
from typing import List
from slugify import slugify
import render
from config import keep_convert_config as kconfig
from collections import OrderedDict

fileConfig('logging.ini')
logger = logging.getLogger()

def get_converted_root_path() -> str:
    tgt = Path(kconfig['converted_notes_folder'])
    tgt.mkdir(parents=True,exist_ok=True)
    logger.debug(f"Markdown target={tgt.absolute()}")
    return tgt

def get_unconverted_file_paths() -> list[Path]:
    src = Path(kconfig['unconverted_notes_folder'])
    logger.debug(f"Getting unconverted Keep notes from {src.absolute()}")
    rtn = list(src.resolve().glob("**/*.json"))
    return rtn

def read_json_file(filepath: Path) -> json:
    with open(filepath, 'r', encoding='utf-8') as p:
        rtn = json.load(p)
        logger.debug('got unconverted json')
        return rtn

def process_note(p: Path) -> dict:
    note = read_json_file(p)
    note['keep_export_file'] = p.name
    note = add_dates(note)
    note = add_tags(note)
    note = fix_title(note)
    note = process_attachments(note, p) if 'attachments' in note else note
    note_path = render_note_to_markdown(note)
    brief_note = {key: note[key] for key in ["createdTimestampUsec", "title", "tags"]}
    brief_note["tags"] = brief_note["tags"].split(", ")
    brief_note["note_path"] = note_path
    return brief_note

def add_dates(note:dict) -> dict:
    note['created_at'] = convert_usec_to_datetime(note['createdTimestampUsec'])
    note['edited_at'] = convert_usec_to_datetime(note['userEditedTimestampUsec'])
    logger.debug('added dates')
    return note

def add_tags(note: dict) -> dict:
    taglist = []
    # labels
    if 'labels' in note.keys():
        tags = [v for k,v in note.items() if k == 'labels'][0]
        taglist = [slugify(i['name']) for i in tags]
    # Trashed
    if note['isTrashed']: taglist += ['Trashed']
    # Pinned
    if note['isPinned']: taglist += ['Pinned']
    # color-blue
    if 'color' in note.keys() and note['color'] != 'DEFAULT': taglist += ['color-' + note['color'].lower()]
    # created-2014
    taglist += ['created-' + note['created_at'].strftime('%Y')]
    # build one-line string for Jinja
    note['tags'] = '\#' + ", \#".join(taglist)
    return note

def process_attachments(note: dict, p: Path) -> dict:
    # separate attachment types to simplify jinja handling
    images = []
    assets = []

    for a in note['attachments']:
        # find attachment in root of unconverted notes location
        src = p.parent.resolve() / a['filePath']
        
        # target relative path
        subfolder = 'images' if a['mimetype'].startswith('image') else 'assets'
        relpath = Path(subfolder) / src.name
        logger.debug(f'Processing attachment {relpath}')

        # add relative path to the note for Jinja rendering
        images.append(relpath) if a['mimetype'].startswith('image') else assets.append(relpath)

        # copy attachment to note target subfolder
        tgt = get_converted_root_path().resolve() / relpath
        tgt.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, tgt)

    # add separated attachment data to note
    if images:
        note['images'] = images
    if assets:
        note['assets'] = assets

    return note
    
def fix_title(note:dict) -> dict:
    if len(note['title']) == 0:
        note['title'] = note['created_at'].strftime('%Y-%m-%d_%H%M%S')
        logger.debug('setting empty title to created timestamp')
    return note

def render_note_to_markdown(note: dict) -> str:
    rendered = render.get_note_markdown(note)
    note_filename = slugify(note['title'])
    note_filename = Path(get_converted_root_path() / note_filename).with_suffix('.md')
    write_markdown_file(rendered,note_filename)
    return note_filename

def convert_usec_to_datetime(usec: int) -> datetime:
    rtn = datetime.fromtimestamp(timedelta(microseconds = usec).total_seconds())
    return rtn

def write_markdown_file(contents: str, target: Path) -> None:
    with open(target, 'w+', encoding="utf-8") as outfile:
        outfile.write(contents)

def create_tag_toc(brief_notes: List[dict]):
    target = Path(kconfig['tag_toc_file']).with_suffix('.md').absolute()
    data_by_tag, uncategorized_notes = organize_notes_by_tags(brief_notes, target)
    # reorg data into supertag -> tag -> notes
    reorganized_data = {
        supertag: {tag_name: tag_data for tag_name, tag_data in data_by_tag.items() if tag_data['supertag'] == supertag}
        for supertag in set(tag_data['supertag'] for tag_data in data_by_tag.values())
    }
    sort_and_generate_markdown(reorganized_data, target)

def organize_notes_by_tags(brief_notes, target):
    data_by_tag = {}
    uncategorized_notes = []

    for note in brief_notes:
        note['note_path'] = str(Path(note['note_path']).absolute().relative_to(target.parent))
        has_category_tag = False

        for tag in note['tags']:
            tag_name = tag.replace('\\#', '')
            supertag = get_supertag(tag_name)
            has_category_tag = has_category_tag or (supertag == 'Category')

            if tag_name not in data_by_tag:
                data_by_tag[tag_name] = {'supertag': supertag, 'notes': []}

            data_by_tag[tag_name]['notes'].append(note)

        if not has_category_tag:
            uncategorized_notes.append(note)

    if uncategorized_notes:
        data_by_tag['Uncategorized'] = {'supertag': 'Category', 'notes': uncategorized_notes}

    return data_by_tag, uncategorized_notes

def sort_and_generate_markdown(reorganized_data, target):
    sorted_reorganized_data = {k: dict(sorted(v.items())) for k, v in sorted(reorganized_data.items())}
    rendered = render.get_tagfile_markdown(sorted_reorganized_data)
    write_markdown_file(rendered, target)

def get_supertag(tag_name):
    if tag_name.startswith('created-'):
        return 'Year'
    elif tag_name.startswith('color-'):
        return 'Color'
    else:
        return 'Category'

def main():

    unconverted_notes = get_unconverted_file_paths()
    brief_notes = []
    for n in unconverted_notes:
        brief_notes.append(process_note(n))
    # create a tag directory file
    create_tag_toc(brief_notes)

if __name__ == "__main__":
    main()
