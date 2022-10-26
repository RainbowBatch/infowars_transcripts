import autosub
from glob import glob
import parse
from os.path import exists

for fname in glob('../infowars_tmp/*.mp3.txt'):
    episode_slug = fname.split('\\')[-1][:-8]

    new_fname = r'%s.txt' % episode_slug

    print(new_fname)

    if exists(new_fname):
        print("Skipping", fname)
        continue

    with open(fname,'r') as old_file, open(new_fname,'w') as new_file:
        new_file.write(old_file.read())