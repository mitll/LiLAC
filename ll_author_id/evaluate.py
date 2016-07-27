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
Authors: Bill Campbell
Date: July 21, 2016
"""

import codecs
import gzip
import json
import numpy as np
from sklearn import metrics

def roc_curve(score_fn, key_fn):
    """
    This function computes the ROC curve given a score file and a key file

    :param score_fn:          Score file in either text or JSON format
    :param key_fn             Key file
    :return tpr, fpr, thresh  The computed ROC curve
    """

    # Load key
    with open(key_fn, 'r') as key_file:
        ans_key = json.load(key_file)

    # Load scores
    if score_fn.endswith('.gz'):
        score_file_raw = gzip.open(score_fn, 'r')
    else:
        score_file_raw = open(score_fn, 'r')
    score_file = codecs.getreader('utf-8')(score_file_raw)
    scores = []
    labels = []
    if score_fn.endswith('.txt') or score_fn.endswith('.txt.gz'):
        for ln in score_file:
            ln = ln.rstrip()
            f = ln.split()
            msg = f[0]
            model = f[1]
            score = float(f[2])
            if msg not in ans_key:
                print 'Message {} not found in answer key, skipping ...'
                continue
            if model==ans_key[msg]:
                labels.append(1.0)
            else:
                labels.append(0.0)
            scores.append(score)
    elif score_fn.endswith('.json') or score_fn.endswith('.json.gz'):
        scores_obj = json.load(score_file)
        for msg in scores_obj:
            if msg not in ans_key:
                print 'Message {} not found in answer key, skipping ...'
                continue
            for model in scores_obj[msg]:
                score = scores_obj[msg][model]
                scores.append(score)
                if model==ans_key[msg]:
                    labels.append(1.0)
                else:
                    labels.append(0.0)
    else:
        raise ValueError('Score file to evaluate must be txt, txt.gz, json, or json.gz')
    score_file_raw.close()

    # Evaluate
    labels = np.array(labels)
    scores = np.array(scores)
    fpr, tpr, thresh = metrics.roc_curve(labels, scores)
    return fpr,tpr, thresh
