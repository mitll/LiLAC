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
Date: July 20, 2016
"""

import codecs
import gzip
import json
import numpy as np
import os
from scipy import sparse
from sklearn.externals import joblib
from sklearn.svm import SVC
from subprocess import call
import sys
from train_models import read_sparse_training_file

def _read_tags(in_fn):
    tags = []
    with open(in_fn, "r") as fid_raw:
        fid = codecs.getreader('utf-8')(fid_raw)
        for ln in fid:
            ln = ln.rstrip()
            tags.append(ln)
    return tags

def score_all(in_fn, model_dir, train_tag_fn, test_tag_fn, out_fn, config, verbose=False):
    """
    This function scores all models against all input files

    :param in_fn:        Sparse, binary input file of all test count vectors
    :param model_dir:    Location of models for author ID
    :param train_tag_fn: File associating tag number to author
    :param out_fn:       Output file name
    :param config:       Configuration file for author ID parameters
    """

    if config['model']['method']=='svmtorch':
        raise Exception('score_all: SVMTorch interface not completed')
        # TODO: Use SVMTest to score
        print 'Scoring using SVMTorch ...'
        svmtest_exe = os.path.join(os.path.dirname(__file__), 'SVMTest')
        if not os.path.exists(svmtest_exe):
            raise Exception('score_all: SVMTest executable not found, {}'.format(svmtest_exe))
        # outfile_base = os.path.join(out_dir, "model")
        # cmd_list = "{} -multi -sparse -bin -t 1 -d 1 -c 10 -m 500".format(svmtorch_exe).split()
        # cmd_list.extend([in_fn, outfile_base])
        # if verbose:
        #     print 'Running command: {}'.format(cmd_list)
        # result = call(cmd_list)
    elif config['model']['method']=='sklearn':
        print 'Scoring using scikit learn ...'

        # Read in test data
        test_matrix, lbl_list = read_sparse_training_file(in_fn)
        test_matrix = test_matrix.tocsr()

        # Load models
        model_fn = os.path.join(model_dir, "models.dat")
        clf = joblib.load(model_fn)

        # Test SVM on data
        # out = clf.predict_proba(test_matrix)
        # out = clf.predict(test_matrix)
        out = clf.decision_function(test_matrix)
        
        # Write out to a file
        model_names = _read_tags(train_tag_fn)
        test_fns = _read_tags(test_tag_fn)

        # Iterate over array and output scores to a file
        json_output = False
        if out_fn.endswith('.json') or out_fn.endswith('.json.gz'):
            json_output = True
            output_dict = {}
        if out_fn.endswith('.gz'):
            outfile_raw = gzip.open(out_fn, 'w')
        else:
            outfile_raw = open(out_fn, 'w')
        outfile = codecs.getwriter('utf-8')(outfile_raw)
        it = np.nditer(out, flags=['multi_index'])
        while not it.finished:
            tst_msg = test_fns[it.multi_index[0]]
            tst_model = model_names[it.multi_index[1]]
            score = float(it[0])
            if json_output:
                if not output_dict.has_key(tst_msg):
                    output_dict[tst_msg] = {}
                output_dict[tst_msg][tst_model] = score
            else:
		#Esther added 'u'
                outfile.write(u'{} {} {}\n'.format(tst_msg, tst_model, score))
            it.iternext()
        if json_output:
            json.dump(output_dict, outfile)
        outfile_raw.close()

    else:
        raise ValueError('score_all: unknown training method -- use sklearn')
