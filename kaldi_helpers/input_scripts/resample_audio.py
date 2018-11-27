#!/usr/bin/python3

"""
Copyright Ola Olsson 2018
Convert audio to 16 bit 16k mono WAV
"""

import argparse
import glob
import os
import subprocess
import threading
from multiprocessing.dummy import Pool
from shutil import move


parser = argparse.ArgumentParser(description="This script will silence a wave file based on annotations in Elan tier ")
parser.add_argument('-c', '--corpus', help='Directory of audio and eaf files', type=str, default='../input/data')
parser.add_argument('-o', '--overwrite', help='Write over existing files', type=str, default='yes')
args = parser.parse_args()

overwrite = args.overwrite
g_baseDir = args.corpus
g_audioExts = ["*.wav"]
g_soxPath = "/usr/bin/sox"
g_tmpDir = "tmp"


def find_files_by_extension(set_of_all_files, extensions):
    res = []
    for f in set_of_all_files:
        name, ext = os.path.splitext(f)
        if ("*" + ext.lower()) in extensions:
            res.append(f)
    return res


def join_norm(p1, p2):
    tmp = os.path.join(os.path.normpath(p1), os.path.normpath(p2))
    return os.path.normpath(tmp)


def process_item(item):
    print("processing")
    inInd, ia = item
    global g_tmpDir
    global g_processLock
    global g_outputStep

    with g_processLock:
        print("[%d, %d]%s" % (g_outputStep, inInd, ia))
        g_outputStep += 1

    input_name = os.path.normpath(ia)
    # 1. convert using sox

    in_dir, name = os.path.split(ia)
    print(in_dir)
    base_name, ext = os.path.splitext(name)
    out_directory = os.path.join(in_dir, g_tmpDir)
    print(out_directory)
    tmpFolders.add(out_directory)

    # avoid race condition
    with g_processLock:
        if not os.path.exists(out_directory):
            os.makedirs(out_directory)

    tmp_audio_name = join_norm(out_directory, "%s.%s" % (base_name, "wav"))

    if not os.path.exists(tmp_audio_name):
        cmdLn = [g_soxPath, input_name, "-b", "16", "-c", "1", "-r", "44.1k", "-t", "wav", tmp_audio_name]
        subprocess.call(cmdLn)
    return tmp_audio_name


allFilesInDir = set(glob.glob(os.path.join(g_baseDir, "**"), recursive=True))
inputAudio = find_files_by_extension(allFilesInDir, set(g_audioExts))
g_processLock = threading.Lock()
g_outputStep = 0

outputs = []
tmpFolders = set([])

# Single thread
# outputs.append(processItem(ia))

# Multithread
with Pool() as p:
    outputs = p.map(process_item, enumerate(inputAudio))

    if overwrite == 'yes':
        # Replace original files
        for f in outputs:
            fname = os.path.basename(f)
            parent = os.path.dirname(os.path.dirname(f))
            move(f, os.path.join(parent, fname))
        # Clean up tmp folders
        for d in tmpFolders:
            os.rmdir(d)