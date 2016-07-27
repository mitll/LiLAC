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
Date: July 19, 2016 (an important date)
"""

import numpy as np
import os
from scipy import sparse
from sklearn.externals import joblib
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from subprocess import call
import struct
import sys

def train_models(in_fn, out_dir, config, verbose=False):
    """
    This function trains models

    :param in_fn:   Sparse, binary input file for training author ID models
    :param out_dir: Output directory for storing models
    :param config:  Configuration file for author ID parameters
    """

    if config['model']['method']=='svmtorch':
        raise Exception('score_all: SVMTorch interface not completed')
        # TODO: Eliminate debug from SVMTorch exe, compact models, include compact model source
        # TODO: Include SVMTorch source
        print 'Using SVMTorch training ...'
        svmtorch_exe = os.path.join(os.path.dirname(__file__), 'SVMTorch')
        if not os.path.exists(svmtorch_exe):
            raise Exception('train_models: SVMTorch executable not found, {}'.format(svmtorch_exe))
        outfile_base = os.path.join(out_dir, "model")
        cmd_list = "{} -multi -sparse -bin -t 1 -d 1 -c 10 -m 500".format(svmtorch_exe).split()
        cmd_list.extend([in_fn, outfile_base])
        if verbose:
            print 'Running command: {}'.format(cmd_list)
        result = call(cmd_list)
    elif config['model']['method']=='sklearn':
        print 'Using scikit learn SVM training ...'
        trn_matrix, lbl_list = read_sparse_training_file(in_fn)
        trn_matrix.tocsr()
        trn_label = np.array(lbl_list)

        # Summary of data
        if verbose:
            print 'Train matrix shape: {}'.format(trn_matrix.shape)
            print 'Labels: {}'.format(trn_label)

        # Train SVM
        # clf = SVC(kernel='linear', probability=True)
        clf = LinearSVC(C=10.0)
        clf.fit(trn_matrix, trn_label)
        if verbose:
            print 'Number of support vectors: {}'.format(clf.n_support_)

        # Save models
        model_fn = os.path.join(out_dir, 'models.dat')
        joblib.dump(clf, model_fn, compress=9)
    else:
        raise ValueError('build_models: unknown training method -- use svmtorch or sklearn')

def read_sparse_training_file (fn):
    i1 = []
    j1 = []
    data = []
    lbl = []
    row_num = 0
    with open(fn, 'rb') as infile:
        num_inst = struct.unpack('i', infile.read(4))[0]
        dim = struct.unpack('i', infile.read(4))[0]
        if (num_inst<=0) or (dim<=0):
            print "The bad file is {}".format(fn)
            raise ValueError('read_sparse_training_file: error in training file')
        for i in xrange(num_inst):
            num_in_vec = struct.unpack('i', infile.read(4))[0]
            if num_in_vec<=0:
                raise ValueError('read_sparse_training_file: error in training file')
            for j in xrange(num_in_vec):
                ind = struct.unpack('i', infile.read(4))[0]
                val = struct.unpack('d', infile.read(8))[0]
                data.append(val)
                i1.append(row_num)
                j1.append(ind)
            lbl_val = struct.unpack('d', infile.read(8))[0]
            lbl.append(lbl_val)
            row_num += 1
    train_matrix =  sparse.coo_matrix((data,(i1,j1)),[row_num,dim], dtype=np.float64)
    return train_matrix, lbl
