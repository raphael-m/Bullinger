#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# xml.py
# Bernard Schroffenegger
# 24th of September, 2019

""" analyzing XML files """

import statistics
import xml.sax
import pandas as pd
import matplotlib.pyplot as plt

from xml.sax.handler import ContentHandler
from Tools.FileSystem import FileSystem
from Tools.Dictionaries import CountDict
from Tools.Dictionaries import ListDict


class Analyzer4XML:

    PRECISION = 3  # rounding
    SCHEMA = ["Attribut", "Mittelwert", "Standardabweichung"]
    SCATTER_V1, SCATTER_V2 = "scatter_v1.png", "scatter_v2.png"
    X_DISTRIBUTION_V1, Y_DISTRIBUTION_V1 = "x_distribution_v1.png", "y_distribution_v1.png"
    X_DISTRIBUTION_V2, Y_DISTRIBUTION_V2 = "x_distribution_v2.png", "y_distribution_v2.png"
    FIELDS = "fields.png"

    ATTRIBUTES = ["Datum", "Absender", "Empfänger", "Autograph", "Kopie", "Photokopie",
                  "Standort", "Bull.", "Corr.", "Sign.", "Abschrift", "Umfang", "Sprache",
                  "Literatur", "Gedruckt", "Bemerkungen"]

    def __init__(self):
        pass

    @staticmethod
    def compute_avg_page_dim(dir_path, dir_out, filter=False):
        """ mean/std-dev of page height & width
            :param dir_path: <string>
            :param dir_out: <string>
            :return: <pd.DataFrame> """
        out = dir_out+"page_size_adjusted.png" if filter else dir_out+"page_size.png"
        d = ListDict()
        x_max, y_max, x_min, y_min = -1, -1, 10**4, 10**4
        for path in FileSystem.get_file_paths(dir_path):
            dims = BullingerPage.get_dimensions(path)
            if filter and dims['x'][0] < 9000 and dims['x'][0] < 6000:
                print("Found:", dims['x'][0], dims['y'][0], path)
                continue
            x_max = dims['x'][0] if dims['x'][0] > x_max else x_max
            y_max = dims['y'][0] if dims['y'][0] > y_max else y_max
            x_min = dims['x'][0] if dims['x'][0] < x_min else x_min
            y_min = dims['y'][0] if dims['y'][0] < y_min else y_min
            d = ListDict.combine([dims, d])
        data = Analyzer4XML.compute_stats(d)
        data['Minimum'] = [y_min, x_min]
        data['Maximum'] = [y_max, x_max]
        data.set_index('Mittelwert')
        # print(data.to_latex(index=False))
        plt.scatter(d['x'], d['y'], alpha=0.7, s=len(d['y']) * [10], color="blue")
        plt.scatter(list(data['Mittelwert'])[1], list(data['Mittelwert'])[0], alpha=0.4, s=len(d['y']) * [200], color="red")
        plt.xlabel('x [px]')
        plt.ylabel('y [px]')
        fig = plt.gcf()  # get current figure
        if dir_out:  # write to file
            plt.draw()
            fig.savefig(out, dpi=100)
        plt.show()

    @staticmethod
    def create_plots_for_attributes(dir_path, out_path=None):
        for j in range(0, 4):
            fig = plt.figure()
            for i, attribute in enumerate(Analyzer4XML.ATTRIBUTES[0+4*j:4+4*j]):
                ld = ListDict()
                plt.subplot(2, 2, i + 1)
                for path in FileSystem.get_file_paths(dir_path):
                    ld = ListDict.combine([ld, BullingerAttributes.get_attribute_coordinates(path, attribute)])
                plt.scatter(ld['x'], ld['y'], alpha=0.1, s=len(ld['x']) * [100], color='blue')
                Analyzer4XML.draw_fields(plt)
                fig.add_subplot(2, 2, i + 1)
                # plt.ylabel("y [px]")
                # plt.xlabel("x [px]")
                plt.xticks([])
                plt.yticks([])
                axes = plt.gca()
                axes.set_xlim([0, 9903])
                axes.set_ylim([0, 7013])
                plt.ylim(plt.ylim()[::-1])  # reverse y-axis
                plt.title(attribute)
            if out_path:
                plt.draw()
                fig.savefig(out_path+"attributes_"+str(j), dpi=100)
            plt.show()

    @staticmethod
    def get_text_coordinates(dir_path_in, version=1):
        parser = BPV1 if version is 1 else BPV2
        data = pd.DataFrame({'x': [], 'y': []})
        for path in FileSystem.get_file_paths(dir_path_in):
            df = parser.get_coordinates(path)
            data = pd.concat([data, df])
        return data

    @staticmethod
    def get_attribute_name(hpos_t, vpos_r, height_b, width_l, version=2):
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
        if mx <= 3057:  # 1st column
            if my <= 1535: return "Datum", None
            elif my <= 2041: return "Autograph", None
            elif my <= 2547: return "Standort", 'A'
            elif my <= 3053: return "Sign.", 'A'
            elif my <= 3559: return "Umfang", 'A'
            elif my <= 4257: return "Sprache", None
            else: return "Gedruckt", None
        elif mx <= 6508:  # 2nd column
            if my <= 1535: return "Absender", None
            elif my <= 2041: return "Kopie", None
            elif my <= 2547: return "Standort", 'B'
            elif my <= 3053: return "Sign.", 'B'
            elif my <= 3559: return "Umfang", 'B'
            elif my <= 5303: return "Literatur", None
            else: return "Bemerkungen", None
        else:  # 3rd column
            if my <= 1535: return "Empfänger", None
            elif my <= 2041: return "Photokopie", None
            elif my <= 2547: return "Bull. Corr.", 'A'
            elif my <= 3053: return "Abschrift", None
            elif my <= 3559: return "Bull. Corr.", 'B'
            elif my <= 5303: return "Literatur", None
            else: return "Bemerkungen", None


    @staticmethod
    def calculate_element_stats(dir_path):
        """ computes mean & standard deviation (element counts) over multiple files
            :param dir_path: <string>. Directory with xml-files
            :return: <pd.DataFrame> """
        count_dicts = [ElementCounter.count(path) for path in FileSystem.get_file_paths(dir_path)]
        data = Analyzer4XML.compute_stats(ListDict.combine(count_dicts))
        print(data.to_latex())

    @staticmethod
    def compute_stats(list_dict):
        """ computes averages and standard deviations
            :param list_dict: key <string> (classifier) --> value <num-list> (data points)
            :return: <DataFrame> """
        s = Analyzer4XML.SCHEMA
        data = pd.DataFrame(columns=s)
        for key in list_dict:
            mean = round(sum(list_dict[key])/len(list_dict[key]), Analyzer4XML.PRECISION)
            std_dev = round(statistics.stdev(list_dict[key]), Analyzer4XML.PRECISION)
            data = pd.concat([data, pd.DataFrame({s[0]: [key], s[1]: [mean], s[2]: std_dev})])
        return data

    @staticmethod  # OCR-V1
    def calculate_focus_points_v1(dir_path_in, dir_path_out):
        """ OCR-mass points (x,y) of all xml-files in <dir_path>
            :param dir_path_in: <string>
            :param dir_path_out: <string>
            :return: show/save plot """
        data = Analyzer4XML.get_text_coordinates(dir_path_in, version=1)
        Analyzer4XML.draw_scatter_plot(
            data['x'].to_list(), data['y'].to_list(),
            out_dir=dir_path_out+Analyzer4XML.SCATTER_V1)
        Analyzer4XML.draw_histogram(data['x'], 'x', out_dir=dir_path_out + Analyzer4XML.X_DISTRIBUTION_V1)
        Analyzer4XML.draw_histogram(data['y'], 'y', out_dir=dir_path_out + Analyzer4XML.Y_DISTRIBUTION_V1)

    @staticmethod  # OCR-V2
    def calculate_focus_points_v2(dir_path_in, dir_path_out):
        data = Analyzer4XML.get_text_coordinates(dir_path_in, version=2)
        Analyzer4XML.draw_scatter_plot(
            data['x'].to_list(), data['y'].to_list(),
            out_dir=dir_path_out+Analyzer4XML.SCATTER_V2)
        Analyzer4XML.draw_histogram(data['x'], 'x', out_dir=dir_path_out + Analyzer4XML.X_DISTRIBUTION_V2)
        Analyzer4XML.draw_histogram(data['y'], 'y', out_dir=dir_path_out + Analyzer4XML.Y_DISTRIBUTION_V2)

    @staticmethod
    def plot_fields(dir_path_in, dir_path_out):
        data = Analyzer4XML.get_text_coordinates(dir_path_in, version=2)
        Analyzer4XML.draw_scatter_plot2(data['x'], data['y'], out_dir=dir_path_out + Analyzer4XML.FIELDS)

    @staticmethod
    def determine_gaps(dir_path_in, version=2, dir_out=None):
        data = Analyzer4XML.get_text_coordinates(dir_path_in, version=version)
        x = data['y'].to_list()
        df = pd.DataFrame(columns=['i', 'y'])
        ranges = list(range(200, 500))+list(range(500, 750))+list(range(750, 1000, 5))\
                 + list(range(1000, 1500, 10))+list(range(1500, 2000, 15))+list(range(2000, 2500, 20))
        for n_bins in ranges:
            print(n_bins)
            ns, bins, bars = plt.hist(x, n_bins)
            plt.close()
            for i, n in enumerate(ns):
                if int(n) is 0:
                    d = pd.DataFrame({'i': [n_bins], 'y': [int((bins[i]+bins[i+1])/2)]})
                    df = pd.concat([df, d])
                    # df = df.reset_index()
        plt.scatter(df['y'], df['i'], alpha=0.4, s=len(df['i']) * [1])  # corrected
        plt.xlabel('Koordinate y [px]')
        plt.ylabel('#Buckets [IN]')
        fig = plt.gcf()  # get current figure
        if dir_out:  # write to file
            plt.draw()
            fig.savefig(dir_out+"gaps_y.png", dpi=100)
        plt.show()

    @staticmethod
    def compute_average_attribute_coordinates(dir_in, dir_out=None):
        """ data/plots
            :param dir_in: <string>. Path
            :param dir_out: <string>. Path
            :return: 2x <DataFrame>, [Attributname, mean, stddev] (für x/y)"""

        # All OCR-text Elements
        c = Analyzer4XML.get_text_coordinates(dir_in, version=2)

        # Attribute Coordinates: Mean & Standard Deviation
        l_dicts = [BPV2Attributes.get_data(path) for path in FileSystem.get_file_paths(dir_in)]
        l_dict = ListDict.combine(l_dicts)
        x_dict = {key: tuple(zip(*l_dict[key]))[0] for key in l_dict}
        y_dict = {key: tuple(zip(*l_dict[key]))[1] for key in l_dict}
        x_stats, y_stats = Analyzer4XML.compute_stats(x_dict), Analyzer4XML.compute_stats(y_dict)
        x_e, y_e = pd.DataFrame(columns=Analyzer4XML.SCHEMA), pd.DataFrame(columns=Analyzer4XML.SCHEMA)

        # Biased Data
        for e in ['Standort', 'Sign.', 'Umfang', 'Bull.', 'Corr.']:
            x_e = pd.concat([x_e, x_stats[x_stats.Attribut == e]])
            y_e = pd.concat([y_e, y_stats[y_stats.Attribut == e]])
            x_stats = x_stats[x_stats.Attribut != e]
            y_stats = y_stats[y_stats.Attribut != e]

        # Linear Separation
        dict_lx, dict_ly, dict_rx, dict_ry = ListDict(), ListDict(), ListDict(), ListDict()
        for e in ['Standort', 'Sign.', 'Umfang']:  # vertically (left/right)
            data_l = tuple(zip(*[pair for pair in l_dict[e] if pair[0] < 2000 < pair[1]]))
            data_r = tuple(zip(*[pair for pair in l_dict[e] if pair[0] >= 2000 and pair[1] > 2000]))
            dict_lx[e], dict_ly[e], dict_rx[e], dict_ry[e] = data_l[0], data_l[1], data_r[0], data_r[1]
        dict_tx, dict_ty, dict_bx, dict_by = ListDict(), ListDict(), ListDict(), ListDict()
        for e in ['Bull.', 'Corr.']:  # horizontally (top/bottom)
            data1 = tuple(zip(*[pair for pair in l_dict[e] if pair[1] < 3000 and pair[0] > 6000]))
            data2 = tuple(zip(*[pair for pair in l_dict[e] if pair[1] >= 3000 and pair[0] > 6000]))
            dict_tx[e], dict_ty[e], dict_bx[e], dict_by[e] = data1[0], data1[1], data2[0], data2[1]

        # Corrected Attributes: Mean & Standard Deviation
        lx, ly = Analyzer4XML.compute_stats(dict_lx), Analyzer4XML.compute_stats(dict_ly)
        rx, ry = Analyzer4XML.compute_stats(dict_rx), Analyzer4XML.compute_stats(dict_ry)
        tx, ty = Analyzer4XML.compute_stats(dict_tx), Analyzer4XML.compute_stats(dict_ty)
        bx, by = Analyzer4XML.compute_stats(dict_bx), Analyzer4XML.compute_stats(dict_by)

        # Plots
        m, c1, c2, c3, c4 = 'Mittelwert', 'cornflowerblue', 'slategrey', 'black', 'green'
        # Analyzer4XML.plot_attributes(coords['x'], coords['y'], x_stats, y_stats, x_e, y_e, dir_out=dir_out)
        plt.scatter(c['x'], c['y'], alpha=0.1, s=len(c['x'].to_list())*[1])  # all
        plt.scatter(x_stats[m], y_stats[m], alpha=0.7, s=len(x_stats[m])*[100], color=c3)  # mean
        # plt.scatter(x_e[m], y_e[m], alpha=0.4, s=len(y_e[m])*[100], color='red')  # errors
        plt.scatter(lx[m], ly[m], alpha=0.7, s=len(lx[m])*[100], color=c4)  # corrected
        plt.scatter(rx[m], ry[m], alpha=0.7, s=len(rx[m])*[100], color=c4)
        plt.scatter(tx[m], ty[m], alpha=0.7, s=len(tx[m])*[100], color=c4)
        plt.scatter(bx[m], by[m], alpha=0.7, s=len(bx[m])*[100], color=c4)

        # Output
        plt.xlabel('x [px]')
        plt.ylabel('y [px]')
        plt.ylim(plt.ylim()[::-1])  # reverse y-axis
        fig = plt.gcf()  # get current figure
        if dir_out:  # write to file
            plt.draw()
            fig.savefig(dir_out+"ocr_attributes_2.png", dpi=100)
        plt.show()

        # Final Data
        # print(pd.concat([x_stats, lx, rx, tx, bx]).to_latex(index=None))
        # print(pd.concat([y_stats, ly, ry, ty, by]).to_latex(index=None))
        return pd.concat([x_stats, lx, rx, tx, bx]), pd.concat([y_stats, ly, ry, ty, by])

    @staticmethod
    def plot_attributes(x, y, x_stats, y_stats, x_e, y_e, dir_out=None):
        plt.scatter(x, y, alpha=0.2, s=len(x.to_list())*[3])
        plt.scatter(x_stats['Mittelwert'], y_stats['Mittelwert'], alpha=1, s=len(x_stats['Mittelwert']) * [100], color='black')
        plt.scatter(x_e['Mittelwert'], y_e['Mittelwert'], alpha=0.4, s=len(y_e['Mittelwert']) * [100], color='red')
        plt.ylim(plt.ylim()[::-1])  # reverse y-axis
        plt.xlabel('x [px]')
        plt.ylabel('y [px]')
        fig = plt.gcf()  # get current figure
        if dir_out:
            plt.draw()
            fig.savefig(dir_out+"ocr_attributes_1.png", dpi=100)
        plt.show()

    @staticmethod
    def draw_scatter_plot(x, y, out_dir=None):
        plt.scatter(x, y, alpha=0.5, s=len(x)*[10])
        plt.ylim(plt.ylim()[::-1])  # reverse y-axis
        plt.xlabel('x [px]')
        plt.ylabel('y [px]')
        Analyzer4XML.draw_fields(plt)
        fig = plt.gcf()  # get current figure
        if out_dir:
            plt.draw()
            fig.savefig(out_dir, dpi=100)
        plt.show()

    @staticmethod
    def draw_scatter_plot2(x, y, out_dir=None):
        plt.scatter(x, y, alpha=0.5, s=len(x)*[10])
        plt.ylim(plt.ylim()[::-1])  # reverse y-axis
        plt.xlabel('x [px]')
        plt.ylabel('y [px]')
        Analyzer4XML.draw_fields(plt)
        fig = plt.gcf()  # get current figure
        if out_dir:
            plt.draw()
            fig.savefig(out_dir+Analyzer4XML.FIELDS, dpi=100)
        plt.show()

    @staticmethod
    def draw_fields(plt):
        x0, x1, x2, x3 = 0, 3057, 6508, 9860
        y0, y1, y2, y3, y4, y5, y6, y7, y8 = 0, 1535, 2041, 2547, 3053, 3559, 4257, 5303, 6978

        # Vertical Lines
        plt.plot((x0, x0), (y0, y8), 'k-', alpha=0.3)
        plt.plot((x1, x1), (y0, y8), 'k-', alpha=0.3)
        plt.plot((x2, x2), (y0, y8), 'k-', alpha=0.3)
        plt.plot((x3, x3), (y0, y8), 'k-', alpha=0.3)

        # Horizontal Lines
        plt.plot((x0, x3), (y0, y0), 'k-', alpha=0.3)  # top
        plt.plot((x0, x3), (y1, y1), 'k-', alpha=0.3)
        plt.plot((x0, x3), (y2, y2), 'blue', alpha=0.3)
        plt.plot((x0, x3), (y3, y3), 'blue', alpha=0.3)
        plt.plot((x0, x3), (y4, y4), 'blue', alpha=0.3)
        plt.plot((x0, x3), (y5, y5), 'k-', alpha=0.3)
        plt.plot((x0, x1), (y6, y6), 'k-', alpha=0.3)
        plt.plot((x1, x3), (y7, y7), 'k-', alpha=0.3)
        plt.plot((x0, x3), (y8, y8), 'k-', alpha=0.3)

    @staticmethod
    def draw_histogram(x, x_name, out_dir=None):
        fig = plt.figure()
        for i, n_bins in enumerate([10**i for i in range(1, 5)]):
            plt.subplot(2, 2, i+1)
            plt.hist(x, n_bins, facecolor='green', alpha=0.5)
            p = fig.add_subplot(2, 2, i+1)
            p.title.set_text(str(n_bins)+" Buckets")
            if i < 2:
                plt.xticks([])
            if i is 0 or i is 2:
                plt.ylabel("Frequency")
            if i is 2 or i is 3:
                plt.xlabel(x_name + " [px]")
        if out_dir:
            plt.draw()
            fig.savefig(out_dir, dpi=100)
        plt.show()


