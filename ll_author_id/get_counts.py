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

Description: This script generates word count objects
"""

import argparse
import codecs
from collections import Counter
from datetime import datetime
from filters import neutral_text_filter, neutral_count_filter
import gzip
import io
import json
import os
import re
import sys

def read_id_filename_list(fn):
    """
    This function reads in a '.txt', '.txt.gz', '.json.gz' or '.json' file with user IDs and filenames corresponding to
    a user ID. UTF-8 encoding is used to preserve user IDs

    Expected format of '.txt' files
    tgt_author <user id 1>
    <path to user id 1 file, file #1>
    tgt_author <userid 2>
    <path to user id 2 file, file #1>
    <path to user id 2 file, file #2>

    Expected format of '.json' files
    {"user id 1": ["<path to user id 1 file, file #1>"],
    "user id 2": ["<path to user id 2 file, file #1>", "<path to user id 2 file, file #2>"]}

    :param fn: Name of file, format '.txt' or '.json'
    :return id_fn_dict: Dictionary where keys are user IDs and values are list of the corresponding filenames. The
        encoding is UTF-8
    """
    # Check the extension of the id_filename_list to be sure it matches either '.txt' or '.json'
    assert (True in [str(fn).endswith(x) for x in ['.txt', '.txt.gz', '.json', '.json.gz']]), "The file {} must have one of the following extensions: '.txt', '.txt.gz', '.json', or '.json.gz'".format(count_filename)
    # Dictionary to link user IDs to files
    id_fn_dict = {}
    # Read text file
    if fn.endswith('.txt') or fn.endswith('.txt.gz'):
        f = codecs.open(fn, encoding='utf-8')
        for line in f:
            if 'tgt_author' in line:
                cur_key = line.split(' ')[1].strip()
                if cur_key not in id_fn_dict.keys():
                    id_fn_dict[cur_key] = {}
            else:
                id_fn_dict[cur_key][line.strip()] = {}
        f.close()
    # Read JSON file
    if fn.endswith('.json') or fn.endswith('.json.gz'):
        input_file = file(fn, 'r')
        raw_dict = json.loads(input_file.read().decode('utf-8-sig'))
        for kk in raw_dict.keys():
            if kk not in id_fn_dict:
                id_fn_dict[kk] = {}
            for fn in raw_dict[kk]:
                id_fn_dict[kk][fn] = {}
        input_file.close()
    return id_fn_dict

def text_to_counts(count_filename, id_filename_list, config, text_filter_func=neutral_text_filter, count_filter_func=neutral_count_filter):
    """
    This function normalizes text files (normalization is specified by the configuration settings), and then creates a
    dictionary of word counts. The count dictionary is saved in one of the following formats: '.json', '.json.gz',
    '.txt', or '.txt.gz'

    1. Reads in text from all user IDs
    2. normalizes text
    3. get word counts
    4. save in out file

    :param count_filename: File name of word count dictionary object
    :param id_filename_list: File of user IDs and related files, in either a '.txt', '.txt.gz', '.json', or '.json.gz'

        Expected format of '.txt' and '.txt.gz' files
        tgt_author <user id 1>
        <path to user id 1 file, file #1>
        tgt_author <userid 2>
        <path to user id 2 file, file #1>
        <path to user id 2 file, file #2>

        Expected format of '.json' and '.json.gz' files
        {"user id 1": ["<path to user id 1 file, file #1>"],
        "user id 2": ["<path to user id 2 file, file #1>", "<path to user id 2 file, file #2>"]}

    :params config: Config dictionary
    :params text_filter_func: Function for filtering content from text, default is no filtering
    :params count_filter_func: Function for word count dictionary filter, default is no filtering
    """
    # Make sure it just matches one of the extensions
    assert (True in [str(count_filename).endswith(x) for x in ['.txt', '.txt.gz', '.json', '.json.gz']]), "The file {} must have one of the following extensions: '.txt', '.txt.gz', '.json', or '.json.gz'".format(count_filename)
    assert (True in [str(id_filename_list).endswith(x) for x in ['.txt', '.txt.gz', '.json', '.json.gz']]), "The file {} must have one of the following extensions: '.txt', '.txt.gz', '.json', or '.json.gz'".format(id_filename_list)

    # Get list of userIDs and corresponding file names
    id_fn_dict = read_id_filename_list(id_filename_list)

    # Get word counts for each author
    for id in id_fn_dict:
        for fn in id_fn_dict[id]:
            counts = _get_text_counts(filename=fn, config=config, text_filter_func=text_filter_func, count_filter_func=count_filter_func)
            if counts is not None:
                id_fn_dict[id][fn] = counts

    # Combine word count dictionaries from all files if specified by config
    if config['counts']['combine_same_user_counts']:
        print "Combine word count dictionaries from all files if specified by config"
        for id in id_fn_dict:
            all = Counter(dict({}))
            for fn in id_fn_dict[id].keys():
                all += Counter(id_fn_dict[id][fn])
                id_fn_dict[id].pop(fn)
            id_fn_dict[id]['all_files'] = dict(all)

    # New file that will contain all user counts, and save them
    if config['counts']['format'].endswith('.gz'):
        open_cmd = gzip.open
    else:
        open_cmd = open
    if '.json' in config['counts']['format']:
        with open_cmd(count_filename, 'w') as output_file_raw:
            output_file = codecs.getwriter('utf-8')(output_file_raw)
            json.dump(id_fn_dict, output_file, sort_keys=True, ensure_ascii=False)
    elif '.txt' in config['counts']['format']:
        with open_cmd(count_filename, 'w') as output_file_raw:
            output_file = codecs.getwriter('utf-8')(output_file_raw)
            for id in id_fn_dict:
                for fn in id_fn_dict[id]:
                    sys.stdout.flush()
                    output_file.write(u"{}\t{}".format(id, fn))
                    for w in id_fn_dict[id][fn]:
                        output_file.write("\t{}{}{}".format(w, config['counts']['count_separator'], id_fn_dict[id][fn][w]))
                    output_file.write(u"\n")
    else:
        print "The file format {} is not recognized. Please use '.json', '.txt', '.json.gz', or '.txt.gz'".format(config['counts']['format'])

def _get_text_counts(filename, config, text_filter_func=neutral_text_filter, count_filter_func=neutral_count_filter):
    """
    This function pulls text files from a directory (desc_dir), normalizes the text by specifications of the
    configurations settings, and then creates a word count dictionary.

    :param filename: The text file name, includes path
    :param config: The settings configuration dictionary object. Specifies how to normalize the text
    :param text_filter_func: Filter that filters content in text, default is no processing
    :param filter_func: Function that filters words in word count dictionary, default is no processing
    """
    # Open and read file, if it exists
    if not os.path.exists(filename):
        print u'File does not exist, skipping: {}'.format(filename)
        return None
    with codecs.open(filename, 'r', encoding='utf-8') as fid:
        product_text = fid.read()
    # Filter content in text file
    product_text = text_filter_func(product_text)
    # Normalize text and lower case
    pt_norm = normalize(product_text, config).lower()
    # Get counts dictionary, where keys are words and values are counts
    pt_norm_arr = [pt_norm]
    counts = get_counts(pt_norm_arr)
    # Filter text in counts dictionary
    counts = count_filter_func(counts)
    return counts

def get_counts(msg):
    """
    This function creates a count dictionary by separating words by single spaces.

    :param msg: String object
    :return counts: Dictionary object, where words are keys and values are counts
    """
    counts = {}
    for sent in msg:
        f = sent.split(' ')
        for w in f:
            if (not counts.has_key(w)):
                counts[w] = 0.0
            counts[w] += 1
    return counts

def remove_repeats(msg):
    """
    This function removes repeated characters from text.

    :param/return msg: String
    """
    # twitter specific repeats
    msg = re.sub(r"(.)\1{2,}", r"\1\1\1", msg)  # characters repeated 3 or more times
    # laughs
    msg = re.sub(r"(ja|Ja)(ja|Ja)+(j)?", r"jaja", msg) # spanish
    msg = re.sub(r"(rs|Rs)(Rs|rs)+(r)?", r"rsrs", msg) # portugese
    msg = re.sub(r"(ha|Ha)(Ha|ha)+(h)?", r"haha", msg) # english
    return msg

def split(ln):
    """
    This function ...

    :param ln: String
    :return fout:
    """
    # horridly simple splitter
    ln = ln.replace(". ", ".\n\n").replace("? ","?\n\n").replace("! ","!\n\n")
    ln = ln.replace('."', '."\n\n')
    f = ln.split("\n")
    fout = []
    for s in f:
        s = s.rstrip()
        s = re.sub(r'^\s+', '', s)
        if (s!=""):
            fout.append(s)
    return fout

def normalize(ln, config):
    """
    This function normalizes text, normalization options include
    1. convert UTF8 to ASCII
    2. Remove Twitter metadata
    3. Remove nonsentenial punctuation
    4. Remove mark up
    5. Remove repeated letters in words

    :param ln: Text before normalization process
    :param config_func: Configuration function
    :return ln: Normalized text

    Q: What is remove_markup?
    Q: Is what I did okay over using example wow.py?
    Q: Is it okay to move create_utf8_rewrite_hash() to the inside of this function?
    """
    # Load dictionary for ASCII conversion
    rw_hash = create_utf8_rewrite_hash()
    # Various normalization routines -- pick and choose as needed
    if config['text_norm']['utf8_to_ascii']:
        ln = convertUTF8_to_ascii(ln, rw_hash)
    if config['text_norm']['remove_twitter']:
        ln = remove_twitter_meta(ln)
    if config['text_norm']['remove_nonsentenial']:
        ln = remove_nonsentential_punctuation(ln)
    if config['text_norm']['remove_markup']:
        ln = remove_markup(ln)
    ln = remove_word_punctuation(ln)  # this is done separately in the original code
    ln = remove_repeats(ln)
    ln = re.sub('\s+', ' ', ln)
    if (ln == ' '):
        ln = ''
    return ln

def convertUTF8_to_ascii(ln, rewrite_hash):
    """
    This function ...

    :param ln:
    :param rewrite_hash:
    :return out:
    """
    out = ''
    for i in xrange(0,len(ln)):
        if (ord(ln[i]) < 0x7f):
            out = out + ln[i]
        elif (rewrite_hash.has_key(ln[i])):
            out = out + rewrite_hash[ln[i]]
        else:
            out = out + " "
    # Clean up extra spaces
    out = re.sub('^\s+', '', out)
    out = re.sub('\s+$', '', out)
    out = re.sub('\s+', ' ', out)
    out = re.sub('\s+.$', '.', out)
    return out

def create_utf8_rewrite_hash():
    """
    This function rewrites UTF-8 characters to ASCII in a rational manner. Strictly speaking (and in python) any ascii
    character >= 128 is not valid

    :return rewrite_hash: Dictionary object where keys are UTF-8 characters and values are corresponding ASCII values
    """
    rewrite_hash = dict([])
    rewrite_hash[u'\xA0'] = " "            # NO-BREAK SPACE 
    rewrite_hash[u'\xA1'] = " "            # INVERTED EXCLAMATION MARK
    rewrite_hash[u'\xA2'] = " cents "      # CENT SIGNS
    rewrite_hash[u'\xA3'] = " pounds "     # POUND SIGN
    rewrite_hash[u'\xA4'] = " "            # CURRENCY SIGN
    rewrite_hash[u'\xA5'] = " yen "        # YEN SIGN
    rewrite_hash[u'\xA6'] = " "            # BROKEN BAR
    rewrite_hash[u'\xA7'] = " "            # SECTION SIGN
    rewrite_hash[u'\xA8'] = " "            # DIAERESIS
    rewrite_hash[u'\xA9'] = " "            # COPYRIGHT SIGN
    rewrite_hash[u'\xAA'] = " "            # FEMININE ORDINAL INDICATOR
    rewrite_hash[u'\xAB'] = " "            # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    rewrite_hash[u'\xAC'] = " "            # NOT SIGN
    rewrite_hash[u'\xAD'] = " "            # SOFT HYPHEN
    rewrite_hash[u'\xAE'] = " "            # REGISTERED SIGN
    rewrite_hash[u'\xAF'] = " "            # MACRON
    rewrite_hash[u'\xB0'] = " degrees "	      # DEGREE SIGN
    rewrite_hash[u'\xB1'] = " plus-or-minus " # PLUS-MINUS SIGN
    rewrite_hash[u'\xB2'] = " "	        # SUPERSCRIPT TWO
    rewrite_hash[u'\xB3'] = " ";	# SUPERSCRIPT THREE
    rewrite_hash[u'\xB4'] = "'"		# ACUTE ACCENT
    rewrite_hash[u'\xB5'] = " micro "   # MICRO SIGN
    rewrite_hash[u'\xB6'] = " "		# PILCROW SIGN
    rewrite_hash[u'\xB7'] = " "		# MIDDLE DOT
    rewrite_hash[u'\xB8'] = " "		# CEDILLA
    rewrite_hash[u'\xB9'] = " "		# SUPERSCRIPT ONE
    rewrite_hash[u'\xBA'] = " "		# MASCULINE ORDINAL INDICATOR
    rewrite_hash[u'\xBB'] = " "		# RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
    rewrite_hash[u'\xBC'] = " 1/4 "	# VULGAR FRACTION ONE QUARTER
    rewrite_hash[u'\xBD'] = " 1/2 "	# VULGAR FRACTION ONE HALF
    rewrite_hash[u'\xBE'] = " 3/4 "     # VULGAR FRACTION THREE QUARTERS
    rewrite_hash[u'\xBF'] = " "		# INVERTED QUESTION MARK

    rewrite_hash[u'\xC0'] = "A"  # LATIN CAPITAL LETTER A WITH GRAVE
    rewrite_hash[u'\xC1'] = "A"  # LATIN CAPITAL LETTER A WITH ACUTE
    rewrite_hash[u'\xC2'] = "A"  # LATIN CAPITAL LETTER A WITH CIRCUMFLEX
    rewrite_hash[u'\xC3'] = "A"  # LATIN CAPITAL LETTER A WITH TILDE
    rewrite_hash[u'\xC4'] = "A"  # LATIN CAPITAL LETTER A WITH DIAERESIS
    rewrite_hash[u'\xC5'] = "A"  # LATIN CAPITAL LETTER A WITH RING ABOVE
    rewrite_hash[u'\xC6'] = "AE" # LATIN CAPITAL LETTER AE
    rewrite_hash[u'\xC7'] = "C"  # LATIN CAPITAL LETTER C WITH CEDILLA
    rewrite_hash[u'\xC8'] = "E"  # LATIN CAPITAL LETTER E WITH GRAVE
    rewrite_hash[u'\xC9'] = "E"  # LATIN CAPITAL LETTER E WITH ACUTE
    rewrite_hash[u'\xCA'] = "E"  # LATIN CAPITAL LETTER E WITH CIRCUMFLEX
    rewrite_hash[u'\xCB'] = "E"  # LATIN CAPITAL LETTER E WITH DIAERESIS
    rewrite_hash[u'\xCC'] = "I"  # LATIN CAPITAL LETTER I WITH GRAVE
    rewrite_hash[u'\xCD'] = "I"  # LATIN CAPITAL LETTER I WITH ACUTE
    rewrite_hash[u'\xCE'] = "I"  # LATIN CAPITAL LETTER I WITH CIRCUMFLEX
    rewrite_hash[u'\xCF'] = "I"  # LATIN CAPITAL LETTER I WITH DIAERESIS

    rewrite_hash[u'\xD0'] = "Th" # LATIN CAPITAL LETTER ETH
    rewrite_hash[u'\xD1'] = "N"  # LATIN CAPITAL LETTER N WITH TILDE
    rewrite_hash[u'\xD2'] = "O"  # LATIN CAPITAL LETTER O WITH GRAVE
    rewrite_hash[u'\xD3'] = "O"  # LATIN CAPITAL LETTER O WITH ACUTE
    rewrite_hash[u'\xD4'] = "O"  # LATIN CAPITAL LETTER O WITH CIRCUMFLEX
    rewrite_hash[u'\xD5'] = "O"  # LATIN CAPITAL LETTER O WITH TILDE
    rewrite_hash[u'\xD6'] = "O"  # LATIN CAPITAL LETTER O WITH DIAERESIS
    rewrite_hash[u'\xD7'] = "x"  # MULTIPLICATION SIGN
    rewrite_hash[u'\xD8'] = "O"  # LATIN CAPITAL LETTER O WITH STROKE
    rewrite_hash[u'\xD9'] = "U"  # LATIN CAPITAL LETTER U WITH GRAVE
    rewrite_hash[u'\xDA'] = "U"  # LATIN CAPITAL LETTER U WITH ACUTE
    rewrite_hash[u'\xDB'] = "U"  # LATIN CAPITAL LETTER U WITH CIRCUMFLEX
    rewrite_hash[u'\xDC'] = "U"  # LATIN CAPITAL LETTER U WITH DIAERESIS    
    rewrite_hash[u'\xDD'] = "Y"  # LATIN CAPITAL LETTER Y WITH ACUTE
    rewrite_hash[u'\xDE'] = "Th" # LATIN CAPITAL LETTER THORN
    rewrite_hash[u'\xDF'] = "ss" # LATIN SMALL LETTER SHARP S
    
    rewrite_hash[u'\xE0'] = "a"  # LATIN SMALL LETTER A WITH GRAVE
    rewrite_hash[u'\xE1'] = "a"  # LATIN SMALL LETTER A WITH ACUTE
    rewrite_hash[u'\xE2'] = "a"  # LATIN SMALL LETTER A WITH CIRCUMFLEX
    rewrite_hash[u'\xE3'] = "a"  # LATIN SMALL LETTER A WITH TILDE
    rewrite_hash[u'\xE4'] = "a"  # LATIN SMALL LETTER A WITH DIAERESIS
    rewrite_hash[u'\xE5'] = "a"  # LATIN SMALL LETTER A WITH RING ABOVE
    rewrite_hash[u'\xE6'] = "ae" # LATIN SMALL LETTER AE
    rewrite_hash[u'\xE7'] = "c"  # LATIN SMALL LETTER C WITH CEDILLA
    rewrite_hash[u'\xE8'] = "e"  # LATIN SMALL LETTER E WITH GRAVE
    rewrite_hash[u'\xE9'] = "e"  # LATIN SMALL LETTER E WITH ACUTE
    rewrite_hash[u'\xEA'] = "e"  # LATIN SMALL LETTER E WITH CIRCUMFLEX
    rewrite_hash[u'\xEB'] = "e"  # LATIN SMALL LETTER E WITH DIAERESIS
    rewrite_hash[u'\xEC'] = "i"  # LATIN SMALL LETTER I WITH GRAVE
    rewrite_hash[u'\xED'] = "i"  # LATIN SMALL LETTER I WITH ACUTE
    rewrite_hash[u'\xEE'] = "i"  # LATIN SMALL LETTER I WITH CIRCUMFLEX
    rewrite_hash[u'\xEF'] = "i"  # LATIN SMALL LETTER I WITH DIAERESIS
    
    rewrite_hash[u'\xF0'] = "th" # LATIN SMALL LETTER ETH
    rewrite_hash[u'\xF1'] = "n"  # LATIN SMALL LETTER N WITH TILDE
    rewrite_hash[u'\xF2'] = "o"  # LATIN SMALL LETTER O WITH GRAVE
    rewrite_hash[u'\xF3'] = "o"  # LATIN SMALL LETTER O WITH ACUTE
    rewrite_hash[u'\xF4'] = "o"  # LATIN SMALL LETTER O WITH CIRCUMFLEX
    rewrite_hash[u'\xF5'] = "o"  # LATIN SMALL LETTER O WITH TILDE
    rewrite_hash[u'\xF6'] = "o"  # LATIN SMALL LETTER O WITH DIAERESIS
    rewrite_hash[u'\xF7'] = " divided by "  # DIVISION SIGN
    rewrite_hash[u'\xF8'] = "o"  # LATIN SMALL LETTER O WITH STROKE
    rewrite_hash[u'\xF9'] = "u"  # LATIN SMALL LETTER U WITH GRAVE
    rewrite_hash[u'\xFA'] = "u"  # LATIN SMALL LETTER U WITH ACUTE
    rewrite_hash[u'\xFB'] = "u"  # LATIN SMALL LETTER U WITH CIRCUMFLEX
    rewrite_hash[u'\xFC'] = "u"  # LATIN SMALL LETTER U WITH DIAERESIS
    rewrite_hash[u'\xFD'] = "y"  # LATIN SMALL LETTER Y WITH ACUTE
    rewrite_hash[u'\xFE'] = "th" # LATIN SMALL LETTER THORN
    rewrite_hash[u'\xFF'] = "y"  # LATIN SMALL LETTER Y WITH DIAERESIS
    
    rewrite_hash[u'\u0100'] = "A"  # LATIN CAPTIAL LETTER A WITH MACRON
    rewrite_hash[u'\u0101'] = "a"  # LATIN SMALL LETTER A WITH MACRON
    rewrite_hash[u'\u0102'] = "A"  # LATIN CAPITAL LETTER A WITH BREVE
    rewrite_hash[u'\u0103'] = "a"  # LATIN SMALL LETTER A WITH BREVE
    rewrite_hash[u'\u0104'] = "A"  # LATIN CAPITAL LETTER A WITH OGONEK
    rewrite_hash[u'\u0105'] = "a"  # LATIN SMALL LETTER A WITH OGONEK
    rewrite_hash[u'\u0106'] = "C"  # LATIN CAPITAL LETTER C WITH ACUTE
    rewrite_hash[u'\u0107'] = "c"  # LATIN SMALL LETTER C WITH ACUTE
    rewrite_hash[u'\u0108'] = "C"  # LATIN CAPITAL LETTER C WITH CIRCUMFLEX
    rewrite_hash[u'\u0109'] = "c"  # LATIN SMALL LETTER C WITH CIRCUMFLEX 
    rewrite_hash[u'\u010A'] = "C"  # LATIN CAPITAL LETTER C WITH DOT ABOVE
    rewrite_hash[u'\u010B'] = "c"  # LATIN SMALL LETTER C WITH DOT ABOVE
    rewrite_hash[u'\u010C'] = "C"  # LATIN CAPITAL LETTER C WITH CARON
    rewrite_hash[u'\u010D'] = "c"  # LATIN SMALL LETTER C WITH CARON
    rewrite_hash[u'\u010E'] = "D"  # LATIN CAPITAL LETTER D WITH CARON
    rewrite_hash[u'\u010F'] = "d"  # LATIN SMALL LETTER D WITH CARON

    rewrite_hash[u'\u0110'] = "D"  # LATIN CAPITAL LETTER D WITH STROKE
    rewrite_hash[u'\u0111'] = "d"  # LATIN SMALL LETTER D WITH STROKE
    rewrite_hash[u'\u0112'] = "E"  # LATIN CAPITAL LETTER E WITH MACRON
    rewrite_hash[u'\u0113'] = "e"  # LATIN SMALL LETTER E WITH MACRON
    rewrite_hash[u'\u0114'] = "E"  # LATIN CAPITAL LETTER E WITH BREVE
    rewrite_hash[u'\u0115'] = "e"  # LATIN SMALL LETTER E WITH BREVE
    rewrite_hash[u'\u0116'] = "E"  # LATIN CAPITAL LETTER E WITH DOT ABOVE
    rewrite_hash[u'\u0117'] = "e"  # LATIN SMALL LETTER E WITH DOT ABOVE
    rewrite_hash[u'\u0118'] = "E"  # LATIN CAPITAL LETTER E WITH OGONEK
    rewrite_hash[u'\u0119'] = "e"  # LATIN SMALL LETTER E WITH OGONEK
    rewrite_hash[u'\u011A'] = "E"  # LATIN CAPITAL LETTER E WITH CARON
    rewrite_hash[u'\u011B'] = "e"  # LATIN SMALL LETTER E WITH CARON
    rewrite_hash[u'\u011C'] = "G"  # LATIN CAPITAL LETTER G WITH CIRCUMFLEX
    rewrite_hash[u'\u011D'] = "g"  # LATIN SMALL LETTER G WITH CIRCUMFLEX
    rewrite_hash[u'\u011E'] = "G"  # LATIN CAPITAL LETTER G WITH BREVE 
    rewrite_hash[u'\u011F'] = "g"  # LATIN SMALL LETTER G WITH BREVE

    rewrite_hash[u'\u0120'] = "G"  # LATIN CAPITAL LETTER G WITH DOT ABOVE
    rewrite_hash[u'\u0121'] = "g"  # LATIN SMALL LETTER G WITH DOT ABOVE
    rewrite_hash[u'\u0122'] = "G"  # LATIN CAPITAL LETTER G WITH CEDILLA
    rewrite_hash[u'\u0123'] = "g"  # LATIN SMALL LETTER G WITH CEDILLA
    rewrite_hash[u'\u0124'] = "H"  # LATIN CAPITAL LETTER H WITH CIRCUMFLEX
    rewrite_hash[u'\u0125'] = "h"  # LATIN SMALL LETTER H WITH CIRCUMFLEX
    rewrite_hash[u'\u0126'] = "H"  # LATIN CAPITAL LETTER H WITH STROKE
    rewrite_hash[u'\u0127'] = "h"  # LATIN SMALL LETTER H WITH STROKE
    rewrite_hash[u'\u0128'] = "I"  # LATIN CAPITAL LETTER I WITH TILDE
    rewrite_hash[u'\u0129'] = "i"  # LATIN SMALL LETTER I WITH TILDE
    rewrite_hash[u'\u012A'] = "I"  # LATIN CAPITAL LETTER I WITH MACRON
    rewrite_hash[u'\u012B'] = "i"  # LATIN SMALL LETTER I WITH MACRON
    rewrite_hash[u'\u012C'] = "I"  # LATIN CAPITAL LETTER I WITH BREVE
    rewrite_hash[u'\u012D'] = "i"  # LATIN SMALL LETTER I WITH BREVE
    rewrite_hash[u'\u012E'] = "I"  # LATIN CAPITAL LETTER I WITH OGONEK
    rewrite_hash[u'\u012F'] = "i"  # LATIN SMALL LETTER I WITH OGONEK

    rewrite_hash[u'\u0130'] = "I"  # LATIN CAPITAL LETTER I WITH DOT ABOVE
    rewrite_hash[u'\u0131'] = "i"  # LATIN SMALL LETTER DOTLESS I
    rewrite_hash[u'\u0132'] = "IJ" # LATIN CAPITAL LIGATURE IJ
    rewrite_hash[u'\u0133'] = "ij" # LATIN SMALL LIGATURE IJ
    rewrite_hash[u'\u0134'] = "J"  # LATIN CAPITAL LETTER J WITH CIRCUMFLEX
    rewrite_hash[u'\u0135'] = "j"  # LATIN SMALL LETTER J WITH CIRCUMFLEX
    rewrite_hash[u'\u0136'] = "K"  # LATIN CAPITAL LETTER K WITH CEDILLA
    rewrite_hash[u'\u0137'] = "k"  # LATIN SMALL LETTER K WITH CEDILLA
    rewrite_hash[u'\u0138'] = "k"  # LATIN SMALL LETTER KRA
    rewrite_hash[u'\u0139'] = "L"  # LATIN CAPITAL LETTER L WITH ACUTE
    rewrite_hash[u'\u013A'] = "l"  # LATIN SMALL LETTER L WITH ACUTE
    rewrite_hash[u'\u013B'] = "L"  # LATIN CAPITAL LETTER L WITH CEDILLA
    rewrite_hash[u'\u013C'] = "l"  # LATIN SMALL LETTER L WITH CEDILLA
    rewrite_hash[u'\u013D'] = "L"  # LATIN CAPITAL LETTER L WITH CARON
    rewrite_hash[u'\u013E'] = "l"  # LATIN SMALL LETTER L WITH CARON
    rewrite_hash[u'\u013F'] = "L"  # LATIN CAPITAL LETTER L WITH MIDDLE DOT

    rewrite_hash[u'\u0140'] = "l"  # LATIN SMALL LETTER L WITH MIDDLE DOT
    rewrite_hash[u'\u0141'] = "L"  # LATIN CAPITAL LETTER L WITH STROKE
    rewrite_hash[u'\u0142'] = "l"  # LATIN SMALL LETTER L WITH STROKE
    rewrite_hash[u'\u0143'] = "N"  # LATIN CAPITAL LETTER N WITH ACUTE
    rewrite_hash[u'\u0144'] = "n"  # LATIN SMALL LETTER N WITH ACUTE
    rewrite_hash[u'\u0145'] = "N"  # LATIN CAPITAL LETTER N WITH CEDILLA
    rewrite_hash[u'\u0146'] = "n"  # LATIN SMALL LETTER N WITH CEDILLA
    rewrite_hash[u'\u0147'] = "N"  # LATIN CAPITAL LETTER N WITH CARON
    rewrite_hash[u'\u0148'] = "n"  # LATIN SMALL LETTER N WITH CARON
    rewrite_hash[u'\u0149'] = "n"  # LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
    rewrite_hash[u'\u014A'] = "N"  # LATIN CAPITAL LETTER ENG
    rewrite_hash[u'\u014B'] = "n"  # LATIN SMALL LETTER ENG
    rewrite_hash[u'\u014C'] = "O"  # LATIN CAPITAL LETTER O WITH MACRON
    rewrite_hash[u'\u014D'] = "o"  # LATIN SMALL LETTER O WITH MACRON
    rewrite_hash[u'\u014E'] = "O"  # LATIN CAPITAL LETTER O WITH BREVE
    rewrite_hash[u'\u014F'] = "o"  # LATIN SMALL LETTER O WITH BREVE

    rewrite_hash[u'\u0150'] = "O"  # LATIN CAPITAL LETTER O WITH DOUBLE ACUTE
    rewrite_hash[u'\u0151'] = "o"  # LATIN SMALL LETTER O WITH DOUBLE ACUTE
    rewrite_hash[u'\u0152'] = "oe" # LATIN CAPITAL LIGATURE OE
    rewrite_hash[u'\u0153'] = "oe" # LATIN SMALL LIGATURE OE
    rewrite_hash[u'\u0153'] = "R"  # LATIN CAPITAL LETTER R WITH ACUTE
    rewrite_hash[u'\u0154'] = "R"  # LATIN CAPITAL LETTER R WITH ACUTE
    rewrite_hash[u'\u0155'] = "r"  # LATIN SMALL LETTER R WITH ACUTE
    rewrite_hash[u'\u0156'] = "R"  # LATIN CAPITAL LETTER R WITH CEDILLA
    rewrite_hash[u'\u0157'] = "r"  # LATIN SMALL LETTER R WITH CEDILLA
    rewrite_hash[u'\u0158'] = "R"  # LATIN CAPITAL LETTER R WITH CARON
    rewrite_hash[u'\u0159'] = "r"  # LATIN SMALL LETTER R WITH CARON
    rewrite_hash[u'\u015A'] = "S"  # LATIN CAPITAL LETTER S WITH ACUTE
    rewrite_hash[u'\u015B'] = "s"  # LATIN SMALL LETTER S WITH ACUTE
    rewrite_hash[u'\u015C'] = "S"  # LATIN CAPITAL LETTER S WITH CIRCUMFLEX
    rewrite_hash[u'\u015D'] = "s"  # LATIN SMALL LETTER S WITH CIRCUMFLEX
    rewrite_hash[u'\u015E'] = "S"  # LATIN CAPITAL LETTER S WITH CEDILLA
    rewrite_hash[u'\u015F'] = "s"  # LATIN SMALL LETTER S WITH CEDILLA

    rewrite_hash[u'\u0160'] = "S"  # LATIN CAPITAL LETTER S WITH CARON
    rewrite_hash[u'\u0161'] = "s"  # LATIN SMALL LETTER S WITH CARON
    rewrite_hash[u'\u0162'] = "T"  # LATIN CAPITAL LETTER T WITH CEDILLA 
    rewrite_hash[u'\u0163'] = "t"  # LATIN SMALL LETTER T WITH CEDILLA
    rewrite_hash[u'\u0164'] = "T"  # LATIN CAPITAL LETTER T WITH CARON
    rewrite_hash[u'\u0165'] = "t"  # LATIN SMALL LETTER T WITH CARON
    rewrite_hash[u'\u0166'] = "T"  # LATIN CAPITAL LETTER T WITH STROKE
    rewrite_hash[u'\u0167'] = "t"  # LATIN SMALL LETTER T WITH STROKE
    rewrite_hash[u'\u0168'] = "U"  # LATIN CAPITAL LETTER U WITH TILDE
    rewrite_hash[u'\u0169'] = "u"  # LATIN SMALL LETTER U WITH TILDE
    rewrite_hash[u'\u016A'] = "U"  # LATIN CAPITAL LETTER U WITH MACRON
    rewrite_hash[u'\u016B'] = "u"  # LATIN SMALL LETTER U WITH MACRON
    rewrite_hash[u'\u016C'] = "U"  # LATIN CAPITAL LETTER U WITH BREVE
    rewrite_hash[u'\u016D'] = "u"  # LATIN SMALL LETTER U WITH BREVE
    rewrite_hash[u'\u016E'] = "U"  # LATIN CAPITAL LETTER U WITH RING ABOVE
    rewrite_hash[u'\u016F'] = "u"  # LATIN SMALL LETTER U WITH RING ABOVE

    rewrite_hash[u'\u0170'] = "U"  # LATIN CAPITAL LETTER U WITH DOUBLE ACUTE
    rewrite_hash[u'\u0171'] = "u"  # LATIN SMALL LETTER U WITH DOUBLE ACUTE
    rewrite_hash[u'\u0172'] = "U"  # LATIN CAPITAL LETTER U WITH OGONEK
    rewrite_hash[u'\u0173'] = "u"  # LATIN SMALL LETTER U WITH OGONEK
    rewrite_hash[u'\u0174'] = "W"  # LATIN CAPITAL LETTER W WITH CIRCUMFLEX
    rewrite_hash[u'\u0175'] = "w"  # LATIN SMALL LETTER W WITH CIRCUMFLEX
    rewrite_hash[u'\u0176'] = "Y"  # LATIN CAPITAL LETTER Y WITH CIRCUMFLEX
    rewrite_hash[u'\u0177'] = "y"  # LATIN SMALL LETTER Y WITH CIRCUMFLEX
    rewrite_hash[u'\u0178'] = "Y"  # LATIN CAPITAL LETTER Y WITH DIAERESIS
    rewrite_hash[u'\u0179'] = "Z"  # LATIN CAPITAL LETTER Z WITH ACUTE
    rewrite_hash[u'\u017A'] = "z"  # LATIN SMALL LETTER Z WITH ACUTE
    rewrite_hash[u'\u017B'] = "Z"  # LATIN CAPITAL LETTER Z WITH DOT ABOVE
    rewrite_hash[u'\u017C'] = "z"  # LATIN SMALL LETTER Z WITH DOT ABOVE
    rewrite_hash[u'\u017D'] = "Z"  # LATIN CAPITAL LETTER Z WITH CARON
    rewrite_hash[u'\u017E'] = "z"  # LATIN SMALL LETTER Z WITH CARON
    rewrite_hash[u'\u017F'] = "s"  # LATIN SMALL LETTER LONG S

    rewrite_hash[u'\u0180'] = "b"  # LATIN SMALL LETTER B WITH STROKE
    rewrite_hash[u'\u0181'] = "B"  # LATIN CAPITAL LETTER B WITH HOOK
    rewrite_hash[u'\u0182'] = "B"  # LATIN CAPITAL LETTER B WITH TOPBAR
    rewrite_hash[u'\u0183'] = "b"  # LATIN SMALL LETTER B WITH TOPBAR
    rewrite_hash[u'\u0184'] = "b"  # LATIN CAPITAL LETTER TONE SIX
    rewrite_hash[u'\u0185'] = "b"  # LATIN SMALL LETTER TONE SIX  
    rewrite_hash[u'\u0186'] = "O"  # LATIN CAPITAL LETTER OPEN O
    rewrite_hash[u'\u0187'] = "C"  # LATIN CAPITAL LETTER C WITH HOOK
    rewrite_hash[u'\u0188'] = "c"  # LATIN SMALL LETTER C WITH HOOK
    rewrite_hash[u'\u0189'] = "D"  # LATIN CAPITAL LETTER AFRICAN D
    rewrite_hash[u'\u018A'] = "D"  # LATIN CAPITAL LETTER D WITH HOOK
    rewrite_hash[u'\u018B'] = "d"  # LATIN CAPITAL LETTER D WITH TOPBAR
    rewrite_hash[u'\u018C'] = "d"  # LATIN SMALL LETTER D WITH TOPBAR
    rewrite_hash[u'\u018D'] = " "  # LATIN SMALL LETTER TURNED DELTA
    rewrite_hash[u'\u018E'] = " "  # LATIN CAPITAL LETTER REVERSED E
    rewrite_hash[u'\u018F'] = " "  # LATIN CAPITAL LETTER SCHWA

    rewrite_hash[u'\u0190'] = "E"  # LATIN CAPITAL LETTER OPEN E
    rewrite_hash[u'\u0191'] = "F"  # LATIN CAPITAL LETTER F WITH HOOK
    rewrite_hash[u'\u0192'] = "f"  # LATIN SMALL LETTER F WITH HOOK
    rewrite_hash[u'\u0193'] = "G"  # LATIN CAPITAL LETTER G WITH HOOK
    rewrite_hash[u'\u0194'] = " "  # LATIN CAPITAL LETTER GAMMA
    rewrite_hash[u'\u0195'] = "hv" # LATIN SMALL LETTER HV
    rewrite_hash[u'\u0196'] = "I"  # LATIN CAPITAL LETTER IOTA
    rewrite_hash[u'\u0197'] = "I"  # LATIN CAPITAL LETTER I WITH STROKE
    rewrite_hash[u'\u0198'] = "K"  # LATIN CAPITAL LETTER K WITH HOOK
    rewrite_hash[u'\u0199'] = "k"  # LATIN SMALL LETTER K WITH HOOK
    rewrite_hash[u'\u019A'] = "l"  # LATIN SMALL LETTER L WITH BAR
    rewrite_hash[u'\u019B'] = " "  # LATIN SMALL LETTER LAMBDA WITH STROKE
    rewrite_hash[u'\u019C'] = " "  # LATIN CAPITAL LETTER TURNED M
    rewrite_hash[u'\u019D'] = "N"  # LATIN CAPITAL LETTER N WITH LEFT HOOK
    rewrite_hash[u'\u019E'] = "n"  # LATIN SMALL LETTER N WITH LONG RIGHT LEG
    rewrite_hash[u'\u019F'] = "O"  # LATIN CAPITAL LETTER O WITH MIDDLE TILDE

    rewrite_hash[u'\u0226'] = "a"  # LATIN CAPITAL LETTER A WITH DOT ABOVE
    rewrite_hash[u'\u0227'] = "a"  # LATIN SMALL LETTER A WITH DOT ABOVE
    rewrite_hash[u'\u02DC'] = " "  # SMALL TILDE 

    rewrite_hash[u'\u0336'] = " "  # COMBINING LONG STROKE OVERLAY
    rewrite_hash[u'\u0391'] = "A" # GREEK CAPITAL LETTER ALPHA
    rewrite_hash[u'\u03A4'] = "T" # GREEK CAPITAL LETTER TAU
    rewrite_hash[u'\u03A9'] = " omega " # GREEK CAPITAL LETTER OMEGA
    rewrite_hash[u'\u03B2'] = " beta " # GREEK SMALL LETTER BETA
    rewrite_hash[u'\u03BC'] = " mu " # GREEK SMALL LETTER MU
    rewrite_hash[u'\u03C0'] = " pi " # GREEK SMALL LETTER PI

    rewrite_hash[u'\u0441'] = "c" # CYRILLIC SMALL LETTER ES

    rewrite_hash[u'\u1F7B'] = "u" # GREEK SMALL LETTER UPSILON WITH OXIA    
    rewrite_hash[u'\u1E25'] = "h" # LATIN SMALL LETTER H WITH DOT BELOW
    rewrite_hash[u'\u1ECB'] = "i" # LATIN SMALL LETTER I WITH DOT BELOW

    rewrite_hash[u'\u2000'] = " " # EN QUAD
    rewrite_hash[u'\u2001'] = " " # EM QUAD
    rewrite_hash[u'\u2009'] = " " # THIN SPACE
    rewrite_hash[u'\u200A'] = " " # HAIR SPACE
    rewrite_hash[u'\u200B'] = " " # ZERO WIDTH SPACE

    rewrite_hash[u'\u200E'] = " " # LEFT-TO-RIGHT MARK
    rewrite_hash[u'\u200F'] = " " # RIGHT-TO-LEFT MARK

    rewrite_hash[u'\u2010'] = "-" # HYPHEN
    rewrite_hash[u'\u2011'] = "-" # NON-BREAKING HYPHEN
    rewrite_hash[u'\u2013'] = " " # EN DASH
    rewrite_hash[u'\u2014'] = " " # EM DASH
    rewrite_hash[u'\u2015'] = " " # HORIZONTAL BAR
    rewrite_hash[u'\u2018'] = "'" # LEFT SINGLE QUOTATION MARK
    rewrite_hash[u'\u2019'] = "'" # RIGHT SINGLE QUOTATION MARK
    rewrite_hash[u'\u201A'] = " " # SINGLE LOW-9 QUOTATION MARK
    rewrite_hash[u'\u201C'] = " " # LEFT DOUBLE QUOTATION MARK
    rewrite_hash[u'\u201D'] = " " # RIGHT DOUBLE QUOTATION MARK
    rewrite_hash[u'\u201E'] = " " # DOUBLE LOW-9 QUOTATION MARK
    rewrite_hash[u'\u201F'] = " " # OUBLE HIGH-REVERSED-9 QUOTATION MARK

    rewrite_hash[u'\u2020'] = " " # DAGGER
    rewrite_hash[u'\u2021'] = " " # DOUBLE DAGGER
    rewrite_hash[u'\u2022'] = " " # BULLET
    rewrite_hash[u'\u2023'] = " " # TRIANGULAR BULLET
    rewrite_hash[u'\u2024'] = " " # ONE DOT LEADER
    rewrite_hash[u'\u2025'] = " " # TWO DOT LEADER
    rewrite_hash[u'\u2026'] = " " # HORIZONTAL ELLIPSIS
    rewrite_hash[u'\u2027'] = " " # HYPHENATION POINT
    rewrite_hash[u'\u2028'] = " " # LINE SEPARATOR
    rewrite_hash[u'\u2029'] = "\n" # PARAGRAPH SEPARATOR
    rewrite_hash[u'\u202A'] = " " # LEFT-TO-RIGHT EMBEDDING (???)
    rewrite_hash[u'\u202B'] = " " # RIGHT-TO-LEFT EMBEDDING (???)
    rewrite_hash[u'\u202C'] = " " # POP DIRECTIONAL FORMATTING (???)
    rewrite_hash[u'\u202D'] = " " # LEFT-TO-RIGHT OVERRIDE
    rewrite_hash[u'\u202E'] = " " # RIGHT-TO-LEFT OVERRIDE
    rewrite_hash[u'\u202F'] = " " # NARROW NO-BREAK SPACE

    rewrite_hash[u'\u2032'] = "\'"    # PRIME
    rewrite_hash[u'\u2033'] = " "     # DOUBLE PRIME
    rewrite_hash[u'\u203B'] = " "     # REFERENCE MARK

    rewrite_hash[u'\u206B'] = " "     # ACTIVATE SYMMETRIC SWAPPING
    rewrite_hash[u'\u206E'] = " "     # NATIONAL DIGIT SHAPES
    rewrite_hash[u'\u206F'] = " "     # NOMINAL DIGIT SHAPES

    rewrite_hash[u'\u20AC'] = " euros " # EURO SIGN

    rewrite_hash[u'\u2116'] = " "     # NUMERO SIGN
    rewrite_hash[u'\u2154'] = "2/3"   # VULGAR FRACTION TWO THIRDS
    rewrite_hash[u'\u2192'] = " "     # RIGHTWARDS ARROW
    rewrite_hash[u'\u21FC'] = " "     # LEFT RIGHT ARROW WITH DOUBLE VERTICAL STROKE
    rewrite_hash[u'\u2122'] = " "     # TRADE MARK SIGN

    rewrite_hash[u'\u2212'] = "-"     # MINUS SIGN

    rewrite_hash[u'\u23AF'] = " "     # HORIZONTAL LINE EXTENSION   
    rewrite_hash[u'\u25BA'] = " "     # BLACK RIGHT-POINTING POINTER
    rewrite_hash[u'\u2665'] = " "     # BLACK HEART SUIT

    rewrite_hash[u'\uFB01'] = "fi"  # LATIN SMALL LIGATURE FI
    rewrite_hash[u'\uFF00'] = " "  #
    return rewrite_hash

def remove_word_punctuation(ln):
    """
    This function removes punctuation from words.

    :param ln: String
    :return ln: String
    """
    ln = re.sub("^(\S+)[\.\!\?]", "\g<1>", ln)
    ln = re.sub("\s(\S+)[\.\!\?]", " \g<1>", ln)
    ln = re.sub("(\S+)[\.\!\?]$", "\g<1>", ln)
    ln = re.sub("\s[\.\!\?]\s", " ", ln)
    ln = re.sub("^[\.\!\?]$", "", ln)
    # Clean up extra spaces
    ln = re.sub('^\s+', '', ln)
    ln = re.sub('\s+$', '', ln)
    ln = re.sub('\s+', ' ', ln)
    return ln

def remove_markup(ln):
    """
    This function ...

    :param/return ln: String
    """
    # remove HTML style angle bracketed tags
    ln = re.sub('\<\S+\>', ' ', ln)
    # remove market symbols
    # ln = re.sub('\([A-Z0-9a-z\_]*\.[A-Z]+\:[^\)]+\)\,?', '', ln)
    # remove web site URLs and links
    ln = re.sub('https?:\/\/?\s*\S+\s', ' ', ln)
    ln = re.sub('https?:\/\/?\s*\S+$', '', ln)
    ln = re.sub('\(https?:\\\\\S+\)', ' ', ln)
    ln = re.sub('\(?www\.\S+\)?', ' ', ln)
    ln = re.sub('\[ID:[^\]]+\]', ' ', ln)
    ln = re.sub('\[id:[^\]]+\]', ' ', ln)
    ln = re.sub('\(PDF\)', ' ', ln)
    # replace html special characters
    ln = re.sub(r'&mdash;', ' ', ln)
    ln = re.sub(r'\&quot\;', ' ', ln)
    ln = re.sub(r'\&\#39\;', ' ', ln)
    # Clean up extra spaces
    ln = re.sub('^\s+', '', ln)
    ln = re.sub('\s+$', '', ln)
    ln = re.sub('\s+', ' ', ln)
    return ln

def remove_twitter_meta(ln):
    """
    This function removes metadata from tweets

    :param/return ln: String
    """
    # ln = re.sub(r'\#\S+', ' ', ln) # remove hashtags --old version
    # ln = re.sub(r'\@\S+', ' ', ln) # remove @tags -- old version

    # ln = re.sub(r'\#[a-zA-Z0-9_]+', ' ', ln) # remove hashtags
    ln = re.sub(r'\@[a-zA-Z0-9_]+', ' ', ln) # remove @tags
    ln = re.sub('\sRT\s', ' ', ln) # remove retweet marker
    ln = re.sub('^RT\s', ' ', ln)

    # Clean up extra spaces
    ln = re.sub('^\s+', '', ln)
    ln = re.sub('\s+$', '', ln)
    ln = re.sub('\s+', ' ', ln)
    return ln

# Adapted from TJs normalization code
def remove_nonsentential_punctuation(ln):
    """
    This function removes nonsentenial punctuation from text.

    :param/return ln: String
    """
    # remove '-'
    ln = re.sub('^\-+', '', ln)
    ln = re.sub('\-\-+', '', ln)
    ln = re.sub('\s\-+', '', ln)

    # remove '~'
    ln = re.sub('\~', ' ', ln)

    # remove standard double quotes
    ln = re.sub('\"', '', ln)

    # remove single quotes
    ln = re.sub("^\'+", '', ln)
    ln = re.sub("\'+$", '', ln)
    ln = re.sub("\'+\s+", ' ', ln)
    ln = re.sub("\s+\'+", ' ', ln)
    ln = re.sub("\s+\`+", ' ', ln)
    ln = re.sub("^\`+", ' ', ln)

    # remove ':'
    ln = re.sub("\:\s", " ", ln)
    ln = re.sub("\:$", "", ln)

    # remove ';'
    ln = re.sub('\;\s', ' ', ln)
    ln = re.sub('\;$', '', ln)

    # remove '_'
    ln = re.sub('\_+\s', ' ', ln)
    ln = re.sub('^\_+', '', ln)
    ln = re.sub('_+$', '', ln)
    ln = re.sub('\_\_+', ' ', ln)

    # remove ','
    ln = re.sub('\,+([\#A-Za-z])', ' \g<1>', ln) 
    ln = re.sub('\,+$', ' ', ln)
    ln = re.sub('\,\.\s', ' ', ln)
    ln = re.sub('\,\s', ' ', ln)

    # remove '*'
    ln = re.sub('\s\*+', ' ', ln)
    ln = re.sub('\*+\s', ' ', ln)
    ln = re.sub('\*\.', ' ', ln)
    ln = re.sub('\s\*+\s', ' ', ln)
    ln = re.sub('^\*+', '', ln)
    ln = re.sub('\*+$', '', ln)

    # Keep only one '.', '?', or '!' 
    ln = re.sub('\?[\!\?]+', '?', ln)
    ln = re.sub('\![\?\!]+', '!', ln)
    ln = re.sub('\.\.+', '.', ln)

    # # remove '/'
    ln = re.sub('\s\/', ' ', ln)
    ln = re.sub('\/\s', ' ', ln)

    # remove sentence final '!' and '?' 
    # ln = re.sub('[\!\?]+\s*$', '', ln)
    
    # remove other special characters
    ln = re.sub('\|', ' ', ln)
    ln = re.sub(r'\\', ' ', ln)

    # Remove parentheses that are not part of emoticons.
    # Note sure of the best way to do this, but here's a conservative 
    # approach.
    ln = re.sub('\(([@\#A-Za-z0-9])', '\g<1>', ln)
    ln = re.sub('([@\#A-Za-z0-9])\)', '\g<1> ', ln)

    # Clean up extra spaces
    ln = re.sub('^\s+', '', ln)
    ln = re.sub('\s+$', '', ln)
    ln = re.sub('\s+', ' ', ln)

    return ln

