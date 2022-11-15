from glob import glob
import chardet
from mutagen.mp3 import MP3
import os
import datetime

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


for filename in glob('../infowars/*.txt'):
    with open(filename, 'rb') as rawdata:
        result = chardet.detect(rawdata.read())

    if result['encoding'] not in valid_encodings:
        if result['encoding'] in spurious_encoding:
            pass
        else:
            print(filename, "Weird encoding reported by chardet:", result['encoding'])

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            f_contents = f.read()
    except:
        print(filename, "Unable to open.")
        f_contents = None

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
            if t_delta > 30: # TODO(woursler): Maybe choose something different?
                print(filename, "Possible truncation (%d seconds unaccounted for)." % int(t_delta))
        else:
            pass # print("No audio", audio_filename)
