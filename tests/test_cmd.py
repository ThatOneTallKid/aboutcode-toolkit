#!/usr/bin/env python
# -*- coding: utf8 -*-

# ============================================================================
#  Copyright (c) 2014 nexB Inc. http://www.nexb.com/ - All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ============================================================================

from __future__ import absolute_import
from __future__ import print_function

import unittest

from about_tool import CRITICAL
from about_tool import DEBUG
from about_tool import ERROR
from about_tool import Error
from about_tool import INFO
from about_tool import NOTSET
from about_tool import WARNING
from about_tool import cmd
from about_tool import model
from about_tool import util

from utils import get_temp_file
from utils import get_test_loc


class CmdTest(unittest.TestCase):

    def check_csv(self, expected, result):
        """
        Compare two CSV files at locations as lists of ordered items.
        """
        def as_items(csvfile):
            mapping = None
            return sorted([i.items() for i in util.load_csv(mapping, csvfile)])

        expected = as_items(expected)
        result = as_items(result)
        assert expected == result

# NB: this test depends on py.test stdout/err capture capabilities
def test_log_errors(capsys):
    errors = [Error(CRITICAL, 'msg1'),
              Error(ERROR, 'msg2'),
              Error(INFO, 'msg3'),
              Error(WARNING, 'msg4'),
              Error(DEBUG, 'msg4'),
              Error(NOTSET, 'msg4'),
              ]
    cmd.log_errors(errors, base_dir='')
    out, err = capsys.readouterr()
    expected_out = '''CRITICAL: msg1
ERROR: msg2
INFO: msg3
WARNING: msg4
DEBUG: msg4
NOTSET: msg4
'''
    assert '' == err
    assert expected_out == out
