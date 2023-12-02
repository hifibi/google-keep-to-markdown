from pathlib import Path
import apputils as utils
import render
from appconfig import keep_convert_config as kcfg
from typing import List

def create_tag_toc(brief_notes: List[dict]):
    target = Path(kcfg.get('tag_toc_file')).resolve()
    data_by_tag = organize_notes_by_tags(brief_notes, target)
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
        note['note_path'] = str(Path(note['note_path']).resolve().relative_to(target.parent))
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

    return data_by_tag

def sort_and_generate_markdown(reorganized_data, target):
    sorted_reorganized_data = {k: dict(sorted(v.items())) for k, v in sorted(reorganized_data.items())}
    rendered = render.get_tagfile_markdown(sorted_reorganized_data)
    utils.write_json_toc(sorted_reorganized_data, target.with_suffix('.json'))
    utils.write_markdown_file(rendered, target)



def get_supertag(tag_name):
    if tag_name.startswith('created-'):
        return 'Year'
    elif tag_name.startswith('color-'):
        return 'Color'
    else:
        return 'Category'

