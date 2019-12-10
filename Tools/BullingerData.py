#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# BullingerData.py
# Bernard Schroffenegger
# 6th of October, 2019

""" (OCR2 ->) Bullinger data analysis (-> DB) """

from Tools.OCR2 import *
from Tools.Dictionaries import ListDict
from Tools.NGrams import NGrams
from Tools.Langid import *
from App.models import *

SN = 's.n.'  # sine nomine
SL = 's.l.'  # sine loco
SD = 's.d.'  # sine die
ADMIN = 'Admin'  # username


class BullingerData:

    # Samples
    PATH_V1 = 'Karteikarten/ocr_sample_100_v1'
    PATH_V2 = 'Karteikarten/ocr_sample_100_v2'

    # Data
    AVG_PAGE_SIZE = [9860, 6978]
    AVG_PAGE_SIZE_DEV = [11, 10]

    ATTRIBUTES = ["Datum", "Absender", "Empfänger", "Autograph", "Kopie", "Photokopie", "Standort", "Bull.", "Corr.",
                  "Sign.", "Abschrift", "Umfang", "Sprache", "Literatur", "Gedruckt", "Bemerkungen"]

    # Patterns for attributnames
    p_standort = '[Ss$][tlf1I|]a[nm]d[o0°O]r[tlf1I]'
    p_signatur = '[Ss][il][g8B]n[.]?'
    p_umfang = '[Uu][mn][ftl]a[nm][g8B]'

    TYPEWRITER = ['StA', 'StB', 'Nr.', 'Ms.', 'Hr.', 'ZB', 'Zürich', 'Genf', 'Basel', 'Zofingen', 'Schaffhausen',
                  'London', 'Hamburg', 'Oxford', 'Gallen', 'Strassburg']

    def __init__(self):
        pass

    @staticmethod
    def get_ssu(data, index):
        standort_baselines, baselines_signatur, is_typewriter = None, None, False
        standort_str, standort, signatur_str, signatur = '', '', '', ''
        umfang_baselines, umfang_str, umfang = '', '', ''
        if "Standort "+index in data:
            standort_baselines = data["Standort "+index]
            standort_str = [t for s in data["Standort "+index] for t in s]
            standort_str = re.sub(BullingerData.p_standort, '', ' '.join(standort_str))
            standort = BullingerData.clean_str(standort_str)
        if "Sign. "+index in data:
            baselines_signatur = data["Sign. "+index]
            signatur_str = [t for s in data["Sign. "+index] for t in s]
            signatur_str = re.sub(BullingerData.p_signatur, '', ' '.join(signatur_str))
            signatur = BullingerData.clean_str(signatur_str)
        if "Umfang "+index in data:
            umfang_str = [t for s in data["Umfang "+index] for t in s]
            umfang_str = re.sub(BullingerData.p_umfang, '', ' '.join(umfang_str))
            umfang = ' '.join(umfang_str)

        # 1. Typewriter Data
        if BullingerData.is_typewriter(standort_baselines) or BullingerData.is_typewriter(baselines_signatur):
            if standort:
                d = standort + signatur + umfang
                m = re.match(r"(.*)StA\s(E[\d\s,]*)([^\d]*)", d)
                m = re.match(r"(.*)StA\s(A[\d\s,]*)([^\d]*)", d) if not m else None
                m = re.match(r"(.*)ZB\s([MsS\d\s,]*)([^\d]*)", d) if not m else None
                standort = m.group(1) if m else standort
                signatur = ' '.join([m.group(2), ]) if m else signatur
                umfang = m.group(3) if m else umfang

        elif BullingerData.check_stdort_for_zuerich_sta(standort) or \
                BullingerData.check_sign_for_zurich_sta(signatur):
            standort, is_zsta = "Zürich StA", True
            number = re.sub(r'[^\d,f]', '', signatur + umfang)
            n_i = BullingerData.how_many_i(signatur)
            signatur = ' '.join(['E', n_i, number.strip(',')])

        elif BullingerData.check_place_zzb(standort):
            standort = "Zürich ZB"
            numbers = re.sub(r'[^\d,]', '', standort + signatur + umfang)
            signatur = ''.join('Ms S ' + numbers)

        elif len(standort_str) or len(signatur_str) or len(umfang_str):
            standort = "Zürich"

        return standort, signatur, umfang

    @staticmethod
    def get_literature(data):
        if "Literatur" in data:
            literature = ' '.join([t for s in data["Literatur"] for t in s])
            literature = re.sub("Literatur", '', literature)
            if not BullingerData.is_probably_junk(literature):
                return BullingerData.clean_str(literature)
        return None

    @staticmethod
    def get_printed(data):
        if "Gedruckt" in data:
            p = ' '.join([t for s in data["Gedruckt"] for t in s])
            p = re.sub("Gedruckt", '', p)
            if not BullingerData.is_probably_junk(p):
                return BullingerData.clean_str(p)
        return None

    @staticmethod
    def get_remark(data):
        if 'Bemerkungen' in data:
            remark, concat = list(), [False]
            for baseline in data["Bemerkungen"]:
                bl = [BullingerData.clean_str(s) for s in baseline]
                bl = [re.sub('Bemerkung', '', t) for t in bl if t]
                if len(bl) > 0:
                    if bl[-1][-1] == '-':
                        bl[-1] = re.sub('-', '', bl[-1]).strip()
                        concat += [True]
                    else:
                        concat += [False]
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
                return rem.replace(' ,', ',').replace(' .', '.')
        return None

    @staticmethod
    def get_lang(data, bemerkung):
        langs = [Langid.classify(bemerkung)]
        if "Sprache" in data:
            for lang in BullingerData.analyze_language(data["Sprache"]):
                if lang not in langs:
                    langs.append(lang)
        return langs

    @staticmethod
    def clean_str(s):
        if s:
            s = re.sub(r'[^\w\d.,:;\-?!() ]', '', str(s))
            return re.sub(r'\s+', ' ', str(s)).strip()
        return ''

    @staticmethod
    def is_probably_junk(s):
        # more than 42% symbols
        s2, s1 = re.sub(r'[^\w\d]', '', s), re.sub(r'[\s]', '', s)
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
            while i < len(m.group(2)) and m.group(2)[i] == '.':
                i += 1
            if i >= 3:
                return m.group(2)[(i-3):].strip()
            return m.group(2)[i:].strip()

    @staticmethod
    def is_typewriter(baselines):
        if baselines:
            for b in baselines:
                if b:
                    for t in b:
                        for k in BullingerData.TYPEWRITER:
                            if k in t:
                                return True
        return False

    @staticmethod
    def check_sign_for_zurich_sta(s):
        j = len(s)
        if j:
            j = s[0:(4 if j > 4 else j)]
            if 'E' in j or '£' in j or '€' in j or 'T' in j or 'X' in j or 'B' in j or 'II' in j:
                return True
        return False

    @staticmethod
    def check_stdort_for_zuerich_sta(s):
        """ :param s: <str>
            :return: True, if there is an 'A' or '4' within the last four characters """
        if s:
            j = len(s)
            if j:
                j = s[-(4 if j > 4 else j):]
                if 'A' in j or '4' in j or 't' in j or 'S' in j:
                    return True
                if re.match(r'\d\d\d,', s):
                    return True
        return False

    @staticmethod
    def check_place_zzb(s):
        j = len(s)
        post = ['Z', '2', 'B', '8']
        if j:
            s1 = s[-(2 if j > 2 else j):]
            for c in post:
                if c in s1:
                    return True
            s2 = s[:(3 if j > 3 else j)]
            if len(re.findall(r'[Z2]', s2)) > 1:
                return True
        return False

    @staticmethod
    def how_many_i(s):
        m = re.match(r'[^E£€]*([^\d]*)\d.*', s)
        if m:
            s = m.group(1).replace('U', 'II').replace('X', 'II').replace('i', 'I').replace('J', 'I').replace('T', 'I')
            count = sum([1 for c in s if c == 'I'])
            return 'II' if count > 1 else 'I'
        return 'II'

    @staticmethod
    def analyze_language(baselines):
        if len(baselines[0]):
            lang, junk = [], []
            s = re.sub("[^A-Za-z]", ' ', ' '.join(baselines[0])).split()
            for t in s:
                t = t.lower()
                if t in "dts" or t in "deutsch":
                    if "Deutsch" not in lang:
                        lang.append("Deutsch")
                elif t in "lateinisch":
                    if "Lateinisch" not in lang:
                        lang.append("Lateinisch")
                elif t in "griechisch":
                    if "Griechisch" not in lang:
                        lang.append("Griechisch")
                else:
                    junk.append(t)
            # lang += junk
            return lang if len(lang) > 0 else []
        return []

    @staticmethod
    def analyze_address(baselines):
        """ Analyzes data from 'Absender' or 'Empfänger'
            :param baselines: list of lists
            :return: <name>, <forename>, <location>, <remarks> """
        # default values
        nn, vn, ort, bemerkung = 's.n.', 's.n.', 's.l.', None
        baselines = BullingerData.clean_up_baselines_sender_receiver(baselines)
        if len(baselines) > 0:
            # Rule 1 - 1st line 1st word == name
            nn = baselines[0][0]
            if len(baselines[0]) > 1:
                vn = ' '.join(baselines[0][1:])
                if nn != 'Geistliche':
                    # Title
                    if re.match(r'.*von.*', vn):
                        vn = vn.replace('von', '').strip()
                        nn = 'von ' + nn
                    if re.match(r'.*de.*', vn):
                        vn = vn.replace('de', '').strip()
                        nn = 'de ' + nn
                    if re.match(r'.*du.*', vn):
                        vn = vn.replace('du', '').strip()
                        nn = 'du ' + nn
                else:  # Geistliche
                    ort = vn.replace('von', '').strip()
                    nn = "Geistliche"
        if len(baselines) > 1:
            ort = ' '.join(baselines[-1])
            ort = re.sub(r'\s+', ' ', ort.replace('.', '. '))
        if len(baselines) > 2:
            bemerkung = ' '.join([t for b in baselines[1:-1] for t in b])
        return nn, vn, ort, bemerkung

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
    def is_bullinger_sender(data, b_n_grams, h_n_grams):
        precision = 4
        threshold = 0.5
        if "Absender" in data and "Empfänger" in data:
            sender, receiver = [t for s in data["Absender"] for t in s], [t for s in data["Empfänger"] for t in s]
            pbs, phs = BullingerData.compute_similarities(sender, precision, b_n_grams, h_n_grams)
            pbr, phr = BullingerData.compute_similarities(receiver, precision, b_n_grams, h_n_grams)
            return max(pbs) + max(phs) > max(pbr) + max(phr)
        elif "Absender" in data:  # Empfänger missing
            sender = [t for s in data["Absender"] for t in s]
            pbs, phs = BullingerData.compute_similarities(sender, precision, b_n_grams, h_n_grams)
            return max(pbs)+max(phs) > 2*threshold
        elif "Empfänger" in data:  # Absender missing
            receiver = [t for s in data["Empfänger"] for t in s]
            pbr, phr = BullingerData.compute_similarities(receiver, precision, b_n_grams, h_n_grams)
            return max(pbr)+max(phr) > 2*threshold
        return False

    @staticmethod
    def compute_similarities(tokens, precision, bng, hng):
        pb, ph = [], []
        for t in tokens:
            nga = [NGrams.create_n_gram_dict(i, t) for i in range(1, precision)]
            dices_bullinger = [NGrams.compute_dice(nga[i], bng[i]) for i in range(len(nga))]
            dices_heiri = [NGrams.compute_dice(nga[i], hng[i]) for i in range(len(nga))]
            pb.append(sum(dices_bullinger) / len(dices_bullinger))
            ph.append(sum(dices_heiri) / len(dices_heiri))
        return pb, ph

    year_predicted = 1547  # 1st file card
    month_predicted, index_predicted = [
        ["Januar"], ["Februar"], ["März", "Mrz"], ["April"], ["Mai", "Mal", "Mi", "Hai"], ["Juni"],
        ["Juli"], ["August"], ["September"], ["Oktober", ], ["November"], ["Dezember"]
    ], 9  # October

    @staticmethod
    def extract_date(id_brief, data):
        if "Datum" in data:
            data = [i for j in data["Datum"] for i in j]
            data = [re.sub("[^A-Za-z0-9]", '', token).strip() for token in data]
            data = [token for token in data if token != '']
            year, month = BullingerData.year_predicted, BullingerData.month_predicted[BullingerData.index_predicted][0]
            for token in data:  # year
                if token == str(year):
                    data.remove(token)
                    break
                if token == str(year+1):
                    BullingerData.year_predicted = int(token)
                    data.remove(token)
                    break
            end = False  # month
            for token in data:
                for m in BullingerData.month_predicted[BullingerData.index_predicted]:
                    if token in m and len(token) > 2:
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
                    if match:
                        candidates.append(match.group(1))
                for token in candidates:  # retry
                    if token.isdigit():
                        if 0 < int(token) < 32:
                            day = int(token)
                            break
            return Datum(
                id_brief=id_brief, year_a=BullingerData.year_predicted,
                month_a=BullingerData.month_predicted[BullingerData.index_predicted][0], day_a=day,
                year_b='', month_b='', day_b=''
            )
        return None

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
                        if len(line) != 0:
                            lines.append(line)
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

    @staticmethod
    def get_attribute_name(x, y):
        """ <x_coord, y_coord> --> attribute name"""
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
        """ to distinguish between duplicate attribute names """
        x_sep, y_sep, results, a = 2000, 3000, [], "Value"
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
        """ <x_coord>/<y_coord>  <-->  <attribute_name> ?
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