class ElementCounter(ContentHandler):

    """ counts XML-elements """

    def __init__(self):
        super(ElementCounter, self).__init__()
        self.elements = CountDict()
        # self.attributes = CountDict()
        # self.values = CountDict()

    def startElement(self, name, attributes):
        self.elements.add(name)
        # for a in attributes:
        #    self.attributes[a] += 1
        #    self.values[attributes[a]] += 1

    @staticmethod
    def count(path):
        """ elements and their frequencies
            :param path: <string> (xml-file)
            :return: <CountingDict> """
        try:
            parser = xml.sax.make_parser()
            handler = ElementCounter()
            parser.setContentHandler(handler)
            parser.parse(path)
            return handler.elements
        except (AttributeError, TypeError):
            print("Warning: Parser failed on", path)
            return None


# Bullinger Parser  V2
class BPV2(ContentHandler):

    """ Elements: <String CONTENT="Johannes" HEIGHT="152" WIDTH="960" VPOS="554" HPOS="4526"/>
        --> mass points (x, y) """

    def __init__(self):
        super(BPV2, self).__init__()
        self.data = pd.DataFrame({'x': [], 'y': []})

    def startElement(self, name, attributes):
        if name == "String" and "STYLE" not in attributes.getNames():
            hpos, vpos, height, width = 0, 0, 0, 0
            for a in attributes.getNames():
                if a == "HPOS":
                    hpos = int(attributes.getValue(a))
                elif a == "VPOS":
                    vpos = int(attributes.getValue(a))
                elif a == "HEIGHT":
                    height = int(attributes.getValue(a))
                elif a == "WIDTH":
                    width = int(attributes.getValue(a))
            x, y = int(hpos + 0.5*width), int(vpos + 0.5*height)
            data = pd.DataFrame({'x': [x], 'y': [y]})
            self.data = pd.concat([self.data, data])

    @staticmethod
    def get_coordinates(path):
        try:
            parser = xml.sax.make_parser()
            counter = BPV2()
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.data
        except (AttributeError, TypeError):
            print("Warning: xml-sax-parser failed on", path)
            return None


