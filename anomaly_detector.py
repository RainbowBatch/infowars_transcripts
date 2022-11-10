from glob import glob
import chardet

valid_encodings = ['ascii', 'utf-8']

for filename in glob('../infowars/*.txt'):
    with open(filename, 'rb') as rawdata:
        result = chardet.detect(rawdata.read())

    #if result['encoding'] not in valid_encodings:
    #    print(filename, result['encoding'])

    try:
        with open(filename, 'r', encoding=result['encoding'].lower()) as f:
            f_contents = f.read()
            if not f_contents.startswith('['):
                print(filename, f_contents[:100])
    except:
        print(filename, "Unable to open.")