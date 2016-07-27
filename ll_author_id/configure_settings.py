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

Description: This script contains functions for editing the configuration settings for ll-authorid
"""


import os, json

# class configure_settings():
#     def __init__(self):
#         self.text_norm = {'utf8_to_ascii': True,              # Options: True or False
#                        'remove_twitter': True,             # Options: True or False
#                        'remove_markup': True,              # Options: True or False
#                        'remove_nonsentenial': True}       # Options: True or False
#         self.counts = {'combine_same_user_counts': True,   # Options: True or False
#                         'format': '.json',                  # Options: '.json', '.json.gz', '.txt', or '.txt.gz'
#                         'count_separator': '|'}
#         self.filter_counts = {}
#


def get_default_config():
    """
    This function loads the configuration settings JSON, or creates it.

    :return config_settings: Dictionary containing configuration settings
    """
    fn = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config_settings.json')
    if os.path.isfile(fn):
        with open(fn) as file_stream:
            config = json.load(file_stream)
        return config
    else:
        config = {'text_norm':
                      {'utf8_to_ascii': True,              # Options: True or False
                       'remove_twitter': True,             # Options: True or False
                       'remove_markup': True,              # Options: True or False
                       'remove_nonsentenial': True},       # Options: True or False
                  'counts':
                        {'combine_same_user_counts': True,   # Options: True or False
                        'format': '.json',                  # Options: '.json', '.json.gz', '.txt', or '.txt.gz'
                        'count_separator': '|'},
                  'filter_counts': {},
                  'model': {'method': 'sklearn'}}
        with open(fn, 'w') as outfile:
            json.dump(config, outfile)
    return config

