#!/usr/bin/env python
import argparse
import sys
import logging

from configparser import ConfigParser
from datetime import datetime, tzinfo, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET

import youtube_dl
from feedgen.feed import FeedGenerator

CFG_PATHS = map(lambda p: Path(p).expanduser(), ('~/.ytm.ini', '.ytm.ini'))

CHANGE_TITLE = 'CHANGE ME!'
DEFAULT_DESC = 'Mirrored playlist'


def output(*msgs):
    '''User output abstraction'''
    print(' '.join(map(str, msgs)))


class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return timedelta(0)


def xml_path(info_dict):
    '''Determine path for a playlist'''
    raw = info_dict['uploader'] + ' - ' + info_dict['playlist_title'] + '.xml'
    return Path(youtube_dl.utils.sanitize_filename(raw, restricted=True))


def fg_from_xml(feed_path):
    '''Load an RSS feed and constructs a new feed_gen from it'''
    guids = []
    tree = ET.parse(feed_path)
    feed_gen = FeedGenerator()
    feed_gen.load_extension('podcast')
    feed_gen.title(tree.findtext('.//title'))
    feed_gen.link(href=tree.findtext('.//link'))
    feed_gen.logo(tree.findtext('.//image/url'))
    feed_gen.description(tree.findtext('.//description'))
    for i in tree.findall('.//item'):
        entry = feed_gen.add_entry()
        guids.append(i.findtext('.//guid'))
        entry.id(i.findtext('.//guid'))
        entry.title(i.findtext('.//title'))
        entry.description(i.findtext('.//description'))
        enc = i.find('.//enclosure')
        entry.enclosure(
            url=enc.attrib['url'],
            length=enc.attrib['length'],
            type=enc.attrib['type'])
        entry.podcast.itunes_duration(
            i.findtext(
                './/{http://www.itunes.com/dtds/podcast-1.0.dtd}duration'))
        entry.pubDate(i.findtext('.//pubDate'))
    return feed_gen, guids


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('feed_file', nargs='?', help='Path to the rss xml')
parser.add_argument('-p', '--playlist', help='URL of the playlist')
parser.add_argument('-l', '--list', action='store_true',
                    help='Only list, not download')
parser.add_argument('-r', '--reverse', action='store_true',
                    help='Reverse the playlist for processing')
parser.add_argument('-s', '--start', type=int, default=1,
                    help='Playlist item to start at')
parser.add_argument('-e', '--end', type=int, default=None,
                    help='Playlist item to end at')

args = parser.parse_args()
logging.basicConfig(level=logging.DEBUG)

cfg = ConfigParser()
hits = cfg.read(CFG_PATHS)
if not hits:
    sys.exit(f'Failed to find ini file in these locations: {CFG_PATHS}')
try:
    url_prefix = cfg['ytm']['url_prefix']
except KeyError:
    sys.exit(f'Did not find `url_prefix` in `[ytm]` section')


# Create feed_gen
if args.feed_file is not None:
    feed_path = Path(args.feed_file)
    feed_gen, known_ids = fg_from_xml(feed_path)
else:
    if args.playlist is None:
        sys.exit('Must specify --playlist when not supplying xml feed')
    known_ids = []
    feed_gen = FeedGenerator()
    feed_gen.load_extension('podcast')
    feed_gen.title(CHANGE_TITLE)
    feed_gen.link(href=args.playlist)
    feed_gen.description(DEFAULT_DESC)

pl_url = feed_gen.link()[0]['href']


# setup ytdl base options
ytdl_opts = {
    'format': 'best',
    'restrictfilenames': True,
    'quiet': True,
    # 'logger': logging.getLogger('ytdl'),
    'writeinfojson': True,
    'ignoreerrors': True,  # Needed for deleted items in playlist
    'outtmpl': '%(uploader)s/%(title)s-%(id)s.%(ext)s',
    'playliststart': args.start,
    'playlistend': args.end,
}

if args.reverse:
    ytdl_opts['playlistreverse'] = True


# full run or just a quick peek?
if args.list:
    with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
        info = ytdl.extract_info(pl_url)
    for e in info['entries']:
        output('{playlist_index:03d} [{upload_date}] {title}'.format(**e))
    sys.exit()


# setup hooks
_INFO_DICT = None


def filter_and_save(info_dict):
    '''ytdl filter function

    Stash info_dict in global and check global known_ids, skipping if found.
    '''
    global _INFO_DICT
    _INFO_DICT = info_dict
    if info_dict['id'] in known_ids:
        output('Skipping ', info_dict['title'])
        return "Already in feed"


def add_when_done(status_dict):
    '''ytdl progress hook

    Add info from global info_dict to global feed_gen on download complete.
    '''
    if status_dict['status'] == 'finished':
        output('DONE ', status_dict['filename'])
        entry = feed_gen.add_entry()
        entry.id(_INFO_DICT['id'])
        entry.title(_INFO_DICT['title'])
        entry.description(_INFO_DICT['description'])
        entry.enclosure(
                url=url_prefix+status_dict['filename'],
                length=str(status_dict['total_bytes']),
                type='video/mp4')
        entry.podcast.itunes_duration(_INFO_DICT['duration'])
        entry.pubDate(datetime(
            *map(int, [
                _INFO_DICT['upload_date'][:4],
                _INFO_DICT['upload_date'][4:6],
                _INFO_DICT['upload_date'][6:]
            ]), tzinfo=UTC()
        ))

        if feed_gen.title() == CHANGE_TITLE:
            global feed_path
            feed_path = xml_path(_INFO_DICT)
            feed_gen.title(_INFO_DICT['playlist_title'])
            feed_gen.logo(_INFO_DICT['thumbnails'][0]['url'])
            output('Setting output path: ', feed_path)
        feed_gen.rss_file(str(feed_path), pretty=True)


ytdl_opts['match_filter'] = filter_and_save
ytdl_opts['progress_hooks'] = [add_when_done]

# import IPython; IPython.embed()  # NOQA
# sys.exit()

# download
output('Starting run')
with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
    ytdl.download([pl_url])
