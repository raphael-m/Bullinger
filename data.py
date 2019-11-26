#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# data.py
# Bernard Schroffenegger
# 23th of September, 2019


from Tools.FileCards import *

from Tools.langid import *

PATH_SAMPLE = "Karteikarten/Sample/ocr_sample_100_v2"
PATH = "Karteikarten/OCR"


def main():

    # print(FileSystem.get_file_paths(PATH))
    # BullingerData.analyze_page_sizes()
    # BullingerData.analyze_text_positions()
    # BullingerData.analyze_attribute_positions()
    # BullingerData.extract(PATH_SAMPLE, recursively=False)
    # FileCards.plot_page_sizes(PATH)  # _SAMPLE)
    # print(remove_leading_junk("**++--%% __ ..Hello"))
    # langid.set_languages(['de', 'la', 'el', 'fr'])

    t = [["Absender", "Helen%", "Schmid"], ["Hütten"]]





def remove_leading_junk(s):
    s.replace('_', ' ')
    m, i = re.match(r'^([^\w\d(.]*)(.*)$', s, re.M | re.I), 0
    if m.group(2):
        while i < len(m.group(2)) and m.group(2)[i] == '.': i += 1
        if i >= 3:
            return m.group(2)[(i - 3):].strip()
        else:
            return m.group(2)[i:].strip()


if __name__ == '__main__':

    main()
