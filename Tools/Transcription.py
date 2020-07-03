#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Transcriptions.py
# Bernard Schroffenegger
# 2nd of July, 2020

import os, re

class Transcriptions:

    @staticmethod
    def count_elements_file(path, element):
        s, e, cs, ce = "<"+element+">", "</"+element+">", 0, 0
        with open(path) as f:
            for line in f:
                for _ in re.findall(s, line): cs += 1
                for _ in re.findall(e, line): ce += 1
        return cs, ce

    @staticmethod
    def count_elements_dir(root, element):
        cs, ce = 0, 0
        for fn in os.listdir(root):
            if fn != ".DS_Store":
                path = "/".join([root, fn])
                cs_t, ce_t = Transcriptions.count_elements_file(path, element)
                cs, ce = cs+cs_t, ce+ce_t
        return cs, ce

    @staticmethod
    def count_all(root, freq=100):
        # count all opening and closing tags (separately); print corresponding file names
        d = dict()
        for fn in os.listdir(root):
            if fn != ".DS_Store":
                with open(root+"/"+fn) as f:
                    for line in f:
                        for m in re.findall(r'</?\w*>', line): d[m] = d[m]+1 if m in d else 1
        for k, v in sorted(d.items(), key=lambda x: x[1], reverse=True):
            print(k, v)
            files = []
            for fn in os.listdir(root):
                if fn != ".DS_Store":
                    with open(root + "/" + fn) as f:
                        match = False
                        for line in f:
                            if k in line: match=True
                    if match: files.append(fn)
            if len(files) <= freq: print(files)

    @staticmethod
    def eliminate_exceptional_tags(root):
        # <diligenter> ---> diligenter
        with open(root+'/1570_40103_lat.txt') as f:
            data = re.sub(r'<diligenter>', "\"diligenter\"", "".join([line for line in f]))
        with open(root+'/1570_40103_lat.txt', 'w') as f: f.write(data)
        # <piis> ---> "piis"
        with open(root+'/1549_19245_lat.txt') as f:
            data = re.sub(r'<piis>', "\"piis\"", "".join([line for line in f]))
        with open(root+'/1549_19245_lat.txt', 'w') as f: f.write(data)
        # <Lücke> ---> [...]
        with open(root+'/1549_19206_de.txt') as f:
            data = re.sub(r'<Lücke>', "[...]", "".join([line for line in f]))
        with open(root+'/1549_19206_de.txt', 'w') as f: f.write(data)
        # </egr> ---> </gr>
        with open(root+'/1548_18334_de.txt') as f:
            data = re.sub(r'</egr>', "</gr>", "".join([line for line in f]))
        with open(root+'/1548_18334_de.txt', 'w') as f: f.write(data)
        # <f> ---> <f1>
        with open(root+'/1549_19106_lat.txt') as f:
            data = re.sub(r'<f>', "<f1>", "".join([line for line in f]))
        with open(root+'/1549_19106_lat.txt', 'w') as f: f.write(data)
        # <regilionis> --> "regilionis"
        with open(root+'/1549_19294_lat.txt') as f:
            data = re.sub(r'<regilionis>', "\"regilionis\"", "".join([line for line in f]))
        with open(root+'/1549_19294_lat.txt', 'w') as f: f.write(data)
        # </brief> --> None
        with open(root+'/1551_21320_de.txt') as f:
            data = re.sub(r'</brief>', "", "".join([line for line in f]))
        with open(root+'/1551_21320_de.txt', 'w') as f: f.write(data)
        # <text> --> <tx>; </text> --> </tx>
        with open(root+'/1551_21320_de.txt') as f:
            data = re.sub(r'<text>', "<tx>", "".join([line for line in f]))
        with open(root+'/1551_21320_de.txt', 'w') as f: f.write(data)
        with open(root+'/1551_21320_de.txt') as f:
            data = re.sub(r'</text>', "</tx>", "".join([line for line in f]))
        with open(root+'/1551_21320_de.txt', 'w') as f: f.write(data)


    @staticmethod
    def print_contexts(path, elem, f_size=3):
        for fn in os.listdir(path):
            if fn != ".DS_Store":
                with open(path + "/" + fn) as f:
                    hit_loc = (False, None)
                    for i, line in enumerate(f):
                        if elem in line: hit_loc = (True, i)
                if hit_loc[0]:
                    print("\n", fn)
                    with open(path + "/" + fn) as f:
                        for i, line in enumerate(f):
                            if hit_loc[1] - f_size < i < hit_loc[1] + f_size:
                                print(line.strip())

    # corrections
    @staticmethod
    def correct_subscription_tx(root):
        # <un>.*</tx>  --->  <un>.*</un>
        for fn in os.listdir(root):
            if fn != ".DS_Store":
                f_path = root + "/" + fn
                with open(f_path) as f: data = "".join([line for line in f])
                m = re.search(r'(.*<un>[^\n]*)</tx>(.*)', data, re.DOTALL)
                if m:
                    with open(f_path, 'w') as f:
                        f.write(m.group(1) + "</un>" + m.group(2))
                        print(fn, "modified")

    @staticmethod
    def correct_subscription_lz(root):
        # <un> ... <lz> ---> <un> ... </un><lz>
        for fn in os.listdir(root):
            p = root + "/" + fn
            if fn != ".DS_Store":
                with open(p) as f: t = "".join([line for line in f])
                m = re.search(r'(.*<un>[^/]*)(<lz>.*)', t, re.DOTALL)
                if m:
                    with open(p, 'w') as f:
                        f.write(m.group(1) + "</un>\n" + m.group(2))
                        print(fn, "modified")

    @staticmethod
    def correct_lz_end(root):
        # <lz> ... ---> <lz> ... </lz>
        for fn in os.listdir(root):
            p = root + "/" + fn
            if fn != ".DS_Store":
                with open(p) as f: t = "".join([line for line in f])
                m = re.search(r'(.*<lz>[^<>]*)', t, re.DOTALL)
                if m:
                    with open(p, 'w') as f:
                        f.write(m.group(1).strip()+"</lz>\n")
                        print(fn, "modified")

    @staticmethod
    def correct_vo_close(root):
        # <vo> ... ---> <lz> ... </vo>
        for fn in os.listdir(root):
            p = root + "/" + fn
            if fn != ".DS_Store":
                with open(p) as f: t = "".join([line for line in f])
                m = re.search(r'(.*<vo>[^<>\n]*\n)(<[^v].*)', t, re.DOTALL)
                if m:
                    with open(p, 'w') as f:
                        f.write(m.group(1).strip()+"</vo>\n"+m.group(2))
                        print(fn, "modified")

    @staticmethod
    def correct_od_close_vo(root):
        # <od> ... <vo> ---> <od> ... </od><vo>
        for fn in os.listdir(root):
            p = root + "/" + fn
            if fn != ".DS_Store":
                with open(p) as f: t = "".join([line for line in f])
                m = re.search(r'(.*<od>[^<>]*)(<[^/o].*)', t, re.DOTALL)
                if m:
                    with open(p, 'w') as f:
                        f.write(m.group(1).strip()+"</od>\n"+m.group(2))
                        print(fn, "modified")

    @staticmethod
    def annotate_odtx(root):
        # place/date in text
        for fn in os.listdir(root):
            p = root + "/" + fn
            if fn != ".DS_Store":
                with open(p) as f: t = "".join([line for line in f])
                m = re.search(r'(.*)\^\$([\(\)\[\]\w+\s]*?[\.,]?\s*\d{1,2}\.[[\(\)\[\]\w+\s+]*\(?\d{4}\)?\.\s*)(.*)', t, re.DOTALL)
                if m:
                    with open(p, 'w') as f:
                        f.write(m.group(1)+"<odtx>"+m.group(2).strip()+"</odtx>\n"+m.group(3))
                        print(fn, "modified")



    """
    @app.route('/api/process_transcriptions/init', methods=['GET', 'POST'])
    def process_transcriptions_init():
        ctr, out, used = 0, None, []
        with open("Data/TUSTEP/src/hbbw.txt") as f:
            for line in f:
                m = re.match(r'.*<nr>(.*)</nr>.*', line)
                if m:
                    nr = m.group(1).replace('[', '').replace(']', '').strip().replace(" ", '_')
                    if nr in used: nr += "i"
                    used.append(nr)
                    out = "Data/TUSTEP/0_index/"+nr+".txt"
                    ctr += 1
                if out:
                    with open(out, "a") as g:
                        g.write(line)
        print("Number of files created:", ctr)
        print("Exceptional indices:")
        for p in used:
            if '_' in p: print(p)
            if 'i' in p: print(p)
        ctr_open, ctr_closed = 0, 0
        print("Expected number of files:")
        with open("Data/TUSTEP/src/hbbw.txt") as f:
            for line in f:
                if '<nr>' in line: ctr_open += 1
                if '</nr>' in line: ctr_closed += 1
            print("Opening tags:", ctr_open)
            print("Closing tags:", ctr_closed)
        return redirect(url_for('index'))

    def compare_fn_date():
        path, data = "Data/TUSTEP/1_lang", dict()
        for fn in os.listdir(path):
            if fn != ".DS_Store":
                with open(path + "/" + fn) as f:
                    for line in f:
                        if '<od>' in line:
                            m = re.match(r'.*(\d{4,4}).*', line)
                            if m:
                                if fn[:2] in data:
                                    data[fn[:2]].append(m.group(1))
                                else:
                                    data[fn[:2]] = [m.group(1)]
                            print(fn, line.strip())
        for k, v in sorted(data.items()):
        return redirect(url_for('index'))

    def add_year():
        path, data = "Data/TUSTEP/1_lang", dict()
        for fn in os.listdir(path):
            if fn != ".DS_Store" and fn != "17057.txt":
                y = "15" + str(int(fn[:2]) + 30)
                os.rename(path + "/" + fn, path + "/" + y + "_" + fn)
            if fn != "17057.txt": os.rename(path + "/" + fn, path + "/" + "1551" + "_" + fn)
        return redirect(url_for('index'))

    def add_lang():
        path = "Data/TUSTEP/2_index_lang"
        for fn in sorted(os.listdir(path)):
            if fn != ".DS_Store":
                with open(path + "/" + fn) as f:
                    s = ""
                    for line in f:
                        s = s + " " + line.strip()
                    # print(s)
                    print(fn, Langid.classify(s))
                    n = fn.split('.')
                    nfn = n[0] + '_' + Langid.classify(s) + '.txt'
                    os.rename(path + "/" + fn, path + "/" + nfn)

    @app.route('/api/process_transcriptions2', methods=['GET', 'POST'])
    def process_transcriptions2():
        dt = dict()
        with open("Data/TUSTEP/src/hbbw.txt") as f:
            for line in f:
                m = re.match(r'.*</?([\w\d]+)>.*', line)
                if m: dt[m.group(1)] = 1 if m.group(1) not in dt else dt[m.group(1)] + 1
        # for t in dt: print(t, '\t', str(dt[t]) + 'x')
        for x in [(k, v) for k, v in sorted(dt.items(), key=lambda x: x[1], reverse=True)]:
            print(x[0], x[1])
        d = dict()
        for t in [r'.*<nr>.*', r'.*</nr>.*',
                  r'.*<ae>.*', r'.*</ae>.*',
                  r'.*<od>.*', r'.*</od>.*',
                  r'.*<vo>.*', r'.*</vo>.*',
                  r'.*<dr>.*', r'.*</dr>.*',
                  r'.*<re>.*', r'.*</re>.*',
                  r'.*<tx>.*', r'.*</tx>.*',
                  r'.*<un>.*', r'.*</un>.*',
                  r'.*<fx>.*', r'.*</fx>.*',
                  r'.*<fe>.*', r'.*</fe>.*',
                  r'.*<fn>.*', r'.*</fn>.*',
                  r'.*<gr>.*', r'.*</gr>.*',
                  r'.*<hebräisch>.*', r'.*</hebräisch>.*',
                  r'.*<k>.*', r'.*</k>.*',
                  r'.*<f1>.*', r'.*</f1>.*',
                  r'.*<fe>.*', r'.*</fe>.*',
                  r'.*<vl>.*', r'.*</vl>.*',
                  r'.*<lx>.*', r'.*</lx>.*',
                  r'.*<fge>.*', r'.*</fge>.*',
                  r'.*<ge>.*', r'.*</ge>.*',
                  r'.*<p>.*', r'.*</p>.*',
                  r'.*<text>.*', r'.*</text>.*',
                  r'.*<id>.*', r'.*</id>.*',
                  r'.*<brief>.*', r'.*</brief>.*',
                  r'.*<fa>.*', r'.*</fa>.*',
                  r'.*<fr>.*', r'.*<fr/>.*',
                  r'.*<a>.*', r'.*</a>.*',
                  r'.*<qv>.*', r'.*</qv>.*',
                  r'.*<>.*', r'.*</>.*',
                  r'.*<>.*', r'.*</>.*',
                  r'.*<>.*', r'.*</>.*',
                  r'.*<>.*', r'.*</>.*',
                  r'.*<>.*', r'.*</>.*',
                  r'.*<zzl>.*', r'.*</zzl>.*',
                  r'.*<lz>.*', r'.*</lz>.*', "^$"]:
            with open("Data/TUSTEP/src/hbbw.txt") as f:
                for line in f:
                    m = re.match(t, line)
                    if m: d[t] = 1 if t not in d else d[t] + 1
        for t in d: print(t, '\t', str(d[t]) + 'x')
        return redirect(url_for('index'))

    import os
    @app.route('/api/process_transcriptions/nr_tags', methods=['GET', 'POST'])
    def process_transcriptions3():
        path, ctr = "Data/TUSTEP/out1_index", 0
        for fn in os.listdir(path):
            if fn != ".DS_Store":
                with open(path + "/" + fn) as f:
                    lnr = 0
                    for line in f:
                        m = re.match(r'\s?<\s?n\s?r\s?>(.*)<\s?/\s?n\s?r\s?>\s?', line)
                        if m:
                            m2 = re.match(r'<nr>(\d+)</nr>', line)
                            if not m2:
                                print(path, line)
                            ctr += 1
                            if lnr != 0: print(fn)
                    lnr += 1
                    # print(m.group(1))
        print(ctr)
        return redirect(url_for('index'))

    import os
    @app.route('/api/process_transcriptions/ae_tags', methods=['GET', 'POST'])
    def process_transcriptions4():
        path, ctr = "Data/TUSTEP/out1_index", 0
        for fn in os.listdir(path):
            match = False
            if fn != ".DS_Store":
                with open(path + "/" + fn) as f:
                    lnr = 0
                    for line in f:
                        m = re.match(r'\s?<\s?a\s?e\s?>(.*)<\s?/\s?a\s?e\s?>\s?', line)
                        if m:
                            match = True
                            m2 = re.match(r'<ae>(.*)</ae>', line)
                            if not m2:
                                print(path, line)
                        # if lnr != 1: print(fn)
                        ctr += 1
                    lnr += 1
                    if not match: print(fn)
        print(ctr)
        return redirect(url_for('index'))

    @app.route('/api/process_transcriptions/count_nr', methods=['GET', 'POST'])
    def process_transcriptions5():
        ctr_open, ctr_closed = 0, 0
        with open("Data/TUSTEP/src/hbbw.txt") as f:
            for line in f:
                if '<nr>' in line: ctr_open += 1
                if '</nr>' in line: ctr_closed += 1
            print(ctr_open, ctr_closed)
        return redirect(url_for('index'))

    @app.route('/api/process_transcriptions/contract', methods=['GET', 'POST'])
    def process_contractions():
        path = "Data/TUSTEP/4_contractions"
        for p in [['<od>', '</od>'], ['<vo>', '</vo>'], ['<dr>', '</dr>'], ['<re>', '</re>'], ['<un>', '</un>']]:
            start, end = p[0], p[1]
            for fn in os.listdir(path):
                if fn != ".DS_Store":
                    new, hit = "", False
                    c1, c2 = 0, 0
                    with open(path + "/" + fn) as f:
                        # start and end in file?
                        for line in f:
                            if start in line: c1 += 1
                            if end in line: c2 += 1
                    if c1 == 1 and c2 == 1:
                        tmp, started, hit, changed = "", False, True, False
                        with open(path + "/" + fn) as f:
                            for line in f:
                                if start in line and end not in line:
                                    tmp += line.strip()
                                    started = True
                                elif start not in line and end not in line and started:
                                    tmp += line.strip()
                                elif start not in line and end in line and started:
                                    tmp += line
                                    new += tmp
                                    started = False
                                    if tmp: changed = True
                                    tmp = ""
                                else:
                                    new += line
                        if hit and changed:
                            with open(path + "/" + fn, 'w') as f:
                                f.write(new)
                            print("Changed:", fn)
        # TEst: 1548_18312_de.txt
        return redirect(url_for('index'))

    @app.route('/api/process_transcriptions/add_od', methods=['GET', 'POST'])
    def add_od():
        # 3059
        path, ctr = "Data/TUSTEP/5_od2", 0
        for p in [['<od>', '</od>']]:
            start, end = p[0], p[1]
            for fn in os.listdir(path):
                case = False
                if fn != ".DS_Store":
                    c1, c2 = 0, 0
                    with open(path + "/" + fn) as f:
                        # start and end in file?
                        for line in f:
                            if start in line: c1 += 1
                            if end in line: c2 += 1
                    if c1 == 0 and c2 == 0:
                        with open(path + "/" + fn) as f:
                            data = [line for line in f]
                            if len(data) > 2:
                                m = re.match(
                                    r'[(\[]?\w+[)\]]?,\s+[(\[]?\d{1,2}[()\]]?\.\s*[(\[]?\w+[)\]]?\s*[(\[]?\d{4,4}[()\]]?\.',
                                    data[2])
                                if m:
                                    case = True
                                    ctr += 1
                                    data[2] = start + data[2].strip() + end + "\n"
                                    print(data[2].strip())
                        if case:
                            with open(path + "/" + fn, 'w') as f:
                                f.write("".join(data))
                            print("Changed:", fn, data[2])
        print(ctr)
        # TEst: 1548_18312_de.txt
        return redirect(url_for('index'))

    @app.route('/api/process_transcriptions/add_vo', methods=['GET', 'POST'])
    def add_vo():
        # 2397
        path, ctr = "Data/TUSTEP/6_autvo", 0
        for p in [['<vo>', '</vo>']]:
            start, end = p[0], p[1]
            for fn in os.listdir(path):
                case = False
                if fn != ".DS_Store":
                    c1, c2 = 0, 0
                    with open(path + "/" + fn) as f:
                        # start and end in file?
                        for line in f:
                            if start in line: c1 += 1
                            if end in line: c2 += 1
                    with open(path + "/" + fn) as f:
                        # start and end in file?
                        data, hit = [line for line in f], False
                        for i, line in enumerate(data):
                            if line.strip() == "(Aut.)":
                                data = data[:i] + data[i + 1:]
                                data[i - 1] = data[i - 1].strip() + "(Aut.)\n"
                                hit = True
                                break
                        if hit:
                            with open(path + "/" + fn, 'w') as f:
                                f.write("".join(data))
                            print("Aut:", fn)
                    if c1 == 0 and c2 == 0:
                        with open(path + "/" + fn) as f:
                            data = [line for line in f]
                            if len(data) > 3:
                                m1 = re.match(r'Zürich StA,.*Orig.(Aut.)', data[3])
                                m1 = re.match(r'Zürich.*\d{3}\.', data[3])
                                if m1:
                                    case = True
                                    ctr += 1
                                    data[3] = start + data[3].strip() + end + "\n"
                                    print(data[3].strip())
                        if case:
                            with open(path + "/" + fn, 'w') as f:
                                f.write("".join(data))
                            print("Changed:", fn, data[3])
        print(ctr)
        # TEst: 1548_18312_de.txt
        return redirect(url_for('index'))

    @app.route('/api/process_transcriptions/add_un1', methods=['GET', 'POST'])
    def add_un1():
        # <un>.*</tx>  --->  <un>.*</un>
        path = "Data/TUSTEP/7_un"
        for fn in os.listdir(path):
            hit_pos = (False, None)
            if fn != ".DS_Store":
                with open(path + "/" + fn) as f:
                    for i, line in enumerate(f):
                        m = re.match(r'^\s*?<un>.*</tx>\s*?$', line)
                        if m:
                            print("\n", fn)
                            print("OLD", line)
                            hit_pos = (True, i)
                if hit_pos[0]:
                    with open(path + "/" + fn) as f:
                        data = [line for line in f]
                        data[hit_pos[1]] = re.sub(r'\s*</tx>\s*$', "</un>", data[hit_pos[1]])
                        print("NEW", data[hit_pos[1]])
                    with open(path + "/" + fn, 'w') as f:
                        f.write("".join(data))
        return redirect(url_for('index'))

    @app.route('/api/process_transcriptions/add_un2', methods=['GET', 'POST'])
    def add_un2():
        # <un>...\n<lz>  --->  <un>...</un>\n<lz>
        path = "Data/TUSTEP/7_un"
        for fn in os.listdir(path):
            if fn != ".DS_Store":
                with open(path + "/" + fn) as f:
                    data = "".join([line for line in f])
                m = re.search(r'(.*<un>[^\n]*)(\n<lz>.*)', data, re.DOTALL)
                if m:
                    with open(path + "/" + fn, 'w') as f:
                        f.write(m.group(1) + "</un>" + m.group(2))
                        print(fn)
        return redirect(url_for('index'))



    # <un>Tuus Ambrosius Blaurer.</UN>
    # ^$Claudius zögt an, das man ...
    """
