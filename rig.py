#!/usr/bin/env python

import youtube_dl
import logging
import IPython

PL = 'https://www.youtube.com/playlist?list=PLwQDSRN0v-fepzxN3g5CVk0T6L4zLejyV'
EM = 'https://www.youtube.com/watch?v=vZG_s7eHrGc' 


logging.basicConfig(level=logging.DEBUG)

blg = logging.getLogger('boopy')

def print_hook(d):
    print('hook', d)

def mr_filter(info_dict):
    print('filter', info_dict['id'], info_dict['title'])
    #return 'Nope! Nope! Nope!'

opts = {
    'format': 'worst',
    'restrictfilenames': True,
    #'quiet': True,
    #'simulate': True,
    'logger': blg,
    #'force_json': True,
    #'dump_single_json': True,
    'writeinfojson': True,
    'progress_hooks': [print_hook],
    'match_filter': mr_filter,
    #'ignoreerrors': True,
    'outtmpl': '%(uploader)s/%(title)s-%(id)s.%(ext)s',
}

ytdl = youtube_dl.YoutubeDL(opts)

pl_info = ytdl.extract_info(PL, download=False)

IPython.embed()
