#!/usr/bin/env python3
# coding: utf-8

#Code to update the metadata of a sound file

import argparse
parser = argparse.ArgumentParser(description="Update metadata of sound file")
parser.add_argument("filename",type=str)
parser.add_argument("--tracknumber", type=str)
parser.add_argument("--tracktotal", type=str)
parser.add_argument("--location", type=str)
parser.add_argument("--comment", type=str)

args = parser.parse_args()

import mutagen

#Edit the audio metadata
##This needs to be updated for the different formats, opus, flac, ogg
meta = mutagen.File(args.filename)
meta["tracknumber"] = args.tracknumber
meta["tracktotal"] = args.tracktotal
meta["location"] = args.location
meta["comment"] = args.comment
#print(meta.pprint())
meta.save()
    
    