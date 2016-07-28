#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright 2016 MIT Lincoln Laboratory, Massachusetts Institute of Technology
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use these files except in compliance with
# the License.
#
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#


"""
Authors: Bill Campbell, Kelly Geyer
Date: May 11, 2016
Installation: Python 2.7 on Windows 7

Description: This script contains filter functions for word count dictionary objects, where keys are words and values
are counts.
"""


import re
from nltk.stem.isri import ISRIStemmer
from nltk.corpus import stopwords


def neutral_count_filter(counts_dict):
    """
    This filter function returns the original word count dictionary

    :param/return counts_dict: Dictionary object from text files, where keys are words and values
    """
    return counts_dict

def neutral_text_filter(txt):
    """
    This filter function returns the original text string

    :param/return txt: String object
    """
    return txt

def market_text_filter(txt):
    """
    This filter is designed for text from teh Agora nad Nucleus data sets. It removes the PGP key from text.

    :param/return txt: String
    """
    pgp_key = re.search(r'BEGIN PGP', txt)
    if pgp_key:
        i1 = pgp_key.start(0)
        txt = txt[0:i1]
    return txt

def market_count_filter(counts_dict):
    """
    This filter is designed for count dictionaries from the Agora and Nucleus data sets

    :param/return count_dict: Dictionary object from text files, where keys are words and values
    """
    if '.' in counts_dict:
        del counts_dict['.']
    if '&' in counts_dict:
        del counts_dict['&']
    if ',' in counts_dict:
        del counts_dict[',']
    for ky in counts_dict.keys():                   # no this isn't a mistake
        if re.match(r'^[0-9]+g$', ky):              # get rid of 5g, etc.
            del counts_dict[ky]
        if re.match(r'^[0-9]+$', ky):               # get rid of numbers
            del counts_dict[ky]
        if re.match(r'^#[0-9\-]+$', ky):            # get rid of counts of pills, #3
            del counts_dict[ky]
        if re.match(r'^[0-9\-]+mg$', ky):           # 5mg
            del counts_dict[ky]
        if re.match(r'^[0-9\-]+kg$', ky):           # 1kg
            del counts_dict[ky]
        if re.match(r'^[0-9]+[xX]$', ky):           # 100x
            del counts_dict[ky]
    return counts_dict

def social_media_text_filter(msg, debug=0):
    """
    This funciton filters out spurious lines, spaces, emojis, and HTML tags

    :param msg: Text to filter
    :param debug: Set to 1 to see messages
    """
    if debug > 0:
        print u"\nmsg: {}".format(msg)
    # Spurious return, newlines
    msg = msg.replace(u'\\r', u' ').replace(u'\\n', u' ')
    # Spurious HTML tags
    msg = re.sub(u'<[a-z].*?>', u' ', msg)
    msg = re.sub(u'</[a-z].*?>', u' ', msg)
    msg = re.sub(u'<[a-z].*?/>', u' ', msg)
    # Remove emojis
    emoji_pattern = re.compile(u'('
        u'\ud83c[\udf00-\udfff]|'
        u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
        u'[\u2600-\u26FF\u2700-\u27BF])+',
        re.UNICODE)
    msg = emoji_pattern.sub(r' ', msg)
    # Extra spaces
    msg = re.sub(u'\s+', u' ', msg)
    # xact['msg_norm'] = msg
    if (debug > 0):
        print u"normalized msg: {}".format(msg)
    return msg


def arabic_social_media_text_filter(txt, debug=0):
    """
    This filter is for filtering Arabic text from social media.

    :param txt: utf-8 text, unicode
    :param debug: Any value greater than 0 prints messages about normalized vs original text.
    :param return:
    """
    txt = social_media_text_filter(txt, debug=debug)
    # Remove diacritics
    st = ISRIStemmer()
    txt = st.norm(txt)
    return txt

def russian_count_filter(counts_dict):
    """
    This funciton removes stop words from a Russian word dictionary

    :param counts_dict: Dictionary where keys are unicode and values are counts
    """
    # Remove stop words
    for wd in counts_dict:
        if wd in stopwords.words('russian'):
            del counts_dict[wd]
    return counts_dict