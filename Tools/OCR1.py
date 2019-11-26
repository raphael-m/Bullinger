#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# OCR1.py
# Bernard Schroffenegger
# 5th of October, 2019

""" Bullinger Parser OCR-V1"""

import pandas as pd
import xml.sax

from xml.sax.handler import ContentHandler
from Tools.FileSystem import FileSystem


class OCR1:

    SCHEMA = ['Path', 'x', 'y']

    def __init__(self):
        pass

    @staticmethod
    def get_page_sizes(directory):
        """ :param directory: <str>; Path """
        data = pd.DataFrame(columns=OCR1.SCHEMA)
        for path in FileSystem.get_file_paths(directory):
            data = pd.concat([data, PageSizeParser1.get_data(path)])
        return data


class PageSizeParser1(ContentHandler):

    """ Avg. Page Size (x_may, y_may) [px]
        E.g. <page width="9849" height="6989" resolution="1200">
    """

    def __init__(self, path):
        super(PageSizeParser1, self).__init__()
        self.data = pd.DataFrame(columns=OCR1.SCHEMA)
        self.path = path  # exceptions

    def startElement(self, element, attributes):
        """ <page> --> (height/width) """
        if element.lower() == "page":
            height, width = -1, -1
            for a in attributes.getNames():
                if a == "width":
                    width = int(attributes.getValue(a))
                if a == "height":
                    height = int(attributes.getValue(a))
            if width and height:
                d = {OCR1.SCHEMA[0]: [self.path], OCR1.SCHEMA[1]: [width], OCR1.SCHEMA[2]: [height]}
                self.data = pd.concat([self.data, pd.DataFrame(d)])
            else:
                print("*** Warning: corrupt <page> data. See", self.path)

    @staticmethod
    def get_data(path):
        try:
            parser = xml.sax.make_parser()
            counter = PageSizeParser1(path)
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.data
        except (AttributeError, TypeError):
            print("*** Warning: parser (page size BV1) failed on", path)
            return None


class TextPositionParser1(ContentHandler):

    """ gathers mass points of ocr-text elements """

    def __init__(self):
        super(TextPositionParser1, self).__init__()
        self.data = pd.DataFrame({'x': [], 'y': []})

    def startElement(self, name, attributes):
        if name == "line":
            d = dict()  # tlrb
            for a in attributes.getNames():
                d[a] = int(attributes.getValue(a))
            x, y = [int((d['r']+d['l'])/2)], [int((d['b']+d['t'])/2)]
            data = pd.DataFrame({'x': x, 'y': y})
            self.data = pd.concat([self.data, data])

    @staticmethod
    def get_coordinates(path):
        try:
            parser = xml.sax.make_parser()
            counter = TextPositionParser1()
            parser.setContentHandler(counter)
            parser.parse(path)
            return counter.data
        except (AttributeError, TypeError):
            print("Warning: TP-parser failed on", path)
