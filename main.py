from pathlib import Path
import logging
from logging.config import fileConfig
import shutil
from typing import List
from slugify import slugify
import render
from appconfig import keep_convert_config as kcfg
import apputils as utils
import tagtoc

fileConfig(Path(__file__).parent / 'logging.ini')
logger = logging.getLogger()

def get_converted_root_path() -> str:
    tgt = Path(kcfg.get('converted_notes_folder')).resolve()
    tgt.mkdir(parents=True,exist_ok=True)
    return tgt

def get_unconverted_file_paths() -> list[Path]:
    src = Path(kcfg.get('unconverted_notes_folder')).resolve()
    rtn = list(src.glob("**/*.json"))
    logger.info(f'Found {len(rtn)} notes to convert.')
    return rtn

def process_note(p: Path) -> dict:
    note = utils.read_json_file(p)
    note['keep_export_file'] = p.name
    note = add_dates(note)
    note = add_tags(note)
    note = fix_title(note)
    note = process_attachments(note, p) if 'attachments' in note else note
    note_path = render_note_to_markdown(note)
    brief_note = {key: note[key] for key in ["createdTimestampUsec", "title", "tags"]}
    # brief_note["tags"] = brief_note["tags"].split(", ")
    brief_note["note_path"] = note_path
    return brief_note

def add_dates(note:dict) -> dict:
    note['created_at'] = utils.convert_usec_to_datetime(note['createdTimestampUsec'])
    note['edited_at'] = utils.convert_usec_to_datetime(note['userEditedTimestampUsec'])
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
    note['tags'] = taglist

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
    utils.write_markdown_file(rendered,note_filename)
    return note_filename


def log_paths():
    for k,v in kcfg.items():
        logger.debug(f'{k} = {Path(v).resolve()}')


def main():
    log_paths()
    unconverted_notes = get_unconverted_file_paths()
    brief_notes = []
    for n in unconverted_notes:
        brief_notes.append(process_note(n))
    logging.debug(f'Converted {len(brief_notes)} notes.')
    # create a tag directory file
    tagtoc.create_tag_toc(brief_notes)

if __name__ == "__main__":
    main()