class BPV1(ContentHandler):

    def __init__(self):
        super(BPV1, self).__init__()
        self.data = pd.DataFrame({'x': [], 'y': []})
        self._charBuffer = []
        self._result = []
        self.bool = False

    def startElement(self, name, attributes):
        if name == "line":
            self.t, self.l, self.r, self.b = 0, 0, 0, 0
            for a in attributes.getNames():
                if a == "t":
                    self.t = int(attributes.getValue(a))
                elif a == "r":
                    self.r = int(attributes.getValue(a))
                elif a == "b":
                    self.b = int(attributes.getValue(a))
                elif a == "l":
                    self.l = int(attributes.getValue(a))

    def endElement(self, name):
        if name == 'line':
            data = pd.DataFrame({'x': [int((self.r+self.l)/2)], 'y': [int((self.b+self.t)/2)]})
            self.data = pd.concat([self.data, data])

    def _getCharacterData(self):
        data = ''.join(self._charBuffer).strip()
        self._charBuffer = []
        return data.strip()

    def characters(self, data):
        self._charBuffer.append(data)

    @staticmethod
    def get_coordinates(path):
        try:
            parser = xml.sax.make_parser()
            counter = BPV1()
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.data
        except (AttributeError, TypeError):
            print("Warning: parser failed on", path)
            return None


