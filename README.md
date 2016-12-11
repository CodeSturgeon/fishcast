# Bookcast
Bookcast makes podcast XML files for folders of audio files in Dropbox public folders.

There is nothing magical about the use of Dropbox, it was just to hand. Other services could be used with minor modification.

## Why?
Some people do not like to use iTunes. Some people have audio books in file form they wish to listen to on their iOS devices. Apple do not like management of audio files to happen outside of a sandboxed app, or iTunes.

The features of podcast apps are very similar to the features required for audiobooks. Hijacking podcasting apps to play audiobooks seemed like the simplest solution to the problem.

## How?
Bookcast scans the first level directories of a Dropbox public folder for audio files. Files it finds will be listed as episodes of the podcast.

The title of the episode will be the title or album tag of audio file. The description of the episode will be the album tag of the audio file.

The publish time of the episodes will be set in decreasing increments from now() in the order that the files were found. This should make for a sane listing of the podcast.

## Setup
Clone this repo and have python2 availiable.

Install the libraries in requirements.txt with pip or whatever.

Copy the bookcast_example.ini to your home folder or your working directory and rename it to either bookcast.ini or .bookcast.ini.

Edit the ini to provide the user id of your Dropbox account. The easiest way I've found of getting that is pulling it from the public URL of your Dropbox Public folder.

You should also set (or blank) the name of the logo file and check the local path to your Public directory.

Run ./bookcast.py

You should now be able to subscribe to your books as a podcast here:
    
    https://dl.dropboxusercontent.com/u/YOUR_USER_ID/podcast.xml
