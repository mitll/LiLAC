#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Authors: Kelly Geyer, Bill Campbell
Date: May 11, 2016

Description: This script is an implementation of the processing step in ll-authorid. It converts text to word count
vectors. Text normalization settings are set by the user.
"""

import os
import ll_author_id as lai
import shutil
import sys

def main():
    # File of training user IDs and corresponding filenames
    train_fn_list = os.path.join(os.getcwd(), "lists", "train.txt")

    # Directories for models, counts, and temporary processing
    counts_dir = os.path.join(os.getcwd(), "counts")
    model_dir = os.path.join(os.getcwd(), "models")
    dict_fn = os.path.join(model_dir, "dict.json")
    tmp_dir = os.path.join(os.getcwd(), "tmp")

    # Steps for training
    do_counts = True
    do_build_training_vectors = True
    do_train_models = True

    # Counts parameters
    counts_output_format = '.json.gz' # Different output formats are '.txt', '.txt.gz', '.json', '.json.gz'
    counts_fn = os.path.join(counts_dir, 'train_counts' + counts_output_format)
    tag_fn = os.path.join(tmp_dir, 'training_tags.txt')

    # Model building parameters
    min_count = 0
    min_words = 200

    # Delete old directories and Create directories
    for d in [counts_dir, model_dir, tmp_dir]:
        if os.path.isdir(d):
            shutil.rmtree(d)
            os.mkdir(d)
        else:
            os.mkdir(d)

    # Normalize training documents and get word counts for each user id/file
    # text --> normalization --> counts --> outfile 
    if do_counts:
        print "Finding counts for text files ..."
        config = lai.get_default_config()
        config['counts']['combine_same_user_counts'] = False
        config['counts']['format'] = counts_output_format
        print 'Config for counts processing is: {}'.format(config)
        lai.text_to_counts(count_filename=counts_fn, id_filename_list=train_fn_list, config=config, text_filter_func=lai.market_text_filter, count_filter_func=lai.market_count_filter)

    # Train author ID
    vec_fn = os.path.join(tmp_dir, 'all_training_vectors.dat')
    if do_build_training_vectors:
        print "Finding dictionary ..."
        lai.find_dict(in_fn=counts_fn, out_fn=dict_fn, config=config)
        print "Converting counts to vectors ..."
        lai.ngm_to_vec(in_fn=counts_fn, dict_fn=dict_fn, out_fn=vec_fn, class_lbl='multi', tag_fn=tag_fn, config=config, min_count=min_count, min_words=min_words)

    if do_train_models:
        print 'Training author models ...'
        lai.train_models(in_fn=vec_fn, out_dir=model_dir, config=config)

if __name__ == '__main__':
    main()
