from glob import glob
import chardet
from mutagen.mp3 import MP3
import os
import datetime
from tqdm import tqdm
import parse
from box import Box
import numpy as np
from thefuzz import fuzz
import matplotlib.pyplot as plt
import pandas as pd


valid_encodings = ['ascii', 'utf-8']
spurious_encoding = [
    'EUC-JP',
    'ISO-8859-1',
    'Windows-1252',
    'Windows-1254',
]

audio_directory = '../../audio_files/infowars/'


def parse_timestamp(ts_str):
    ts_str = ts_str.strip()

    pattern = '%M:%S'
    if ts_str.count(':') == 2:
        pattern = '%H:' + pattern
    if ',' in ts_str:
        pattern += ",%f"
    if '.' in ts_str:
        pattern += ".%f"

    ts_dt = datetime.datetime.strptime(ts_str, pattern)
    ts_seconds = datetime.timedelta(hours=ts_dt.hour, minutes=ts_dt.minute,
                                    seconds=ts_dt.second, microseconds=ts_dt.microsecond).total_seconds()

    return ts_seconds


def format_timestamp(ts_seconds):
    if pd.isna(ts_seconds):
        return None
    hours, remainder = divmod(ts_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds, microseconds = divmod(seconds, 1)
    return '{:02}:{:02}:{:02}.{}'.format(int(hours), int(minutes), int(seconds), str(microseconds).split('.')[-1][:3].ljust(3, '0'))


def parse_whisper_txt(transcript_text):
    transcript_text = transcript_text.replace('\x00', '').replace('ÿþ', '')
    blocks = transcript_text.split('\n')

    transcript_blocks = []

    parse_template = "[{} --> {}] {}"

    for block in blocks:
        line = block.strip()
        if len(line) == 0:
            continue
        start_timestamp, end_timestamp, text = parse.parse(
            parse_template, line)

        transcript_blocks.append(Box({
            'start_timestamp': parse_timestamp(start_timestamp),
            'end_timestamp': parse_timestamp(end_timestamp),
            'text': text.strip(),
        }))
    return transcript_blocks


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


for filename in glob('../infowars/*.txt'):
    with open(filename, 'rb') as rawdata:
        result = chardet.detect(rawdata.read())

    if result['encoding'] not in valid_encodings:
        if result['encoding'] in spurious_encoding:
            pass
        else:
            print(filename, "Weird encoding reported by chardet:",
                  result['encoding'])

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            f_contents = f.read()
    except:
        print(filename, "Unable to open.")
        f_contents = None

    #try:
    if True:
        transcript_blocks = parse_whisper_txt(f_contents)
        transcript_texts = [block.text for block in transcript_blocks]

        N = len(transcript_texts)
        W = 30
        D2 = np.zeros(N - W)

        for i in range(N):
            ds = []
            for j in range(i, i+W):
                if j >= N:
                    continue
                d = fuzz.partial_ratio(
                    transcript_texts[i].lower(), transcript_texts[j].lower())
                ds.append(d)
            if i < len(D2):
                D2[i] = 1 - np.mean(ds)/100

        low_distance_idxs = list(np.where(D2 < 0.2)[0])

        if len(low_distance_idxs) > 0:
            duration = transcript_blocks[max(
                low_distance_idxs)].end_timestamp - transcript_blocks[min(low_distance_idxs)].start_timestamp
            badness = min(D2)
            if duration > 60:
                print(filename, "Likely repetitive mistranscriptions between ~%s to ~%s, (badness: %.2f, duration: %s)" % (
                    format_timestamp(transcript_blocks[min(
                        low_distance_idxs)].start_timestamp),
                    format_timestamp(transcript_blocks[max(
                        low_distance_idxs)].end_timestamp),
                    badness,
                    format_timestamp(duration)
                ))
    #except:
    #    print(filename, "Unable to parse transcript. Likely formatting error.")
    #    f_contents = None

    if f_contents is not None:
        if 'Traceback (most recent call last):' in f_contents:
            print(filename, "Python traceback in transcript")
            continue
        if '\0' in f_contents:
            print(filename, "Possible UTF-16 file.")
            continue
        if not f_contents.startswith('['):
            print(filename, "Malformed first line:", repr(f_contents[:100]))
            continue

        last_ts_str = f_contents.strip().split(
            '\n')[-1].split(']')[0].split(' --> ')[1]
        last_ts = parse_timestamp(last_ts_str)
    else:
        last_ts = None

    if last_ts is not None:
        # TODO(woursler): Fix this to use pathlib.
        audio_filename = audio_directory + \
            filename.split('\\')[-1][:-4] + '.mp3'
        if os.path.exists(audio_filename):
            audio = MP3(audio_filename)
            t_delta = audio.info.length - last_ts
            if t_delta > 30:  # TODO(woursler): Maybe choose something different?
                print(
                    filename, "Possible truncation (%d seconds unaccounted for)." % int(t_delta))
        else:
            pass  # print("No audio", audio_filename)
