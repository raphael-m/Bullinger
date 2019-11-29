#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# BullingerData.py
# Bernard Schroffenegger
# 6th of October, 2019

import statistics
import re
from datetime import datetime

from Tools.OCR1 import *
from Tools.OCR2 import *
from Tools.Plots import ScatterPlot
from Tools.FileSystem import FileSystem
from Tools.Dictionaries import ListDict, CountDict
from Tools.Langid import *
from App.models import *

SN = 's.n.'  # sine nomine
SL = 's.l.'  # sine loco
SD = 's.d.'  # sine die
ADMIN = 'Admin'  # username


class BullingerData:

    ROUND = 0
    SCHEMA_STATS = ['axis', 'mean', 'dev']

    PATH_V1 = 'Karteikarten/ocr_sample_100_v1'
    PATH_V2 = 'Karteikarten/ocr_sample_100_v2'

    IMG_PAGE_DIM_1 = 'Dokumentation/tex/Bilder/ocr_page_sizes_1.png'
    IMG_PAGE_DIM_2 = 'Dokumentation/tex/Bilder/ocr_page_sizes_2.png'
    IMG_TEXT_POSITIONS = 'Dokumentation/tex/Bilder/ocr_text_positions.png'  # all
    IMG_ATTRIBUTES_2 = "Dokumentation/tex/Bilder/ocr_attributes_2.png"  # attr. separation
    IMG_ATTRIBUTES_3 = "Dokumentation/tex/Bilder/ocr_attributes_3.png"  # scaled
    IMG_ATTRIBUTES_4 = "Dokumentation/tex/Bilder/ocr_attributes_4.png"  # content
    IMG_ATTRIBUTES_5 = "Dokumentation/tex/Bilder/ocr_attributes_5.png"  # ...

    ATTRIBUTES = ["Datum", "Absender", "Empfänger", "Autograph", "Kopie", "Photokopie",
                  "Standort", "Bull.", "Corr.", "Sign.", "Abschrift", "Umfang", "Sprache",
                  "Literatur", "Gedruckt", "Bemerkungen"]

    AVG_PAGE_SIZE = [9860, 6978]
    AVG_PAGE_DEV = [11, 10]

    def __init__(self):
        pass

    @staticmethod
    def export(dir_path, database):
        card_nr, n_gram_max, threshold = 0, 4, 0.3
        n_grams_bullinger = [BullingerData.create_n_gram_dict(i, "Bullinger") for i in range(1, n_gram_max)]
        database.add(Person(name="Bullinger", title="", forename="Heinrich", place="Zürich", user=ADMIN, time=datetime.now()))
        database.commit()
        id_bullinger = Person.query.filter_by(name="Bullinger").first().id
        for path in FileSystem.get_file_paths(dir_path, recursively=False):
            card_nr += 1
            T0 = datetime.now()
            print(card_nr, path)
            data = BullingerData.get_data_as_dict(path)
            if data:

                # Datum
                if "Datum" in data:
                    BullingerData.extract_date(card_nr, [i for j in data["Datum"] for i in j], database)
                else:
                    database.add(Datum(id_brief=card_nr, year_a=SD, month_a=SD, day_a=SD, user=ADMIN, time=T0))

                # Absender/Empfänger
                if BullingerData.is_bullinger_sender(data, n_grams_bullinger, n_gram_max, threshold):
                    # Bullinger ist Absender
                    database.add(Absender(id_brief=card_nr, id_person=id_bullinger, user=ADMIN, time=T0))
                    e = BullingerData.analyze_address(data["Empfänger"])
                    known = Person.query.filter_by(name=e[0], vorname=e[1], titel=e[4], ort=e[2]).first()
                    if not known:
                        database.add(Person(title=e[4], name=e[0], forename=e[1], place=e[2], user=ADMIN, time=T0))
                    ref = Person.query.filter_by(name=e[0], vorname=e[1], titel=e[4], ort=e[2]).first().id
                    database.add(Empfaenger(id_brief=card_nr, id_person=ref, remark=e[3], user=ADMIN, time=T0))
                else:
                    # Bullinger ist Empfänger
                    database.add(Empfaenger(id_brief=card_nr, id_person=id_bullinger, user=ADMIN, time=T0))
                    a = BullingerData.analyze_address(data["Absender"])
                    known = Person.query.filter_by(name=a[0], vorname=a[1], ort=a[2], titel=a[4]).first()
                    if not known:
                        database.add(Person(title=a[4], name=a[0], forename=a[1], place=a[2], user=ADMIN, time=T0))
                        database.commit()
                    ref = Person.query.filter_by(name=a[0], vorname=a[1], ort=a[2], titel=a[4]).first().id
                    database.add(Absender(id_brief=card_nr, id_person=ref, remark=a[3], user=ADMIN, time=T0))

                # Patterns for attributnames
                p_standort = '[Ss$][tlf1I|]a[nm]d[o0°O]r[tlf1I]'
                p_signatur = '[Ss][il][g8B]n[.]?'
                p_umfang = '[Uu][mn][ftl]a[nm][g8B]'

                # Autograph
                autograph, is_zsta = Autograph(id_brief=card_nr, user=ADMIN, time=T0), False
                standort_baselines, baselines_signatur, is_typewriter = None, None, False
                standort_str, standort, signatur_str, signatur = '', '', '', ''
                umfang_baselines, umfang_str, umfang = '', '', ''
                if "Standort A" in data:
                    standort_baselines = data["Standort A"]
                    standort_str = [t for s in data["Standort A"] for t in s]
                    standort_str = re.sub(p_standort, '', ' '.join(standort_str))
                    standort = BullingerData.clean_str(standort_str)
                if "Sign. A" in data:
                    baselines_signatur = data["Sign. A"]
                    signatur_str = [t for s in data["Sign. A"] for t in s]
                    signatur_str = re.sub(p_signatur, '', ' '.join(signatur_str))
                    signatur = BullingerData.clean_str(signatur_str)
                if "Umfang A" in data:
                    umfang_baselines = data["Umfang A"]
                    umfang_str = [t for s in data["Umfang A"] for t in s]
                    umfang_str = re.sub(p_umfang, '', ' '.join(umfang_str))
                    umfang = ' '.join(umfang_str)

                # 1. Typewriter Data
                if BullingerData.is_typewriter(standort_baselines) or BullingerData.is_typewriter(baselines_signatur):
                    if standort:
                        d = standort + signatur + umfang
                        m = re.match("(.*)StA\s(E[\d\s,]*)([^\d]*)", d)
                        m = re.match("(.*)StA\s(A[\d\s,]*)([^\d]*)", d) if not m else None
                        m = re.match("(.*)ZB\s([MsS\d\s,]*)([^\d]*)", d) if not m else None
                        autograph.standort = m.group(1) if m else standort
                        autograph.signatur = ' '.join([m.group(2), ]) if m else signatur
                        autograph.umfang = m.group(3) if m else umfang

                elif BullingerData.check_stdort_for_zuerich_sta(standort) or\
                        BullingerData.check_sign_for_zuerich_sta(signatur):
                        autograph.standort, is_zsta = "Zürich StA", True
                        number = re.sub(r'[^\d,f]', '', signatur+umfang)
                        n_I = BullingerData.how_many_I(signatur)
                        autograph.signatur = ' '.join(['E', n_I, number.strip(',')])

                elif BullingerData.check_standort_ZZB(standort):
                    autograph.standort = "Zürich ZB"
                    numbers = re.sub(r'[^\d,]', '', standort+signatur+umfang)
                    autograph.signatur = ''.join('Ms S ' + numbers)

                elif len(standort_str) or len(signatur_str) or len(umfang_str):
                    autograph.standort = "Zürich"

                if autograph.standort or autograph.signatur:
                    database.add(autograph)



                # Kopie
                kopie = Kopie(id_brief=card_nr, user=ADMIN, time=T0)
                standort_baselines, baselines_signatur, is_typewriter = None, None, False
                standort_str, standort, signatur_str, signatur = '', '', '', ''
                umfang_baselines, umfang_str, umfang = '', '', ''
                if "Standort B" in data:
                    standort_baselines = data["Standort B"]
                    standort_str = [t for s in data["Standort B"] for t in s]
                    standort_str = re.sub(p_standort, '', ' '.join(standort_str))
                    standort = BullingerData.clean_str(standort_str)
                if "Sign. B" in data:
                    baselines_signatur = data["Sign. B"]
                    signatur_str = [t for s in data["Sign. B"] for t in s]
                    signatur_str = re.sub(p_signatur, '', ' '.join(signatur_str))
                    signatur = BullingerData.clean_str(signatur_str)
                if "Umfang B" in data:
                    umfang_baselines = data["Umfang B"]
                    umfang_str = [t for s in data["Umfang B"] for t in s]
                    umfang_str = re.sub(p_umfang, '', ' '.join(umfang_str))
                    umfang = ' '.join(umfang_str)

                # Typewriter
                if BullingerData.is_typewriter(standort_baselines) or BullingerData.is_typewriter(baselines_signatur):
                    if standort:
                        d = standort + signatur + umfang
                        m = re.match("(.*)StA\s(E[\d\s,]*)([^\d]*)", d)
                        m = re.match("(.*)StA\s(A[\d\s,]*)([^\d]*)", d) if not m else None
                        m = re.match("(.*)ZB\s([MsSF\d\s,]*)([^\d]*)", d) if not m else None
                        kopie.standort = m.group(1) if m else standort
                        kopie.signatur = ' '.join([m.group(2), ]) if m else signatur
                        kopie.umfang = m.group(3) if m else umfang

                # Zürich StA
                elif BullingerData.check_stdort_for_zuerich_sta(standort_str)\
                        or BullingerData.check_sign_for_zuerich_sta(signatur):
                        kopie.standort = "Zürich StA"
                        if signatur:
                            number = re.sub(r'[^\d,]*f*', '', signatur+umfang)
                            n_I = BullingerData.how_many_I(signatur)
                            kopie.signatur = ''.join('E '+n_I+' '+number.strip(','))

                # ZZB
                elif is_zsta and (len(standort_str) > 0 or len(signatur_str+umfang_str) > 0):
                    kopie.standort = "Zürich ZB"
                    numbers = re.sub(r'[^\d,]', '', standort+signatur+umfang)
                    kopie.signatur = ''.join('Ms S ' + numbers)

                # Zürich ?
                elif len(standort_str) or len(signatur_str) or len(umfang_str):
                    kopie.standort = "Zürich"

                if kopie.signatur or kopie.standort:
                    database.add(kopie)

                if "Photokopie" in data:
                    photokopie = Photokopie(id_brief=card_nr, user=ADMIN, time=T0)
                    photokopie.standort = ' '.join([t for s in data["Photokopie"] for t in s]).replace('2', 'Z')
                    e = BullingerData.analyze_bull_corr(data["Bull. Corr. A"], photokopie)
                    if e: database.add(photokopie)
                if "Abschrift" in data:
                    abschrift = Abschrift(id_brief=card_nr, user=ADMIN, time=T0)
                    abschrift.standort = ' '.join([t for s in data["Abschrift"] for t in s]).replace('2', 'Z')
                    abschrift.standort = re.sub("Abschrift", '', abschrift.standort)
                    d = BullingerData.analyze_bull_corr(data["Bull. Corr. B"], abschrift)
                    if d: database.add(abschrift)

                if "Literatur" in data:
                    literatur = ' '.join([t for s in data["Literatur"] for t in s])
                    literatur = re.sub("Literatur", '', literatur)
                    if not BullingerData.is_probably_junk(literatur):
                        literatur = ' '.join([BullingerData.clean_str(t) for s in data["Literatur"] for t in s])
                        database.add(Literatur(id_brief=card_nr, literature=literatur, user=ADMIN, time=T0))
                if "Gedruckt" in data:
                    gedruckt = ' '.join([t for s in data["Gedruckt"] for t in s])
                    if not BullingerData.is_probably_junk(gedruckt):
                        gedruckt = ' '.join([BullingerData.clean_str(t) for s in data["Gedruckt"] for t in s])
                        database.add(Gedruckt(id_brief=card_nr, printed=gedruckt, user=ADMIN, time=T0))

                bemerkung = ''
                if 'Bemerkungen' in data:
                    b = Bemerkung(id_brief=card_nr, user=ADMIN, time=T0)
                    remark, concat = list(), [False]
                    for baseline in data["Bemerkungen"]:
                        bl = [BullingerData.clean_str(s) for s in baseline]
                        if len(bl)>0:
                            if "Bemer" in bl[0] or "rkung" in bl[0]:
                                bl[0] = ''
                        bl = [re.sub('Bemerkung', '', t) for t in bl if t]

                        if len(bl) > 0:
                            if bl[-1][-1] == '-':
                                bl[-1] = re.sub('-', '', bl[-1]).strip()
                                concat += [True]
                            else: concat += [False]
                        if len(bl) > 0:
                            remark.append(bl)
                    rem = []
                    if len(remark) > 1:
                        for i, bl in enumerate(remark):
                            if not concat[i]:
                                rem += bl
                            else:
                                rem[-1] = rem[-1] + str(bl[0])
                                if len(bl) > 1:
                                    rem += bl[1:]
                    rem = BullingerData.remove_leading_junk(' '.join(rem))
                    if rem:
                        rem = rem.replace(' ,', ',').replace(' .', '.')
                        b.bemerkung = rem
                        bemerkung = rem
                        database.add(b)
                langs = [Langid.classify(bemerkung)]
                if "Sprache" in data:
                    for lang in BullingerData.analyze_language(data["Sprache"]):
                        if lang not in langs:
                            langs.append(lang)
                for lang in langs:
                    database.add(Sprache(id_brief=card_nr, language=lang, user=ADMIN, time=T0))

            else:
                print("*** WARNING [file ignored]:", path)
                database.add(Datum(id_brief=card_nr, year_a=SD, month_a=SD, day_a=SD, user=ADMIN, time=T0))
            database.commit()

    @staticmethod
    def clean_str(s):
        if s:
            s = re.sub('[^\w\d.,:;\-?!() ]', '', str(s))
            return re.sub('\s+', ' ', str(s)).strip()
        else: return ''

    @staticmethod
    def is_probably_junk(s):
        # more than 42% symbols
        s2, s1 = re.sub('[^\w\d]', '', s), re.sub('[\s]', '', s)
        if len(s1) == 0:
            return True
        if 0.58 > len(s2) / len(s1):
            return True
        # avg-str-length < 3
        tokens = s.split()
        if sum([len(s0) for s0 in tokens])/len(tokens) < 3:
            return True
        # big letters between small letters
        if re.match(r'.*[a-z]+[A-Z]+.*', s):
            return True
        if re.match(r'.*\s[^\s]\s.*\s[^\s]\s.*', s):
            return True
        return False

    @staticmethod
    def remove_leading_junk(s):
        s = s.replace('_', ' ')
        m, i = re.match(r'^([^\w\d(.]*)(.*)$', s, re.M | re.I), 0
        if m.group(2):
            while i < len(m.group(2)) and m.group(2)[i] == '.': i += 1
            if i >= 3: return m.group(2)[(i-3):].strip()
            else: return m.group(2)[i:].strip()

    @staticmethod
    def is_typewriter(baselines):
        keywords = ['StA', 'StB', 'Nr.', 'Ms.', 'Hr.', 'ZB', 'Zürich', 'Genf', 'Basel', 'Zofingen', 'Schaffhausen', 'London', 'Hamburg', 'Oxford', 'Gallen', 'Strassburg']
        if baselines:
            for b in baselines:
                if b:
                    for t in b:
                        for k in keywords:
                            if k in t:
                                return True
        return False

    @staticmethod
    def check_sign_for_zuerich_sta(s):
        l = len(s)
        if l:
            l = s[0:(4 if l > 4 else l)]
            if 'E' in l or '£' in l or '€' in l or 'T' in l or 'X' in l or 'B' in l or 'II' in l:
                return True
        return False

    @staticmethod
    def check_stdort_for_zuerich_sta(s):
        """ :param s: <str>
            :return: True, if there is an 'A' or '4' within the last four characters """
        if s:
            l = len(s)
            if l:
                l = s[-(4 if l > 4 else l):]
                if 'A' in l or '4' in l or 't' in l or 'S' in l:
                    return True
                if re.match(r'\d\d\d,', s):
                    return True
        return False

    @staticmethod
    def check_standort_ZZB(s):
        l = len(s)
        post = ['Z', '2', 'B', '8']
        if l:
            s1 = s[-(2 if l > 2 else l):]
            for c in post:
                if c in s1:
                    return True
            s2 = s[:(3 if l > 3 else l)]
            if len(re.findall(r'[Z2]', s2)) > 1:
                return True
        return False


    @staticmethod
    def how_many_I(s):
        m = re.match(r'[^E£€]*([^\d]*)\d.*', s)
        if m:
            s = m.group(1).replace('U', 'II').replace('X', 'II').replace('i', 'I').replace('J', 'I').replace('T', 'I')
            count = sum([1 for c in s if c == 'I'])
            return 'II' if count > 1 else 'I'
        return 'II'

    @staticmethod
    def analyze_bull_corr(baselines, record):
        if len(baselines) > 0:
            bc, bcc = [t.replace("Bull.Corr.", '') for s in baselines for t in s], []
            for t in bc:
                if "Corr" not in t:
                    t = re.sub("[A-Za-z]{3,}", '', t)
                    if t:
                        t = t.replace("Bl.", '').replace("Bl", '').replace("B1.", '').replace("B.", '')\
                             .replace("ßl.", '').replace("ßl", '').replace("ß1.", '').replace("ß.", '')\
                             .replace("8l.", '').replace("8l", '').replace("81.", '').replace("8.", '')\
                             .replace("S.", '').replace("S", '').replace("$.", '')\
                             .replace('l', '1').replace('I', '1')\
                             .replace('£', '2')\
                             .replace('?', '7').replace('y', '7')\
                             .replace('g', '8').replace('B', '8').replace('ß', '8').replace('$', '8')\
                             .replace('°', '0').replace('O', '0').replace('o', '0')
                        t = re.sub("[^0-9]", '', t)
                        if len(t) is not 0 and t is not '0': bcc.append(t)
            if len(bcc) == 1: record.bull_corr = int(bcc[0])
            elif len(bcc) == 2: record.blatt, record.seite = int(bcc[0]), int(bcc[1])
            elif len(bcc) > 2: record.bull_corr, record.blatt, record.seite = int(bcc[0]), int(bcc[1]), int(bcc[2])
            if len(bcc) is not 0: return record
        return None

    @staticmethod
    def analyze_language(baselines):
        if len(baselines[0]):
            lang, junk = [], []
            s = re.sub("[^A-Za-z]", ' ', ' '.join(baselines[0])).split()
            for t in s:
                t = t.lower()
                if t in "dts" or t in "deutsch":
                    if "Deutsch" not in lang: lang.append("Deutsch")
                elif t in "lateinisch":
                    if "Lateinisch" not in lang: lang.append("Lateinisch")
                elif t in "griechisch":
                    if "Griechisch" not in lang: lang.append("Griechisch")
                else: junk.append(t)
            # lang += junk
            return lang if len(lang) > 0 else []
        else: return []


    @staticmethod
    def analyze_address(baselines):
        """ Analyzes data from 'Absender' or 'Empfänger'
            :param baselines: list of lists
            :return: <name>, <forename>, <location>, <remarks> """
        # default values
        title, nn, vn, ort, bemerkung = '', 's.n.', 's.n.', 's.l.', None
        baselines = BullingerData.clean_up_baselines_sender_receiver(baselines)
        if len(baselines) > 0:
            # Rule 1 - 1st line 1st word == name
            nn = baselines[0][0]
            # Rule 2 - 1st line words 2-end == forename
            if len(baselines[0]) > 1:
                vn = ' '.join(baselines[0][1:])
                if nn != 'Geistliche':
                    # Titel
                    if 'von' in vn:
                        title = 'von'
                        vn = vn.replace('von', '').strip()
                    if 'de' in vn:
                        title = 'de'
                        vn = vn.replace('de', '').strip()
                else:  # Geistliche
                    ort = vn.replace('von', '').strip()
                    vn, nn = '', ''
                    title = "Geistliche"
        if len(baselines) > 1:
            ort = ' '.join(baselines[-1])
            ort = re.sub('\s+', ' ', ort.replace('.', '. '))
        if len(baselines) > 2:
            bemerkung = ' '.join([t for b in baselines[1:-1] for t in b])
        return nn, vn, ort, bemerkung, title


    @staticmethod
    def clean_up_baselines_sender_receiver(bl):
        _filter, new_baselines = ["Absender", "Empfänger"], []
        for b in bl:
            new_b = []
            for token in b:
                t = re.sub("[^A-Za-zäöüéèêàâñë.]", '', token)
                legal = True
                for x in _filter:
                    if x in t:
                        legal = False
                if legal and t != '' and t != '.':
                    new_b += [t]
            if new_b:
                new_baselines += [new_b]
        return new_baselines


    @staticmethod
    def is_bullinger_sender(data, hb_ngrams, precision, threshold):
        if "Absender" in data and "Empfänger" in data:
            abs, emp = [t for s in data["Absender"] for t in s], [t for s in data["Empfänger"] for t in s]
            res_a, res_b = [], []
            for a in abs:
                nga = [BullingerData.create_n_gram_dict(i, a) for i in range(1, precision)]
                dices = [BullingerData.compute_dice(nga[i], hb_ngrams[i]) for i in range(len(nga))]
                res_a.append(sum(dices)/len(dices))
            for a in emp:
                nga = [BullingerData.create_n_gram_dict(i, a) for i in range(1, precision)]
                dices = [BullingerData.compute_dice(nga[i], hb_ngrams[i]) for i in range(len(nga))]
                res_b.append(sum(dices)/len(dices))
            return max(res_a) > max(res_b)
        elif "Absender" in data:
            abs = [t for s in data["Absender"] for t in s]
            res_a = []
            for a in abs:
                nga = [BullingerData.create_n_gram_dict(i, a) for i in range(1, precision)]
                dices = [BullingerData.compute_dice(nga[i], hb_ngrams[i]) for i in range(len(nga))]
                res_a.append(sum(dices)/len(dices))
            return max(res_a) > threshold
        elif "Empfänger" in data:
            emp = [t for s in data["Empfänger"] for t in s]
            res_b = []
            for a in emp:
                nga = [BullingerData.create_n_gram_dict(i, a) for i in range(1, precision)]
                dices = [BullingerData.compute_dice(nga[i], hb_ngrams[i]) for i in range(len(nga))]
                res_b.append(sum(dices)/len(dices))
            return max(res_b) > threshold
        else: return False

    @staticmethod
    def create_n_gram_dict(n, string):
        """ :param n: <int> 1..n
            :param string: <str> """
        dict_n_gram_count = CountDict()
        boundaries = (n - 1) * '_'
        test = boundaries + string + boundaries
        for i in range(len(test) + 1 - n):
            dict_n_gram_count.add(test[i: i + n])
        return dict_n_gram_count

    @staticmethod
    def compute_dice(dict1, dict2):
        d1, c1 = dict1, dict1.tot
        d2, c2 = dict2, dict2.tot
        return -1 if c1+c2 == 0 else 2.0 * BullingerData.compute_number_of_common_values(d1, d2) / (c1 + c2)

    @staticmethod
    def compute_number_of_common_values(dict1, dict2):
        return sum([min(dict1[key], dict2[key]) for key in dict1 if key in dict2])

    @staticmethod
    def get_data_as_dict(path):
        d = ListDict()
        size = OCR2.get_page_size(path)
        if size:
            scale_factor_x = BullingerData.AVG_PAGE_SIZE[0]/size[0]
            scale_factor_y = BullingerData.AVG_PAGE_SIZE[1]/size[1]
            t = OCR2.get_attr_positions(path, (scale_factor_x, scale_factor_y), inverse=True)
            t["Field"] = None
            t.reset_index(inplace=True, drop=True)
            for index, row in t.iterrows():
                ad = BullingerData.get_attribute_name(row['x'], row['y'])
                attribute = ' '.join([ad[0], ad[1]]) if ad[1] else ad[0]
                t.loc[index, "Field"] = attribute
            t = t[["Field", "Value", "x", "y", "Baseline"]]
            fields = t.groupby('Field')
            for attribute, group in fields:
                group.sort_values(['x'], ascending=False).reset_index(drop=True)
                group.sort_values(['Baseline'], ascending=False).reset_index(drop=True)
                for index, row in group.iterrows():
                    if BullingerData.is_attribute(row['Field'], row['x'], row['y']):
                        group.drop(index, inplace=True)
                lines, line, baseline = [], [], 0
                for index, row in group.iterrows():
                    if baseline != row['Baseline']:
                        if len(line) != 0: lines.append(line)
                        line = list()
                        line.append(row['Value'])
                        baseline = row['Baseline']
                    else:
                        line.append(row['Value'])
                lines.append(line)
                d.add(attribute, lines)
            return d
        else:
            print("*** Warning, file ignored:", path)
            return None

    year_predicted = 1547  # 1st file card
    month_predicted, index_predicted = [
        ["Januar"], ["Februar"], ["März", "Mrz"], ["April"], ["Mai", "Mal", "Mi", "Hai"], ["Juni"],
        ["Juli"], ["August"], ["September"], ["Oktober", ], ["November"], ["Dezember"]
    ], 9  # October
    @staticmethod
    def extract_date(id_brief, data, database):
        data = [re.sub("[^A-Za-z0-9]", '', token).strip() for token in data]
        data = [token for token in data if token != '']
        year, month = BullingerData.year_predicted, BullingerData.month_predicted[BullingerData.index_predicted][0]
        for token in data: # year
            if token == str(year):
                data.remove(token)
                break
            if token == str(year+1):
                BullingerData.year_predicted = int(token)
                data.remove(token)
                break
        end = False # month
        for token in data:
            for m in BullingerData.month_predicted[BullingerData.index_predicted]:
                if token in m and len(token)>2:
                    data.remove(token)
                    end = True
                    break
            if end:
                break
            else:
                i = BullingerData.index_predicted
                i = i+1 if i < 11 else 0
                for m in BullingerData.month_predicted[i]:
                    if token in m and len(token) > 2:
                        data.remove(token)
                        BullingerData.index_predicted = i
        day = SD
        for token in data:
            if token.isdigit():
                if 0 < int(token) < 32:
                    day = int(token)
                    data.remove(token)
                    break
        # correction mechanisms
        if str(BullingerData.year_predicted-1) in data:
            BullingerData.year_predicted -= 1
        if day == SD and len(data) > 0:
            modified_tokens = []
            for token in data:  # ocr-errors
                token = token.replace('o', '0')
                token = token.replace('O', '0')
                token = token.replace('I', '1')
                token = token.replace('i', '1')
                token = token.replace('l', '1')
                modified_tokens.append(token)
            candidates = []  # split tokens into int/str
            for token in modified_tokens:
                match = re.match(r"[a-z]*([0-9]+)", token, re.I)
                if match: candidates.append(match.group(1))
            for token in candidates:  # retry
                if token.isdigit():
                    if 0 < int(token) < 32:
                        day = int(token)
                        break
        database.add(Datum(
            id_brief=id_brief,
            year_a=BullingerData.year_predicted,
            month_a=BullingerData.month_predicted[BullingerData.index_predicted][0],
            day_a=day,
            year_b='',
            month_b='',
            day_b='',
            user=ADMIN,
            time=T0
        ))
        database.commit()

    @staticmethod
    def extract(dir_path, recursively=True):

        # Stats
        # c = pd.DataFrame({'content': [], 'x': [], 'y': []})
        a = pd.DataFrame({'Value': [], 'x': [], 'y': [], "Baseline": []})
        # t = pd.DataFrame({'Attribute': [], 'x': [], 'y': []})

        paths = FileSystem.get_file_paths(dir_path, recursively=recursively)
        n, n_max = 0, len(paths)  # counter
        for path in paths:

            n += 1

            print("\n\n"+74 * '=')
            print('{:_>5}'.format(n), "-", path)
            print(74 * '=')

            size = OCR2.get_page_size(path)
            if size:

                scale_factor_x = BullingerData.AVG_PAGE_SIZE[0]/size[0]
                scale_factor_y = BullingerData.AVG_PAGE_SIZE[1]/size[1]
                print("Scaling x:", scale_factor_x, "\nScaling y:", scale_factor_y)
                print("Width =", int(scale_factor_x*size[0]), "\nHeight =", int(scale_factor_y*size[1]))

                df_attr = OCR2.get_attr_positions(path, (scale_factor_x, scale_factor_y))
                t = OCR2.get_attr_positions(path, (scale_factor_x, scale_factor_y), inverse=True)

                a = pd.concat([a, df_attr])
                t["Field"] = None
                t.reset_index(inplace=True, drop=True)
                for index, row in t.iterrows():
                    ad = BullingerData.get_attribute_name(row['x'], row['y'])
                    attribute = ' '.join([ad[0], ad[1]]) if ad[1] else ad[0]
                    t.loc[index, "Field"] = attribute

                t = t[["Field", "Value", "x", "y", "Baseline"]]
                fields = t.groupby('Field')
                for attribute, group in fields:

                    print(60*'-')
                    print(attribute)
                    print(60 * '-')

                    group.sort_values(['x'], ascending=False).reset_index(drop=True)
                    group.sort_values(['Baseline'], ascending=False).reset_index(drop=True)

                    for index, row in group.iterrows():
                        if BullingerData.is_attribute(row['Field'], row['x'], row['y']):
                            group.drop(index, inplace=True)
                    print(group.to_string())

            else:
                # Invalid Path
                print("*** Warning, file ignored:", path)

        # Visualization for 100

        attr, err, stats = BullingerData._analyze_attribute_positions(a)
        print(stats.to_latex(index=False))
        """
        print(err)  # is empty due to scaling :)
        ScatterPlot.create(
            [t['x']],
            [t['y']],
            alpha=[0.3], size=[1, 5, 100, 80], color=['black', 'green', 'red', 'navy'],
            xlabel="width [px]", ylabel="height [px]", reverse_y=True,
            output_path=BullingerData.IMG_ATTRIBUTES_4,
            function=BullingerData.draw_grid
        )"""

    @staticmethod
    def analyze_attribute_positions():
        data, err, stats = BullingerData._analyze_attribute_positions(BullingerData.get_attribute_data())
        c = BullingerData.get_text_coordinates(BullingerData.PATH_V2)  # scenery
        ScatterPlot.create(
            [c['x'], data['x'], err['x'], stats['x']],
            [c['y'], data['y'], err['y'], stats['y']],
            alpha=[0.1, 0.3, 0.3, 0.3], size=[1, 5, 5, 80], color=['black', 'green', 'red', 'navy'],
            xlabel="width [px]", ylabel="height [px]", reverse_y=True,
            output_path=BullingerData.IMG_ATTRIBUTES_2,
            function=BullingerData.draw_grid
        )

    @staticmethod
    def _analyze_attribute_positions(attribute_positions):
        a = 'Value'
        data = pd.DataFrame({a: [], 'x': [], 'y': []})
        err = pd.DataFrame({a: [], 'x': [], 'y': []})  # outliers
        stats = pd.DataFrame({a: [], 'x': [], 'y': [], 'xd': [], 'yd': []})
        for attr in BullingerData.ATTRIBUTES:
            d = attribute_positions[(attribute_positions[a] == attr)].copy()
            d.reset_index(inplace=True, drop=True)
            for index, row in d.iterrows():  # filter/collect outliers
                if row[a] not in BullingerData.get_attribute_name(row['x'], row['y'])[0]:
                    d.drop(index, inplace=True)
                    err = pd.concat([err, pd.DataFrame(
                        {a: [row[a]], 'x': [row['x']], 'y': [row['y']]})])
            for ad in BullingerData.linear_separation(d, attr):
                ad.reset_index(drop=True)
                if not ad.empty:
                    mean = list(BullingerData.stats(ad, columns=['x', 'y']).loc[:, 'mean'])
                    dev = list(BullingerData.stats(ad, columns=['x', 'y']).loc[:, 'dev'])
                    s = pd.DataFrame({
                        a: [attr], 'x': [mean[0]], 'y': [mean[1]],
                        'xd': [dev[0]], 'yd': [dev[1]]})
                    stats = pd.concat([stats, s])
            data = pd.concat([data, d], sort=True)
        return data, err, stats

    @staticmethod
    def analyze_text_positions():
        df1 = BullingerData.get_text_coordinates(BullingerData.PATH_V1, version=1)
        df2 = BullingerData.get_text_coordinates(BullingerData.PATH_V2, version=2)
        x, y = list(df1)[1], list(df1)[2] # schema names
        ScatterPlot.create(
            [df1[x], df2[x]],
            [df1[y], df2[y]],
            alpha=[0.1, 0.1], color=['red', 'blue'], size=[1, 1],
            reverse_y=True, xlabel="width [px]", ylabel="height [py]",
            function=BullingerData.draw_grid,
            output_path=BullingerData.IMG_TEXT_POSITIONS
        )

    @staticmethod
    def draw_grid(plt):
        """ appends the grid of a typical index card to plot <plt> """
        x0, x1, x2, x3 = 0, 3057, 6508, 9860
        y0, y1, y2, y3, y4, y5, y6, y7, y8 = 0, 1535, 2041, 2547, 3053, 3559, 4257, 5303, 6978
        alpha, linewidth = 0.3, 0.5

        # Vertical Lines
        plt.plot((x0, x0), (y0, y8), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x1, x1), (y0, y8), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x2, x2), (y0, y5), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x3, x3), (y0, y8), 'black', alpha=alpha, linewidth=linewidth)

        # Horizontal Lines
        plt.plot((x0, x3), (y0, y0), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x0, x3), (y1, y1), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x0, x3), (y2, y2), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x0, x3), (y3, y3), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x0, x3), (y4, y4), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x0, x3), (y5, y5), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x0, x1), (y6, y6), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x1, x3), (y7, y7), 'black', alpha=alpha, linewidth=linewidth)
        plt.plot((x0, x3), (y8, y8), 'black', alpha=alpha, linewidth=linewidth)

    @staticmethod
    def analyze_page_sizes():

        # Data
        df1 = OCR1.get_page_sizes(BullingerData.PATH_V1)  # Version 1
        df2 = OCR2.get_page_sizes(BullingerData.PATH_V2)  # Version 2
        x, y, mean = list(df1)[1], list(df1)[2], BullingerData.SCHEMA_STATS[1]  # schema names
        s1 = list(BullingerData.stats(df1, columns=[x, y]).loc[:, mean])  # stats 1
        s2 = list(BullingerData.stats(df2, columns=[x, y]).loc[:, mean])  # stats 2
        s3 = list(BullingerData.stats(pd.concat([df1, df2]), columns=[x, y]).loc[:, mean])  # s1+2

        # Plot (uncorrected)
        ScatterPlot.create(
            [df1[x], [s1[0]], [s2[0]], [s3[0]]],
            [df1[y], df2[y], [s1[1]], [s2[1]], [s3[1]]],
            alpha=[0.3, 0.3, 0.1, 0.1, 0.1],
            color=['green', 'blue', 'green', 'blue', 'red'],
            size=[5, 5, 50, 50, 500],
            xlabel="width [px]", ylabel="height [py]",
            output_path=BullingerData.IMG_PAGE_DIM_1
        )
        # --> there is no difference between df1 and df2

        # Plot (without outliers)
        df = df1[df1.x > 6000]  # 4/99
        sdf = list(BullingerData.stats(df, columns=[x, y]).loc[:, mean])
        ScatterPlot.create(
            [df[x], [sdf[0]]],
            [df[y], [sdf[1]]],
            alpha=[0.3, 0.5], color=['b', 'r'], size=[10, 100],
            xlabel="width [px]", ylabel="height [py]",
            output_path=BullingerData.IMG_PAGE_DIM_2
        )

        return int(sdf[0]), int(sdf[1])  # avg. (width, height)

    @staticmethod
    def stats(df, columns=None):
        """ computes averages and standard deviations
            :param columns: <list(int)>. indices
            :param df: <DataFrame>
            :return: <DataFrame> """
        s = BullingerData.SCHEMA_STATS
        d = pd.DataFrame(columns=s)
        for column in columns:
            mean = round(sum(df.loc[:, column]) / len(list(df.loc[:, column])), BullingerData.ROUND)
            std_dev = round(statistics.stdev(df.loc[:, column]), BullingerData.ROUND)
            d = pd.concat([d, pd.DataFrame({s[0]: [column], s[1]: [mean], s[2]: std_dev})])
        return d

    @staticmethod
    def get_text_coordinates(dir_path_in, version=2):
        parser = TextPositionParser1 if version is 1 else TextPositionParser2
        data = pd.DataFrame({'content': [], 'x': [], 'y': []})
        for path in FileSystem.get_file_paths(dir_path_in):
            data = pd.concat([data, parser.get_coordinates(path, (1, 1))])
        return data

    @staticmethod  # ANALYSIS
    def get_attribute_data():
        data = pd.DataFrame({'Attribute': [], 'x': [], 'y': []})
        for path in FileSystem.get_file_paths(BullingerData.PATH_V2):
            data = pd.concat([data, AttributePositionParser.get_attributes(path, (1, 1))])
        return data

    @staticmethod
    def get_attribute_indirectly(hpos_t, vpos_r, height_b, width_l, version=2):
        """ key: position --> value: (attribute name, index)
            :param hpos_t: <int>
            :param vpos_r: <int>
            :param height_b: <int>
            :param width_l: <int>
            :param version: <1|2>: (top/right/bottom/left) || (top/left, height/width) """
        if version is 2:
            mx, my = int(hpos_t + 0.5 * width_l), int(vpos_r + 0.5 * height_b)  # mass point
        else:  # version 1
            mx, my = int((hpos_t+height_b)/2), int((vpos_r+width_l)/2)
        return BullingerData.get_attribute_name(mx, my)

    @staticmethod
    def get_attribute_name(x, y):
        if x <= 3057:  # 1st column
            if y <= 1535: return "Datum", None
            elif y <= 2041: return "Autograph", None
            elif y <= 2547: return "Standort", 'A'
            elif y <= 3053: return "Sign.", 'A'
            elif y <= 3559: return "Umfang", 'A'
            elif y <= 4257: return "Sprache", None
            else: return "Gedruckt", None
        elif x <= 6508:  # 2nd column
            if y <= 1535: return "Absender", None
            elif y <= 2041: return "Kopie", None
            elif y <= 2547: return "Standort", 'B'
            elif y <= 3053: return "Sign.", 'B'
            elif y <= 3559: return "Umfang", 'B'
            elif y <= 5303: return "Literatur", None
            else: return "Bemerkungen", None
        else:  # 3rd column
            if y <= 1535: return "Empfänger", None
            elif y <= 2041: return "Photokopie", None
            elif y <= 2547: return "Bull. Corr.", 'A'
            elif y <= 3053: return "Abschrift", None
            elif y <= 3559: return "Bull. Corr.", 'B'
            elif y <= 5303: return "Literatur", None
            else: return "Bemerkungen", None

    @staticmethod
    def linear_separation(df, attr):
        a = "Value"
        x_sep, y_sep, results = 2000, 3000, []
        if attr in ['Standort', 'Sign.', 'Umfang']:  # duplicate
            d_l = df[(df[a] == attr) & (df['x'] < x_sep)].copy()
            d_r = df[(df[a] == attr) & (df['x'] > x_sep)].copy()
            d_l.loc[:, a] = d_l[a].apply(lambda x: x + '-Left')
            d_r.loc[:, a] = d_r[a].apply(lambda x: x + '-Right')
            results += [d_l, d_r]
        elif attr in ['Bull.', 'Corr.']:
            d_t = df[(df[a] == attr) & (df['y'] < y_sep)].copy()
            d_b = df[(df[a] == attr) & (df['y'] > y_sep)].copy()
            d_t.loc[:, a] = d_t[a].apply(lambda x: attr + '-Left')
            d_b.loc[:, a] = d_b[a].apply(lambda x: attr + '-Right')
            results += [d_t, d_b]
        else:
            results += [df]
        return results

    @staticmethod
    def is_attribute(attribute_name, x_coord, y_coord, deviation=3):
        """ checks if (<x_coord>, <y_coord>) corresponds to <attribute_name>
            :param attribute_name: <str>
            :param x_coord: <int>
            :param y_coord: <int>
            :param deviation <int>
            :return: <bool> """
        d = deviation  # tolerance
        return {
            "Datum": lambda x, y: True if 364-d*20 < x < 364+d*20 and 320-d*13 < y < 320+d*13 else False,
            "Absender": lambda x, y: True if 3631-d*17 < x < 3631+d*17 and 329-d*12 < y < 329+d*12 else False,
            "Empfänger": lambda x, y: True if 7134-d*18 < x < 7174+d*18 and 349-d*12 < y < 349+d*12 else False,
            "Autograph": lambda x, y: True if 515-d*19 < x < 515+d*19 and 1901-d*13 < y < 1901+d*13 else False,
            "Standort A": lambda x, y: True if 437-d*20 < x < 437+d*20 and 2291-d*12 < y < 2281+12 else False,
            "Standort B": lambda x, y: True if 3577-d*19 < x < 3577+d*19 and 2283-d*12 < y < 2283+d*12 else False,
            "Sign. A": lambda x, y: True if 298-d*18 < x < 298+d*18 and 2903-d*12 < y < 2903+d*12 else False,
            "Sign. B": lambda x, y: True if 3442-d*18 < x < 3442+d*18 and 2903-d*12 < y < 2903+d*12 else False,
            "Umfang A": lambda x, y: True if 397-d*21 < x < 397+d*21 and 3297-d*13 < y < 3297+d*13 else False,
            "Umfang B": lambda x, y: True if 3543-d*17 < x < 3543+d*17 and 3297-d*13 < y < 3297+d*13 else False,
            "Photokopie": lambda x, y: True if 7120-d*26 < x < 7120+d*26 and 1904-d*12 < y < 1904+d*12 else False,
            "Bull. Corr. A": lambda x, y: True if 6865-d*35 < x < 7273+d*37 and 2282-d*15 < y < 2282+d*15 else False,
            "Bull. Corr. B": lambda x, y: True if 6865-d*35 < x < 7273+d*37 and 3284-d*15 < y < 3284+d*15 else False,
            "Abschrift": lambda x, y: True if 7049-d*25 < x < 7049+d*25 and 2890-d*11 < y < 2890+d*11 else False,
            "Sprache": lambda x, y: True if 417-d*22 < x < 417+d*22 and 3917-d*13 < y < 3917+d*13 else False,
            "Gedruckt": lambda x, y: True if 448-d*21 < x < 448+d*21 and 4594-d*13 < y < 4594+d*13 else False,
            "Literatur": lambda x, y: True if 3560-d*20 < x < 3560+d*20 and 3904-d*13 < y < 3904+d*13 else False,
            "Bemerkungen": lambda x, y: True if 3752-d*19 < x < 3752+d*19 and 5691-d*15 < y < 5691+d*15 else False,
            "Kopie": lambda x, y: True if 3465-d*17 < x < 3465+d*17 and 1903-d*12 < y < 1903+d*12 else False,
        }[attribute_name](x_coord, y_coord)