class BPV2Attributes(ContentHandler):

    """ Elements:
            <String CONTENT="Johannes" HEIGHT="152" WIDTH="960" VPOS="554" HPOS="4526"/>
        --> avg. (x, y) = f(attribute_name)  """

    NAMES = ["Datum", "Absender", "Empfänger", "Autograph", "Kopie", "Photokopie",
             "Standort", "Bull.", "Corr.", "Sign.", "Abschrift", "Umfang", "Sprache",
             "Literatur", "Gedruckt", "Bemerkungen"]

    def __init__(self):
        super(BPV2Attributes, self).__init__()
        self.l_dict = ListDict()

    def startElement(self, name, attributes):
        if name == "String" and "STYLE" not in attributes.getNames():
            key, value, hpos, vpos, height, width = None, None, 0, 0, 0, 0
            for a in attributes.getNames():
                key = attributes.getValue(a)
                if a == "CONTENT" and key in self.NAMES:
                    value = str(key)
                elif a == "HPOS":
                    hpos = int(key)
                elif a == "VPOS":
                    vpos = int(key)
                elif a == "HEIGHT":
                    height = int(key)
                elif a == "WIDTH":
                    width = int(key)
            if key is not None and value is not None:
                x, y = BPV2Attributes.get_mass_point(hpos, vpos, width, height)
                self.l_dict.add(value, (x, y))

    @staticmethod
    def get_mass_point(hpos, vpos, width, height):
        return int(hpos + 0.5*width), int(vpos + 0.5*height)

    @staticmethod
    def get_data(path):
        try:
            parser = xml.sax.make_parser()
            counter = BPV2Attributes()
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.l_dict
        except (AttributeError, TypeError):
            print("Warning: parser failed on", path)
            return None


