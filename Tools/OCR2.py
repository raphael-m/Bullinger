#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# OCR2.py
# Bernard Schroffenegger
# 5th of October, 2019

""" Bullinger Parser OCR-V2 """

import re
import pandas as pd
import xml.sax
from xml.sax.handler import ContentHandler
from Tools.FileSystem import FileSystem


class OCR2:

    """ ocr file analysis """

    SCHEMA = ['Path', 'x', 'y']

    def __init__(self):
        pass

    @staticmethod
    def get_page_size(path):
        """ <page width="9849" height="6989" resolution="1200"> """
        size = PageSizeParser2.get_size(path)
        if size is not None:
            return list(size.loc[0, 'x':'y'])  # width/height
        else: return None

    @staticmethod
    def get_page_sizes(directory):
        """ :param directory: <str>; Path """
        data = pd.DataFrame(columns=OCR2.SCHEMA)
        outliers = []
        for path in FileSystem.get_file_paths(directory):
            size = PageSizeParser2.get_size(path)
            if size.iloc[0]['x'] < 9000 or size.iloc[0]['y'] > 10000:
                match = re.search(r'(\d+)', path)
                if match:
                    outliers.append(int(match.group(1)))
                print(path, size.iloc[0]['x'], size.iloc[0]['y'])
            data = pd.concat([data, size])
        print(outliers)
        return data

    @staticmethod
    def get_text_positions(path, scaling):
        return TextPositionParser2.get_coordinates(path, scaling)

    @staticmethod
    def get_attr_positions(path, scaling, inverse=False):
        return AttributePositionParser.get_attributes(path, scaling, inverse=inverse)


class PageSizeParser2(ContentHandler):

    """ path --> page size (x_max, y_max) [px] """

    def __init__(self, path):
        super(PageSizeParser2, self).__init__()
        self.data = pd.DataFrame(columns=OCR2.SCHEMA)
        self.path = path  # exceptions

    def startElement(self, element, attributes):
        """ <page> --> (height/width). E.g. <page width="9849" height="6989" resolution="1200"> """
        if element.lower() == "page":
            height, width = -1, -1
            for a in attributes.getNames():
                if a.lower() == "width":
                    width = int(attributes.getValue(a))
                if a.lower() == "height":
                    height = int(attributes.getValue(a))
            if width and height:
                d = {OCR2.SCHEMA[0]: [self.path], OCR2.SCHEMA[1]: [width], OCR2.SCHEMA[2]: [height]}
                self.data = pd.concat([self.data, pd.DataFrame(d)])
            else:
                print("*** Warning: corrupt <page> data. See", self.path)

    @staticmethod
    def get_size(path):
        try:
            parser = xml.sax.make_parser()
            counter = PageSizeParser2(path)
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.data
        except:
            print("*** Warning: parser (page size) failed on", path)
            return None


class TextPositionParser2(ContentHandler):

    """ (path, scaling) {[content, h, w, vp, hp]} --> {(content, x, y)} mass-points """

    def __init__(self, scaling):
        super(TextPositionParser2, self).__init__()
        self.data = pd.DataFrame({'content': [], 'x': [], 'y': []})
        self.scaling = scaling

    def startElement(self, name, attributes):
        if name == "String" and "STYLE" not in attributes.getNames():
            d = dict()
            for a in attributes.getNames():
                if a in ["HPOS", "VPOS", "HEIGHT", "WIDTH"]:
                    d[a] = int(attributes.getValue(a))
                if a in ["CONTENT"]:
                    d[a] = str(attributes.getValue(a))
            x, y = d["HPOS"] + 0.5*d["WIDTH"], d["VPOS"] + 0.5*d["HEIGHT"]
            x, y = int(self.scaling[0]*x), int(self.scaling[1]*y)
            if d['CONTENT'] != '-':
                data = pd.DataFrame({'content': [d["CONTENT"]], 'x': [x], 'y': [y]})
                self.data = pd.concat([self.data, data])

    @staticmethod
    def get_coordinates(path, scaling):
        try:
            parser = xml.sax.make_parser()
            counter = TextPositionParser2(scaling)
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.data
        except:
            print("*** Warning: position-parser failed on", path)
            return None


class AttributePositionParser(ContentHandler):

    """ [String, HPOS, VPOS, HEIGHT, WIDTH] --> [str, x, y, baseline] """

    NAMES = ["Datum", "Absender", "Empfänger", "Autograph", "Kopie", "Photokopie",
             "Standort", "Bull.", "Corr.", "Sign.", "Abschrift", "Umfang", "Sprache",
             "Literatur", "Gedruckt", "Bemerkungen"]

    def __init__(self, scaling, inverse=False):
        super(AttributePositionParser, self).__init__()
        self.data = pd.DataFrame({'Value': [], 'x': [], 'y': [], "Baseline": []})
        self.scaling = scaling
        self.inverse = inverse
        self.current_baseline = 0

    def startElement(self, name, attributes):
        if name == "TextLine":
            for a in attributes.getNames():
                if a == "BASELINE":
                    self.current_baseline = attributes.getValue(a)

        if name == "String" and "STYLE" not in attributes.getNames():
            d = dict()
            d["BASELINE"] = self.current_baseline
            for a in attributes.getNames():
                d[a] = attributes.getValue(a)
            if self.inverse:
                if d["CONTENT"] not in AttributePositionParser.NAMES:
                    self.append(d)
            else:
                if d["CONTENT"] in AttributePositionParser.NAMES:
                    self.append(d)

    def append(self, d):
        hpos, vpos = int(d["HPOS"]), int(d["VPOS"])
        width, height = int(d["WIDTH"]), int(d["HEIGHT"])
        x, y = AttributePositionParser.get_mass_point(hpos, vpos, width, height, self.scaling)
        value = ''
        if ("SUBS_TYPE" in d) and ("SUBS_CONTENT" in d):
            if d["SUBS_TYPE"] == "HypPart1":
                value = d["SUBS_CONTENT"]
        else: value = d["CONTENT"]
        df = pd.DataFrame({
            'Value': [value],
            'x': [x], 'y': [y],
            'Baseline': [self.current_baseline]
        })
        self.data = pd.concat([self.data, df])

    @staticmethod
    def get_mass_point(hpos, vpos, width, height, scaling):
        """ text center coordinates """
        x, y = hpos + 0.5 * width, vpos + 0.5 * height
        return int(scaling[0]*x), int(scaling[1]*y)

    @staticmethod
    def get_attributes(path, scaling, inverse=False):
        try:
            parser = xml.sax.make_parser()
            counter = AttributePositionParser(scaling, inverse=inverse)
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.data
        except:
            print("*** Warning: attribute-parser failed on", path)
            return pd.DataFrame({'Value': [], 'x': [], 'y': [], "Baseline": []})