'''
\begin{tabular}{lrrrr}
\toprule
       Value &       x &       y &    xd &    yd \\
\midrule
       Datum &   364.0 &   320.0 &  20.0 &  13.0 \\
    Absender &  3631.0 &   329.0 &  17.0 &  12.0 \\
   Empfänger &  7134.0 &   349.0 &  18.0 &  12.0 \\
   Autograph &   515.0 &  1901.0 &  19.0 &  13.0 \\
       Kopie &  3465.0 &  1903.0 &  17.0 &  12.0 \\
  Photokopie &  7120.0 &  1904.0 &  26.0 &  12.0 \\
    Standort &   437.0 &  2281.0 &  20.0 &  12.0 \\
    Standort &  3577.0 &  2283.0 &  19.0 &  12.0 \\
       Bull. &  6861.0 &  2282.0 &  31.0 &  13.0 \\
       Bull. &  6872.0 &  3284.0 &  37.0 &  18.0 \\
       Corr. &  7261.0 &  2284.0 &  31.0 &  13.0 \\
       Corr. &  7273.0 &  3285.0 &  36.0 &  17.0 \\
       Sign. &   298.0 &  2903.0 &  18.0 &  12.0 \\
       Sign. &  3442.0 &  2903.0 &  16.0 &  12.0 \\
   Abschrift &  7049.0 &  2890.0 &  25.0 &  11.0 \\
      Umfang &   397.0 &  3297.0 &  21.0 &  13.0 \\
      Umfang &  3543.0 &  3299.0 &  17.0 &  12.0 \\
     Sprache &   417.0 &  3917.0 &  22.0 &  13.0 \\
   Literatur &  3560.0 &  3904.0 &  20.0 &  13.0 \\
    Gedruckt &   448.0 &  4594.0 &  21.0 &  13.0 \\
 Bemerkungen &  3752.0 &  5691.0 &  19.0 &  15.0 \\
\bottomrule
\end{tabular}
'''