class BullingerPage(ContentHandler):

    """ Computes avg page dimensions (x_may, y_may) [px] """

    def __init__(self, path):
        super(BullingerPage, self).__init__()
        self.l_dict = ListDict()  # x, y
        self.path = path

    def startElement(self, name, attributes):
        if name == "Page":
            for a in attributes.getNames():
                if a == "WIDTH":
                    self.l_dict.add('x', int(attributes.getValue(a)))
                if a == "HEIGHT":
                    self.l_dict.add('y', int(attributes.getValue(a)))
                    if int(attributes.getValue(a)) == 3488:
                        print(self.path)

    @staticmethod
    def get_dimensions(path):
        try:
            parser = xml.sax.make_parser()
            counter = BullingerPage(path)
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.l_dict
        except (AttributeError, TypeError):
            print("Warning: parser failed on", path)
            return None


class BullingerAttributes(ContentHandler):


    def __init__(self, path, attr):
        super(BullingerAttributes, self).__init__()
        self.l_dict = ListDict()  # x, y
        self.path = path
        self.attr = attr

    def startElement(self, name, attributes):
        if name == "String":
            key, value, hpos, vpos, height, width = None, None, 0, 0, 0, 0
            for a in attributes.getNames():
                key = attributes.getValue(a)
                if a == "CONTENT" and key == self.attr:
                    value = str(key)
                elif a == "HPOS":
                    hpos = int(key)
                elif a == "VPOS":
                    vpos = int(key)
                elif a == "HEIGHT":
                    height = int(key)
                elif a == "WIDTH":
                    width = int(key)
            if value:
                x, y = BPV2Attributes.get_mass_point(hpos, vpos, width, height)
                self.l_dict.add('x', x)
                self.l_dict.add('y', y)

    @staticmethod
    def get_attribute_coordinates(path, attr_name):
        try:
            parser = xml.sax.make_parser()
            counter = BullingerAttributes(path, attr_name)
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.l_dict
        except (AttributeError, TypeError):
            print("Warning: parser failed on", path)
            return None
