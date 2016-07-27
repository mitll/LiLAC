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
Date: May 12, 2016
Installation: Python 2.7 on Windows 7

Description: This script contains ...
"""

import re, gzip, numpy as np, codecs, struct, json
from operator import itemgetter

def find_dict(in_fn, out_fn, config):
    """
    This function computes Common N-Gram (CNG) dissimilarity scores from word count vectors. The CNG dissimilarity calculations are givin in "Author Verification Using Common N-Gram Profiles of Text Documents"

    :param in_fn: Input file of counts in one of the formats '.txt', '.txt.gz', '.json', or '.json.gz'
    :param out_fn: Dictionary output file of Common N-Gram (CNG) dissimilarity scores, in one of the formats '.json' or '.json.gz'
    """
    # Check for valid file format
    assert (True in [str(in_fn).endswith(x) for x in ['.txt', '.txt.gz', '.json', '.json.gz']]), "The file {} must have one of the following extensions: '.txt', '.txt.gz', '.json', or '.json.gz'".format(in_fn)
    assert (True in [str(out_fn).endswith(x) for x in ['.json', '.json.gz']]), "The file {} must end with either the extension '.json' or '.json.gz'".format(out_fn)

    # Open input counts file and read it in
    ngms = {}
    if in_fn.endswith('.gz'):
        open_cmd = gzip.open
    else:
        open_cmd = open
    with open_cmd(in_fn, 'r') as f_raw:
        f = codecs.getreader('utf-8')(f_raw)
        if in_fn.endswith('.txt') or in_fn.endswith('.txt.gz'):
            for ln in f:
                ln = ln.strip()
                ln = ln.split("\t")
                if len(ln) < 3:
                    continue
                ln = ln[2:]
                for pr in ln:
                    wrd, cnt = pr.split(config['counts']['count_separator'])
                    wrd = wrd.strip()
                    cnt = float(cnt)
                    if (wrd.strip() == '') or (cnt < 1.):
                        continue
                    if wrd not in ngms:
                        ngms[wrd] = 0.
                    ngms[wrd] += cnt
        elif in_fn.endswith('.json') or in_fn.endswith('.json.gz'):
            raw_dict = json.load(f)
            for un in raw_dict.keys():
                for fn in raw_dict[un].keys():
                    for wrd in raw_dict[un][fn]:
                        wrd = wrd.strip()
                        if wrd not in ngms:
                            ngms[wrd] = 0.
                        ngms[wrd] += raw_dict[un][fn][wrd]

    # Now normalize dictionary
    s = 0.0
    for val in ngms.itervalues():
        s += val
    for ky, val in ngms.iteritems():
        ngms[ky] = val/s

    # Print n-grams and save to .JSON-type file
    output_file = codecs.open(out_fn, 'w', encoding='utf-8')
    json.dump(ngms, output_file, sort_keys=True, ensure_ascii=False)

def ngm_to_vec(in_fn, dict_fn, out_fn, class_lbl, tag_fn, config, min_count=0, min_words=0, doc_tags=False):
    """
    Ngram to vector -- written by BC, 7/25/2013
    Mods for gzip i/o, 6/24/2015

    @param in_fn: Input file of counts produced by text_to_counts
    @param dict: .json or .json.gz file containing dictionary of n-grams produced by find_dict
    @param min_count: minimum count to vectorize, default value 0
    @param min_words: minimum words to vectorize, default value 0
    @param out_fn: binary svm output file, format '.dat'
    @param label: class label, usually -1/1 or 0...n
    @param tags: tag output file????
    @return ????
    """

    # Check file names of in_fn, dict_fn and out_fn
    assert (True in [str(in_fn).endswith(x) for x in ['.txt', '.txt.gz', '.json', '.json.gz']]), "The file {} must have one of the following extensions: '.txt', '.txt.gz', '.json', or '.json.gz'".format(in_fn)
    assert (True in [str(dict_fn).endswith(x) for x in ['.json', '.json.gz']]), "The file {} must end with either the extension '.json' or '.json.gz'".format(dict_fn)
    assert (str(out_fn).endswith('.dat')), "The file {} must end with either the extension '.dat'".format(out_fn)

    if (class_lbl!='multi'):
        class_lbl = float(class_lbl)

    # Read in dictionary
    ngms_scale = {}
    ngms_idx = {}
    idx = 1  # make the indices 1-based  
    dict_file = file(dict_fn, 'r')
    raw_dict = json.loads(dict_file.read().decode('utf-8-sig'))
    for kk in raw_dict:
        ngms_idx[kk] = idx
        ngms_scale[kk] = np.log(1. / float(raw_dict[kk])) + 1.
        idx += 1

    # Now read in counts and output binary vectors
    ngms = {}

    # Read infile, process as dictionary
    # if (re.search("\.gz$", in_fn)):
    #     infile_raw = gzip.open(in_fn, 'r')
    #     infile = codecs.getreader('utf-8')(infile_raw)
    # else:
    #     infile = codecs.open(in_fn, 'r', encoding='utf-8')

    if in_fn.endswith('.gz'):
        open_cmd = gzip.open
    else:
        open_cmd = open
    with open_cmd(in_fn, 'r') as f_raw:
        f = codecs.getreader('utf-8')(f_raw)
        if in_fn.endswith('.txt') or in_fn.endswith('.txt.gz'):
            all_counts = {}
            for ln in f:
                ln = ln.strip()
                ln = ln.split("\t")
                if len(ln) < 3:
                    continue
                userid = ln[0].strip()
                if userid not in all_counts:
                    all_counts[userid] = {}
                fn = ln[1].strip()
                if fn not in all_counts[userid]:
                    all_counts[userid][fn] = {}
                ln = ln[2:]
                for pr in ln:
                    wrd, cnt = pr.split(config['counts']['count_separator'])
                    wrd = wrd.strip()
                    cnt = float(cnt)
                    if (wrd.strip() == '') or (cnt < 1.):
                        continue
                    if wrd not in all_counts[userid][fn]:
                        all_counts[userid][fn][wrd] = 0.
                    all_counts[userid][fn][wrd] += cnt
        if in_fn.endswith('.json') or in_fn.endswith('.json.gz'):
            all_counts = json.load(f)
    
    with open(out_fn, 'wb') as outfile:
        with codecs.open(tag_fn, 'w', encoding='utf-8') as tag_file:
            outfile.write(struct.pack('ii', int(0), int(idx)))
            num_vecs = 0
            num_authors = 0
            for auth in all_counts:
                write_to_tag_file = False
                for doc in all_counts[auth]:
                    tag = auth

                    # Skip if too few words, even if there's plenty of counts
                    if len(all_counts[auth][doc].keys()) < min_words:
                        continue

                    # First pass -- total prob
                    cnt_total = 0.
                    for pr in all_counts[auth][doc]:
                        if pr in ngms_idx:
                            cnt_total += all_counts[auth][doc][pr]

                    # Check for all unseen words or too few words
                    if (cnt_total == 0) or (cnt_total < min_count):
                        continue

                    # Second pass -- create vector pairs
                    vec_list = []
                    for pr in all_counts[auth][doc]:
                        if pr in ngms_idx:
                            vec_idx = ngms_idx[pr]
                            wrd_prob = all_counts[auth][doc][pr] / cnt_total
                            vec_val = wrd_prob * ngms_scale[pr]
                            vec_list.append((vec_idx, vec_val))
                    vec_list = sorted(vec_list, key=itemgetter(0))

                    # Now write out in binary format
                    outfile.write(struct.pack('i', len(vec_list)))
                    for pr in vec_list:
                        # for some reasoning combining these into one 'id' pack doesn't work
                        outfile.write(struct.pack('i', pr[0]))
                        outfile.write(struct.pack('d', pr[1]))
                    if class_lbl == 'multi':
                        outfile.write(struct.pack('d', num_authors))
                    else:
                        outfile.write(struct.pack('d', class_lbl))

                    # Next iteration
                    write_to_tag_file = True
                    if doc_tags:
			#Esther added 'u'
                        tag_file.write(u"{}\n".format(doc))
                        write_to_tag_file = False
                    num_vecs += 1

                if write_to_tag_file:
		    #Esther added 'u'
                    tag_file.write(u"{}\n".format(tag))
                    num_authors += 1

    # Reopen file and modify number of vecs
    with open(out_fn, 'r+b') as outfile:
        outfile.write(struct.pack('i', num_vecs))
