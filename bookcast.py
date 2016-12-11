#!/usr/bin/env python

from feedgen.feed import FeedGenerator
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.easymp4 import EasyMP4
from mutagen.mp4 import MP4

from collections import namedtuple
import ConfigParser
from datetime import datetime, timedelta, tzinfo
from urllib import quote
from glob import glob
import os


PUBLIC_BASE_URL = 'https://dl.dropboxusercontent.com/u/%s/'
FILE_TYPES = ['mp3', 'mp4', 'm4a', 'm4b']
GLOB_PATTERN = '*.m[p4][34ab]'
CFG_SEARCH = [
        os.path.expanduser('~/.bookcast.ini'),
        os.path.expanduser('~/bookcast.ini'),
        '.bookcast.ini',
        'bookcast.ini',
    ]


def get_cfg(paths=CFG_SEARCH):
    full_cfg = ConfigParser.SafeConfigParser()
    full_cfg.read(paths)
    section = 'DEFAULTS'
    options = full_cfg.options(section)
    CFG = namedtuple('CFG', options)
    return CFG(**{k: full_cfg.get(section, k) for k in options})


class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return timedelta(0)


def get_tags(fp):
    if fp.endswith('mp3'):
        return EasyID3(fp)
    return EasyMP4(fp).tags


def get_length(fp):
    if fp.endswith('mp3'):
        l = MP3(fp).info.length
    else:
        l = MP4(fp).info.length
    return str(int(l))


def populate_feedgen(fg, path_base, url_base):
    def isdir(name):
        return os.path.isdir(os.path.join(path_base, name))
    folders = [d for d in os.listdir(path_base) if isdir(d)]
    i = 0
    d = datetime.now(UTC())
    dt = timedelta(1)
    for folder in folders:
        search_path = os.path.join(path_base, folder, GLOB_PATTERN)
        files = [f for f in glob(search_path) if f[-3:] in FILE_TYPES]
        for f in files:
            i += 1
            d -= dt
            file_rel_path = f[len(path_base):]
            url = url_base + quote(file_rel_path)
            tags = get_tags(f)
            length = get_length(f)
            fe = fg.add_entry()
            fe.id(url)
            if 'title' in tags:
                title = tags['title'][0]
            else:
                print 'No title on %s' % f
                print tags
                title = tags['album'][0]
            fe.title(title)
            fe.description(tags['album'][0])
            fe.enclosure(url=url, length=length, type='audio/mpeg')
            fe.podcast.itunes_duration(length)
            fe.podcast.itunes_order(i)
            fe.pubdate(d)


cfg = get_cfg()
url_base = PUBLIC_BASE_URL % cfg.dropbox_uid
path_base = os.path.expanduser(cfg.dropbox_public_path)
fg = FeedGenerator()
fg.load_extension('podcast')
# fg.podcast.itunes_category('Technology', 'Podcasting')
fg.title(cfg.title)
fg.link(href=cfg.link, rel='alternate')
fg.description(cfg.description)
if cfg.logo:
    fg.logo(url_base + quote(cfg.logo))
populate_feedgen(fg, path_base, url_base)

fg.rss_str(pretty=True)
fg.rss_file(os.path.join(path_base, 'podcast.xml'))
print 'Published to:', url_base + 'podcast.xml'
