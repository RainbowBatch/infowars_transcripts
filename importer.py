import autosub
from glob import glob
import parse
from os.path import exists

LINE_TEMPLATE = '[%s]  %s\n'


def reformat_vtt(contents):
    result = ''
    for block in contents.split('\n\n'):
        if block.strip() == 'WEBVTT':
            continue
        if block.strip() == '':
            continue

        tss, text = block.split('\n')
        result += LINE_TEMPLATE % (tss.strip(), text.strip())
    return result


for fname in glob('../infowars_tmp/*.mp3.vtt'):
    episode_slug = fname.split('\\')[-1][:-8]

    new_fname = r'%s.txt' % episode_slug

    print(new_fname)

    if exists(new_fname):
        try:
            with open(new_fname, 'r') as f:
                f_contents = f.read()
                if f_contents.startswith('['):
                    print("Skipping", fname)
                    continue
        except:
            pass

    with open(fname, 'r') as old_file, open(new_fname, 'w') as new_file:
        new_file.write(
            reformat_vtt(old_file.read()).encode('utf-8')
        )
