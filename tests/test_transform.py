#!/usr/bin/env python
# -*- coding: utf8 -*-

# ============================================================================
#  Copyright (c) 2014-2020 nexB Inc. http://www.nexb.com/ - All rights reserved.
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
from __future__ import unicode_literals

from collections import OrderedDict
import unittest

from testing_utils import get_temp_dir
from testing_utils import get_test_loc

from attributecode import ERROR
from attributecode import INFO
from attributecode import CRITICAL
from attributecode import Error
from attributecode import gen

from attributecode.transform import check_duplicate_fields
from attributecode.transform import read_json
from attributecode.transform import transform_data
from attributecode.transform import normalize_dict_data
from attributecode.transform import Transformer

from attributecode.util import python2

if python2:  # pragma: nocover
    from itertools import izip_longest as zip_longest  # NOQA
else:  # pragma: nocover
    from itertools import zip_longest  # NOQA

class TransformTest(unittest.TestCase):
    def test_transform_data_new_col(self):
        data = [OrderedDict([(u'Directory/Filename', u'/tmp/test.c'), (u'Component', u'test.c'),
                             (u'version', '1'), (u'notes', u'test'), (u'temp', u'foo')])]
        configuration = get_test_loc('test_transform/configuration_new_cols')
        transformer = Transformer.from_file(configuration)

        field_name, data, err = transform_data(data, transformer)

        expect_name = [u'path',u'about_resource', u'name',u'version',u'notes',u'temp']
        expected_data = [dict(OrderedDict([(u'path', u'/tmp/test.c'),
                                           (u'about_resource', u'/tmp/test.c'),
                                           (u'name', u'test.c'), (u'version', u'1'),
                                           (u'notes', u'test'),(u'temp', u'foo')]))]
        assert len(field_name) == len(expect_name)
        for name in field_name:
            assert name in expect_name
        assert len(data) == len(expected_data)
        for d in data:
            assert dict(d) in expected_data

    def test_transform_data(self):
        data = [OrderedDict([(u'Directory/Filename', u'/tmp/test.c'),
                             (u'Component', u'test.c'), (u'version', u'1'),
                             (u'notes', u'test'), (u'temp', u'foo')])]
        configuration = get_test_loc('test_transform/configuration')
        transformer = Transformer.from_file(configuration)

        field_name, data, err = transform_data(data, transformer)

        expect_name = [u'about_resource', u'name', u'version']
        expected_data = [dict(OrderedDict([(u'about_resource', u'/tmp/test.c'), (u'name', u'test.c'), (u'version', u'1')]))]

        assert len(field_name) == len(expect_name)
        for name in field_name:
            assert name in expect_name
        assert len(data) == len(expected_data)
        for d in data:
            assert dict(d) in expected_data

    def test_transform_data_mutli_rows(self):
        data = [OrderedDict([(u'Directory/Filename', u'/tmp/test.c'), (u'Component', u'test.c'), (u'Confirmed Version', u'v0.01')]),
                OrderedDict([(u'Directory/Filename', u'/tmp/tmp.h'), (u'Component', u'tmp.h'), (u'Confirmed Version', None)])]
        configuration = get_test_loc('test_transform/configuration2')
        transformer = Transformer.from_file(configuration)

        field_name, data, err = transform_data(data, transformer)

        expect_name = [u'about_resource', u'name', u'version']
        expected_data = [dict(OrderedDict([(u'about_resource', u'/tmp/test.c'), (u'name', u'test.c'), (u'version', u'v0.01')])),
                         dict(OrderedDict([(u'about_resource', u'/tmp/tmp.h'), (u'name', u'tmp.h'), (u'version', None)]))]

        assert len(field_name) == len(expect_name)
        for name in field_name:
            assert name in expect_name
        assert len(data) == len(expected_data)
        for d in data:
            assert dict(d) in expected_data

    def test_normalize_dict_data_scancode(self):
        test_file = get_test_loc('test_transform/input_scancode.json')
        json_data = read_json(test_file)
        data = normalize_dict_data(json_data)
        expected_data = [OrderedDict([(u'path', u'samples'),
                                 (u'type', u'directory'),
                                 (u'name', u'samples'),
                                 (u'base_name', u'samples'),
                                 (u'extension', u''), (u'size', 0),
                                 (u'date', None),(u'sha1', None), (u'md5', None),
                                 (u'mime_type', None), (u'file_type', None),
                                 (u'programming_language', None),
                                 (u'is_binary', False), (u'is_text', False),
                                 (u'is_archive', False), (u'is_media', False),
                                 (u'is_source', False), (u'is_script', False),
                                 (u'licenses', []), (u'license_expressions', []),
                                 (u'copyrights', []), (u'holders', []),
                                 (u'authors', []), (u'packages', []),
                                 (u'emails', []), (u'urls', []),
                                 (u'files_count', 33), (u'dirs_count', 10),
                                 (u'size_count', 1161083), (u'scan_errors', [])])]
        assert data == expected_data

    def test_normalize_dict_data_json(self):
        json_data = OrderedDict([(u'Directory/Filename', u'/aboutcode-toolkit/'),
                                 (u'Component', u'AboutCode-toolkit'),
                                 (u'version', u'1.2.3'), (u'note', u'test'),
                                 (u'temp', u'foo')])
        data = normalize_dict_data(json_data)
        expected_data = [OrderedDict([(u'Directory/Filename', u'/aboutcode-toolkit/'),
                                      (u'Component', u'AboutCode-toolkit'),
                                      (u'version', u'1.2.3'), (u'note', u'test'),
                                      (u'temp', u'foo')])]
        assert data == expected_data

    def test_normalize_dict_data_json_array(self):
        json_data = [OrderedDict([(u'Directory/Filename', u'/aboutcode-toolkit/'),
                    (u'Component', u'AboutCode-toolkit'),
                    (u'version', u'1.0'), (u'temp', u'fpp')]),
                    OrderedDict([(u'Directory/Filename', u'/aboutcode-toolkit1/'),
                    (u'Component', u'AboutCode-toolkit1'),
                    (u'version', u'1.1'), (u'temp', u'foo')])]
        data = normalize_dict_data(json_data)
        expected_data = [OrderedDict([(u'Directory/Filename', u'/aboutcode-toolkit/'),
                        (u'Component', u'AboutCode-toolkit'),
                        (u'version', u'1.0'), (u'temp', u'fpp')]),
                        OrderedDict([(u'Directory/Filename', u'/aboutcode-toolkit1/'),
                        (u'Component', u'AboutCode-toolkit1'),
                        (u'version', u'1.1'),
                        (u'temp', u'foo')])]
        assert data == expected_data

    def test_check_duplicate_fields(self):
        field_name = ['path', 'name', 'path', 'version']
        expected = ['path']
        dups = check_duplicate_fields(field_name)
        assert dups == expected

