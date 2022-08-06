#!/usr/bin/env python
'''Playlist to ficast catalog file'''
from pathlib import Path
import json

import yaml

start_dir = Path('.')

for pl_info_path in start_dir.glob('**/playlist.info.json'):
    pl_info = json.load(open(pl_info_path))
    feed_dir = pl_info_path.parent
    cat_file = feed_dir / '_fcat.yml'
    if cat_file.exists():
        catalog = yaml.safe_load(open(cat_file)) or {}
    else:
        catalog = {}
    catalog['title'] = pl_info['title']
    catalog['description'] = 'YouTube Playlist'
    catalog['url'] = pl_info['webpage_url']
    # Deleted entries show up as None
    first_entry = [e for e in pl_info['entries']
                   if e is not None and e['playlist_index'] == 1][0]
    catalog['image_url'] = first_entry['thumbnails'][0]['url']
    catalog['video'] = True
    yaml.safe_dump(catalog, open(cat_file, 'w'))
    print(catalog)
