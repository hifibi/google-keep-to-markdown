# HiFiBI Google Notes to Markdown Converter

- Converts .json files from Google Takeout for Keep Notes to Markdown.
- Format Markdown notes with Jinja.
- Converted format is standard Markdown but only tested in Visual Studio Code and on GitHub.

## How to Use

- Clone the repo.
- Put Google Keep data from Takeout into `./notes_unconverted`. It can be at any subfolder level. All JSON files in `./notes_unconverted` will be assumed to be `Keep no`tes.
- Run `main.py`.
- Find a table of contents by tag at `./notes_converted/tag_index.md`.
- If you re-run the script, converted notes will be overwritten but not cleaned up.
- All paths are relative to location of `main.py`.

## Export Google Keep Notes

Google's tool for exporting Keep Notes and any other Google data is called Google Takeout. Read [this help document](https://support.google.com/accounts/answer/3024190?hl=en) or search Google Takeout to learn how to get your data exported. The export will include the JSON files exactly as required by this tool. You just need to put them in a folder somewhere.