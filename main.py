## TODO
## [ ] get Logos notes into here
## [ ] Bible wiki links? Checkout Markdown Scripture ext
## [ ] set up dotenv and argparse 
## [x] parse checklists
## [ ] parse annotations
## [x] parse attachments
##      [x] move images to assets folder under converted note target
## [x] generate a file of tags
##      [ ] include files with no tags in an "Untagged" category
## [ ] create a bookmark-like file out of all links
##      [ ] maybe delete notes that are links only

from pathlib import Path
import json
import logging
import shutil
from datetime import datetime, timedelta
from logging.config import fileConfig
fileConfig('logging.ini')
logger = logging.getLogger()
from typing import List
import judo_utils
import render
from config import keep_convert_config as kconfig

all_tags = {}

def get_converted_root_path() -> str:
    rtn = Path(kconfig['converted_notes_path'])
    rtn.mkdir(parents=True,exist_ok=True)
    logger.debug(f"Markdown target={rtn.absolute()}")
    return rtn

def get_unconverted_paths() -> list[Path]:
    # unconverted root path
    src = Path(kconfig['unconverted_notes_path'])
    logger.debug(f"Getting unconverted Keep notes from {src.absolute()}")
    rtn = src.resolve().glob("**/*.json")
    return rtn

def read_json_file(filepath: Path) -> json:
    with open(filepath) as p:
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
        taglist = [judo_utils.slugify(i['name']) for i in tags]
    # Trashed
    if note['isTrashed']: taglist += ['Trashed']
    # Pinned
    if note['isPinned']: taglist += ['Pinned']
    # color-blue
    if 'color' in note.keys() and note['color'] != 'DEFAULT': taglist += ['color-' + note['color'].lower()]
    # created-2014
    taglist += ['created-' + note['created_at'].strftime('%Y')]
    # build string because jinja whitespace is cra
    note['tags'] = '\#' + ", \#".join(taglist)
    logger.debug(f"adding tags {taglist}")

    # stash tags for the tag file
    all_tags[note['createdTimestampUsec']] = taglist

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
    target = judo_utils.slugify(note['title'])
    target = Path(get_converted_root_path() / target).with_suffix('.md')
    write_markdown_file(rendered,target)
    stash_note_tags(note,target)
    return target

def convert_usec_to_datetime(usec: int) -> datetime:
    rtn = datetime.fromtimestamp(timedelta(microseconds = usec).total_seconds())
    return rtn

def write_markdown_file(contents: str, target: Path) -> None:
    with open(target, 'w+', encoding="utf-8") as outfile:
        outfile.write(contents)

def stash_note_tags(note: dict, target: str):
    ## get the tags at created timestamp into key as target
    all_tags[target] = all_tags[note['createdTimestampUsec']]
    ## delete created timestamp key
    del all_tags[note['createdTimestampUsec']]

def render_tags_to_markdown():
    # reorganize tags from path: [tags] to tag: [paths]
    render_tags = {}
    for tagpath, tags in all_tags.items():
        for tag in tags:
            if tag in render_tags:
                render_tags[tag].append(Path(tagpath).absolute())
            else:
                render_tags[tag] = [tagpath]
    # render reorganized tags to markdown file
    rendered = render.get_tagfile_markdown(render_tags)
    target = kconfig['tag_toc_path_with_filename']
    target = Path(target).with_suffix('.md')
    write_markdown_file(rendered,target)

def render_tags_to_markdown_alt(brief_notes: List[str]):
    # Create a dictionary to organize the data by tag
    data_by_tag = {}
    for note in brief_notes:
        for tag in note['tags']:
            tag_name = tag.replace('\\#', '')  # Remove the '\\#' prefix
            if tag_name not in data_by_tag:
                data_by_tag[tag_name] = []
            data_by_tag[tag_name].append(note)
    # get markdown string
    rendered = render.get_tagfile_markdown(data_by_tag)
    # get markdown file path
    target = kconfig['tag_toc_path_with_filename']
    target = Path(target).with_suffix('.md').absolute()
    # save markdown file
    write_markdown_file(rendered,target)

def main():
    unconverted_notes = get_unconverted_paths()
    brief_notes = []
    for n in unconverted_notes:
        logger.debug(f'processing {n.name}')
        brief_notes.append(process_note(n))
    # create a tag directory file
    # render_tags_to_markdown()
    render_tags_to_markdown_alt(brief_notes)

if __name__ == "__main__":
    main()
