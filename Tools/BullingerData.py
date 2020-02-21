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

ADMIN = 'Admin'  # username


class BullingerData:

    # Samples
    PATH_V1 = 'Karteikarten/ocr_sample_100_v1'
    PATH_V2 = 'Karteikarten/ocr_sample_100_v2'

    # Data
    AVG_PAGE_SIZE = [9860, 6978]
    AVG_PAGE_SIZE_DEV = [11, 10]
    NG_MAX = 4  # n-grams (precision)

    ATTRIBUTES = ["Datum", "Absender", "Empfänger", "Autograph", "Kopie", "Photokopie", "Standort", "Bull.", "Corr.",
                  "Sign.", "Abschrift", "Umfang", "Sprache", "Literatur", "Gedruckt", "Bemerkungen"]
    TYPEWRITER_ABBREV = ["StA", "ZB", "BPU", "UB", "KB", "StB", "AST", "BNU", "BM", "UL", "StUB", "BurgerB", "BSG",
                         "BN", "BRU", "TC", "StUA", "BL"]
    TYPEWRITER_ = ['Simler', 'Prof.']
    TYPEWRITER = ["Zürich", "Genf", "Basel", "Schaffhausen", "Gallen", "Marburg", "Zofingen", "Strassburg", "London",
                  "Cambridge", "Winterthur", "Hamburg", "Bern", "Chur", "Weimar", "Paris", "Utrecht", "Dresden",
                  "Kopenhagen", "Dublin", "Prag", "Oxford", "Nr.", "Ms.", "Hr."] + TYPEWRITER_ABBREV + TYPEWRITER_

    PTH_OCR_KRAKEN = "Karteikarten/OCR_Kraken/"

    def __init__(self, path, card_nr):
        self.path = path
        self.card_nr = card_nr
        self.second_try = False
        if path:
            self.input = self.get_data_as_dict(path)
            self.output = self.extract_values()

    def get_data(self): return self.output

    def extract_values(self):
        if self.input:
            data = dict()
            data["year"], data["month"], data["day"] = self.extract_date(self.input, self.card_nr)
            data["a_nn"], data["a_vn"], data["a_ort"], data["a_bem"] = self.analyze_address("Absender")
            data["e_nn"], data["e_vn"], data["e_ort"], data["e_bem"] = self.analyze_address("Empfänger")
            data["a_standort"], data["a_signatur"], data["a_umfang"] = self.extract_ssu("Autograph")
            data["c_standort"], data["c_signatur"], data["c_umfang"] = self.extract_ssu("Kopie")
            data["literatur"] = self.extract_literature()
            data["gedruckt"] = self.extract_printed()
            data["bemerkung"] = self.extract_remark()
            data["sprache"] = self.extract_language(data["bemerkung"])
            return data
        return None

    def get_date(self): return self.output["year"], self.output["month"], self.output["day"]
    def get_sender(self): return self.output["a_nn"], self.output["a_vn"], self.output["a_ort"], self.output["a_bem"]
    def get_receiver(self): return self.output["e_nn"], self.output["e_vn"], self.output["e_ort"], self.output["e_bem"]
    def get_autograph(self): return self.output["a_standort"], self.output["a_signatur"], self.output["a_umfang"]
    def get_copy(self): return self.output["c_standort"], self.output["c_signatur"], self.output["c_umfang"]
    def get_literature(self): return self.output["literatur"]
    def get_printed(self): return self.output["gedruckt"]
    def get_bemerkung(self): return self.output["bemerkung"]
    def get_sprache(self): return self.output["sprache"]

    def get_data_as_string(self, field_id, index, clean=True):
        if index: field_id = ' '.join([field_id, index])
        if field_id in self.input:
            string = ' '.join([token for baseline in self.input[field_id] for token in baseline])
            string = BullingerData.clean_str(re.sub(field_id, '', string)) if clean else string
            return string
        return ''

    def extract_ssu(self, attribute):  # Autograph/Kopie
        index = "A" if attribute == "Autograph" else "B"
        standort = self.get_data_as_string("Standort", index)
        signatur = self.get_data_as_string("Sign.", index)
        umfang = self.get_data_as_string("Umfang", index)
        ssu = ' '.join([standort, signatur, umfang])
        if BullingerData.is_typewriter(ssu):
            for a in BullingerData.TYPEWRITER_ABBREV:
                if a in ssu:
                    standort, signatur = BullingerData.split_string_after(ssu, a)
                    break
        elif BullingerData.is_standort_zsta(standort) or BullingerData.is_signatur_zsta(signatur):
            standort = "Zürich StA"
            num_arabic = re.sub(r'[^\d,f]', '', ssu).strip(',')  # e.g. 666,666ff
            if 'f' in num_arabic: re.sub(r'[f]', '', ssu)+'f'
            num_roman = BullingerData.get_roman_signature(signatur)
            signatur, umfang = ' '.join(['E', num_roman, num_arabic]).strip(), None
        elif BullingerData.is_standort_zzb(standort):
            standort = "Zürich ZB"
            numbers = re.sub(r'[^\d,]', '', standort + signatur + umfang).strip()
            signatur, umfang = ''.join('Ms S ' + numbers).strip(), None
        elif ssu: standort, signatur, umfang = None, None, None
        standort = standort if standort else None
        signatur = signatur if signatur else None
        umfang = umfang if umfang else None
        return standort, signatur, umfang

    @staticmethod
    def split_string_after(string, delimiter):
        splits = re.sub(r'\s+', ' ', string.strip()).split(delimiter)
        return ' '.join(splits[:1]+[delimiter]).strip(), ' '.join(splits[1:]).strip()

    @staticmethod
    def is_typewriter(string):
        for k in BullingerData.TYPEWRITER:
            if k in string: return True
        return False

    @staticmethod
    def is_signatur_zsta(string):
        if string:
            first = string[0:4]
            for char in ['E', '£', '€', 'B', 'A', '4', 'I', 'II', 'T', 'X']:  # EI, EII, AI, AII
                if char in first: return True
        return False

    @staticmethod
    def is_standort_zsta(string):
        if string:
            last = string[-4:]
            for char in ['S', '$', '8', 't', 'A', '4']:  # StA
                if char in last: return True
        return False

    @staticmethod
    def is_standort_zzb(string):
        if string:
            first, last = string[:4], string[-4:]
            for char in ['Z', '2', 'B', '8']:
                if char in last: return True
            for s in ['ZZ', 'Z2', '2Z', '22']:
                if s in first: return True
        return False

    @staticmethod
    def get_roman_signature(str_signature):
        for char in ['II', 'U', 'X', 'T', 'H']:
            if char in str_signature: return 'II'
        return 'I'

    def extract_literature(self):
        if "Literatur" in self.input:
            literature = self.get_data_as_string("Literatur", '', clean=False)
            if BullingerData.is_probably_junk(literature): return None
            literature = BullingerData.clean_str(literature)
            return literature if literature else None
        return None

    def extract_printed(self):
        if "Gedruckt" in self.input:
            literature = self.get_data_as_string("Gedruckt", '', clean=False)
            if BullingerData.is_probably_junk(literature): return None
            literature = BullingerData.clean_str(literature)
            return literature if literature else None
        return None

    def extract_remark(self):
        if 'Bemerkungen' in self.input:
            a, concat = [], [False]
            for baseline in self.input["Bemerkungen"]:
                bl = [BullingerData.clean_str(s) for s in baseline]
                bl = [re.sub('Bemerkung', '', t) for t in bl if t]
                if len(bl) > 0:
                    if bl[-1][-1] == '-':
                        bl[-1] = re.sub('-', '', bl[-1]).strip()
                        concat += [True]
                    else: concat += [False]
                if len(bl) > 0: a.append(bl)
            b = []
            if len(a) > 1:
                for i, bl in enumerate(a):
                    if not concat[i]: b += bl
                    else:
                        b[-1] = b[-1] + str(bl[0])
                        if len(bl) > 1: b += bl[1:]
            remark = BullingerData.remove_leading_junk(' '.join(b))
            remark = remark.replace(' ,', ',').replace(' .', '.').strip()
            return remark if remark else None
        return None

    @staticmethod
    def clean_str(s):
        s = re.sub(r'[^\w\d.,:;\-?!() ]', '', str(s))
        return re.sub(r'\s+', ' ', str(s)).strip()

    @staticmethod
    def is_probably_junk(s):
        tokens, abc123, all_chars = s.split(), re.sub(r'[^\w\d]', '', s), re.sub(r'[\s]', '', s)
        if len(all_chars) == 0 \
                or 0.58 > len(abc123) / len(all_chars) \
                or sum([len(s0) for s0 in tokens])/len(tokens) < 3 \
                or re.match(r'.*[a-z]+[A-Z]+.*', s) \
                or re.match(r'.*\s[^\s]\s.*\s[^\s]\s.*', s):
            return True
        return False

    @staticmethod
    def remove_leading_junk(s):
        s = s.replace('_', ' ')
        m, i = re.match(r'^([^\w\d(.]*)(.*)$', s, re.M | re.I), 0
        if m.group(2):
            while i < len(m.group(2)) and m.group(2)[i] == '.': i += 1
            if i >= 3: return m.group(2)[(i-3):].strip()
            return m.group(2)[i:].strip()
        return s

    def extract_language(self, bemerkung):
        lng = Langid.classify(bemerkung)
        languages = [] if not lng else [lng]
        if "Sprache" in self.input["Sprache"]:
            for lang in self.extract_language_basic():
                if lang not in languages: languages.append(lang)
        return languages

    def extract_language_basic(self):
        baselines = self.input["Sprache"]
        if len(baselines[0]):
            lang, junk = [], []
            s = re.sub("[^A-Za-z]", ' ', ' '.join(baselines[0])).split()
            for t in s:
                t = t.lower()
                if (t in "dts" or t in "deutsch") and "Deutsch" not in lang: lang.append("Deutsch")
                elif t in "lateinisch" and "Latein" not in lang: lang.append("Latein")
                elif t in "griechisch" and "Griechisch" not in lang: lang.append("Griechisch")
                else: junk.append(t)
            # lang += junk
            return lang if len(lang) > 0 else []
        return []

    def analyze_address(self, attribute):
        nn, vn, ort, bemerkung = None, None, None, None
        baselines = self.input["Absender"] if attribute == "Absender" else self.input["Empfänger"]
        baselines = BullingerData.clean_up_baselines_sender_receiver(baselines)
        if len(baselines) > 0:
            # Rule 1 - 1st line 1st word == name
            nn = baselines[0][0].strip()
            if len(baselines[0]) > 1:
                vn = ' '.join(baselines[0][1:]).strip()
                if nn != 'Geistliche':
                    # Title
                    if re.match(r'.*(?:^|\s+)von(?:\s+|$).*', vn):
                        vn = vn.replace('von', '').strip()
                        nn = 'von ' + nn
                    if re.match(r'.*(?:^|\s+)de(?:\s+|$).*', vn):
                        vn = vn.replace('de', '').strip()
                        nn = 'de ' + nn
                    if re.match(r'.*(?:^|\s+)du(?:\s+|$).*', vn):
                        vn = vn.replace('du', '').strip()
                        nn = 'du ' + nn
                    if re.match(r'.*(?:^|\s+)a(?:\s+|$).*', vn):
                        vn = vn.replace('a', '').strip()
                        nn = 'a ' + nn
                    if re.match(r'.*(?:^|\s+)zum(?:\s+|$).*', vn):
                        vn = vn.replace('zum', '').strip()
                        nn = 'zum ' + nn
                else:  # Geistliche
                    ort = vn.replace('von', '').strip()
                    nn = "Geistliche"
        if len(baselines) > 1:
            ort = ' '.join(baselines[-1])
            ort = re.sub(r'\s+', ' ', ort.replace('.', '. ')).strip()
        if len(baselines) > 2: bemerkung = ' '.join([t for b in baselines[1:-1] for t in b]).strip()
        if nn: nn = nn.replace('.', '')
        if vn: vn = vn.replace('.', '')
        if ort: ort = ort.replace('.', '')
        nn = nn if nn and len(nn) > 3 else None
        vn = vn if vn and len(vn) > 2 else None
        ort = ort if ort and len(ort) > 2 else None
        bemerkung = bemerkung if bemerkung else None
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
                    if x in t: legal = False
                if legal and t != '' and t != '.': new_b += [t]
            if new_b: new_baselines += [new_b]
        return new_baselines

    def is_bullinger_sender(self):
        threshold = 0.5
        precision = BullingerData.NG_MAX
        b_n_grams = NGrams.get_ngram_dicts_dicts("Bullinger", precision)
        h_n_grams = NGrams.get_ngram_dicts_dicts("Heinrich", precision)
        if "Absender" in self.input and "Empfänger" in self.input:
            sender = [t for s in self.input["Absender"] for t in s]
            receiver = [t for s in self.input["Empfänger"] for t in s]
            pbs, phs = BullingerData.compute_similarities(sender, precision, b_n_grams, h_n_grams)
            pbr, phr = BullingerData.compute_similarities(receiver, precision, b_n_grams, h_n_grams)
            return max(pbs) + max(phs) > max(pbr) + max(phr)  # match-percentages bullinger/heinrich sender/receiver
        elif "Absender" in self.input:  # Empfänger missing
            sender = [t for s in self.input["Absender"] for t in s]
            pbs, phs = BullingerData.compute_similarities(sender, precision, b_n_grams, h_n_grams)
            return max(pbs)+max(phs) > 2*threshold
        elif "Empfänger" in self.input:  # Absender missing
            receiver = [t for s in self.input["Empfänger"] for t in s]
            pbr, phr = BullingerData.compute_similarities(receiver, precision, b_n_grams, h_n_grams)
            return max(pbr)+max(phr) > 2*threshold
        return False  # dead code

    @staticmethod
    def compute_similarities(tokens, precision, bng, hng):
        pb, ph = [], []
        if not len(tokens): return [0], [0]
        for t in tokens:  # else
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

    def extract_date(self, data, card_nr):
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
            day = None
            for token in data:
                if token.isdigit():
                    if 0 < int(token) < 32:
                        day = int(token)
                        data.remove(token)
                        break
            # correction mechanisms
            if str(BullingerData.year_predicted-1) in data:
                BullingerData.year_predicted -= 1
            if not day and len(data) > 0:
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
            if year: return year, BullingerData.index_predicted+1, day
        if not self.second_try:
            self.second_try = True
            path = BullingerData.PTH_OCR_KRAKEN+'/HBBW_Karteikarte_'+(5-len(str(card_nr)))*'0'+str(card_nr)+'.ocr'
            return self.extract_date(self.get_data_as_dict(path), card_nr)
        return None, None, None

    def get_data_as_dict(self, path):
        data = ListDict()
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
                data.add(attribute, lines)
            return data
        else:
            print("*** Warning, file ignored:", self.path)
            return dict()

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
    '''
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
        else: results += [df]
        return results
    '''
