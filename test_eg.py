#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Authors: Bill Campbell
Date: July 20, 2016

Description: This script is an implementation of the processing step in ll-authorid. It converts text to word count
vectors. Text normalization settings are set by the user.
"""

import matplotlib.pyplot as plt
import os
import ll_author_id as lai
import sys

def main():
    # Setup of files and directories
    id_fn_list = os.path.join(os.getcwd(), "lists", "test.txt")
    key_fn = os.path.join(os.getcwd(), "lists", "key.json")

    counts_dir = os.path.join(os.getcwd(), "counts")

    model_dir = os.path.join(os.getcwd(), "models")
    dict_fn = os.path.join(model_dir, "dict.json")

    tmp_dir = os.path.join(os.getcwd(), "tmp")
    score_fn = os.path.join(tmp_dir, "scores.txt")
    training_tag_fn = os.path.join(tmp_dir, "training_tags.txt")
    testing_tag_fn = os.path.join(tmp_dir, "testing_tags.txt")

    # Steps for training
    do_counts = True
    do_build_testing_vectors = True
    do_scoring = True
    do_evaluation = True

    # Counts parameters
    counts_output_format = '.json.gz' # Different output formats are '.txt', '.txt.gz', '.json', '.json.gz'
    counts_fn = os.path.join(counts_dir, 'test_counts' + counts_output_format)

    # Model building parameters
    min_count = 0
    min_words = 200

    # Normalize training documents and get word counts for each user id/file
    # text --> normalization --> counts --> outfile
    if do_counts:
        print "Finding counts for text files ..."
        config = lai.get_default_config()
        config['counts']['combine_same_user_counts'] = False
        config['counts']['format'] = counts_output_format
        print 'Config for counts processing is: {}'.format(config)
        lai.text_to_counts(count_filename=counts_fn, id_filename_list=id_fn_list, config=config, text_filter_func=lai.market_text_filter, count_filter_func=lai.market_count_filter)

    # Create testing vectors
    vec_fn = os.path.join(tmp_dir, 'all_testing_vectors.dat')
    if do_build_testing_vectors:
        print "Converting counts to vectors ..."
        lai.ngm_to_vec(in_fn=counts_fn, dict_fn=dict_fn, out_fn=vec_fn, class_lbl='multi', tag_fn=testing_tag_fn, config=config, min_count=min_count, min_words=min_words, doc_tags=True)

    # Score all models against all vectors
    if do_scoring:
        print 'Scoring author models ...'
        lai.score_all(in_fn=vec_fn, model_dir=model_dir, train_tag_fn=training_tag_fn, test_tag_fn=testing_tag_fn, out_fn=score_fn, config=config)

    # Evaluate
    if do_evaluation:
        # Calculate and plot ROC curve
        print 'Evaluating results with key: {}'.format(key_fn)
        fpr, tpr, thresh = lai.roc_curve(score_fn=score_fn, key_fn=key_fn)
        plt.plot(fpr, tpr, label='LiLAC')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('LiLAC Performance on a Small Train/Test Dataset')
        plt.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Chance')
        plt.grid()
        plt.legend()
        plt.show()

if __name__ == '__main__':
    main()
