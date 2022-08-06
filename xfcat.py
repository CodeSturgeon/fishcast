#!/usr/bin/env python

import os
from datetime import datetime, timedelta, tzinfo
from urllib.parse import quote_plus
from pathlib import Path
import json

import yaml
from feedgen.feed import FeedGenerator
import mutagen


class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return timedelta(0)

def path_url(file_path):
    return base_url + '/' + '/'.join(map(quote_plus, file_path.parts))

base_url = 'https://s3-us-west-2.amazonaws.com/fishcast/ab'
data_dir = Path('.').expanduser()
#data_dir = Path('~/Desktop/vid/').expanduser()
os.chdir(data_dir)
start_dir = Path('.')
time_step = timedelta(1)

for cat_file in start_dir.glob('**/*fcat.yml'):
    feed_dir = cat_file.parent
    catalog = yaml.safe_load(open(cat_file))

    # Setup the feed
    feed_gen = FeedGenerator()
    feed_gen.load_extension('podcast')
    feed_gen.title(catalog['title'])
    if 'description' in catalog:
        feed_gen.description(catalog['description'])
    else:
        feed_gen.description(catalog['title'])
    if 'url' in catalog:
        feed_gen.link(href=catalog['url'], rel='alternate')
    else:
        feed_gen.link(href='http://google.com', rel='alternate')
    if 'image_url' in catalog:
        feed_gen.logo(catalog['image_url'])
    elif 'image_file' in catalog:
        feed_gen.logo(path_url(feed_dir / catalog['image_file']))

    # Setup the file loop variables
    tag_for_title = catalog.get('tag_for_title') or 'title'
    tag_for_description = catalog.get('tag_for_description') or 'comment'
    pub_time = datetime.now(UTC())

    file_paths = sorted(feed_dir.glob('*.m[p4][ab34]'))
    for file_path in file_paths:
        meta = mutagen.File(file_path, easy=True)
        title = meta.tags[tag_for_title][0]
        desc = meta.tags[tag_for_description][0]
        duration = str(int(meta.info.length))
        size = file_path.stat().st_size
        if catalog.get('video'):
            mime_type = 'video/mp4'
        else:
            mime_type = meta.mime[0]
        pub_time -= time_step

        url = path_url(file_path)

        entry = feed_gen.add_entry()
        entry.id(url)
        entry.title(title)
        entry.description(desc)
        entry.enclosure(url=url, length=str(size), type=mime_type)
        entry.podcast.itunes_duration(duration)
        entry.pubDate(pub_time)

    s = feed_gen.rss_str(pretty=True).decode("utf-8")
    feed_filename = f'{feed_dir.name}.xml'.replace(' ', '_')
    print(feed_filename)
    open(feed_filename, 'w').write(s)
