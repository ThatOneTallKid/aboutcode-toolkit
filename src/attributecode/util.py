#!/usr/bin/env python
# -*- coding: utf8 -*-
# ============================================================================
#  Copyright (c) 2013-2018 nexB Inc. http://www.nexb.com/ - All rights reserved.
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
import ntpath
import os
import posixpath
import shutil
import string
import sys

from attributecode import CRITICAL
from attributecode import WARNING
from attributecode import Error


python2 = sys.version_info[0] < 3

if python2:  # pragma: nocover
    from itertools import izip_longest as zip_longest  # NOQA
else:  # pragma: nocover
    from itertools import zip_longest  # NOQA

if python2:  # pragma: nocover
    from backports import csv  # NOQA
    # monkey patch backports.csv until bug is fixed
    # https://github.com/ryanhiebert/backports.csv/issues/30
    csv.dict = OrderedDict
else:  # pragma: nocover
    import csv  # NOQA


on_windows = 'win32' in sys.platform


def to_posix(path):
    """
    Return a path using the posix path separator given a path that may contain
    posix or windows separators, converting "\\" to "/". NB: this path will
    still be valid in the windows explorer (except for a UNC or share name). It
    will be a valid path everywhere in Python. It will not be valid for windows
    command line operations.
    """
    return path.replace(ntpath.sep, posixpath.sep)


UNC_PREFIX = u'\\\\?\\'
UNC_PREFIX_POSIX = to_posix(UNC_PREFIX)
UNC_PREFIXES = (UNC_PREFIX_POSIX, UNC_PREFIX,)

valid_file_chars = string.digits + string.ascii_letters + '_-.' + ' '


def invalid_chars(path):
    """
    Return a list of invalid characters in the file name of `path`.
    """
    path = to_posix(path)
    rname = resource_name(path)
    name = rname.lower()
    return [c for c in name if c not in valid_file_chars]


def check_file_names(paths):
    """
    Given a sequence of file paths, check that file names are valid and that
    there are no case-insensitive duplicates in any given directories.
    Return a list of errors.

    From spec :
        A file name can contain only these US-ASCII characters:
        - digits from 0 to 9
        - uppercase and lowercase letters from A to Z
        - the _ underscore, - dash and . period signs.
    From spec:
     The case of a file name is not significant. On case-sensitive file
     systems (such as Linux), a tool must raise an error if two ABOUT files
     stored in the same directory have the same lowercase file name.
    """
    # FIXME: this should be a defaultdicts that accumulates all duplicated paths
    seen = {}
    errors = []
    for orig_path in paths:
        path = orig_path
        invalid = invalid_chars(path)
        if invalid:
            invalid = ''.join(invalid)
            msg = ('Invalid characters %(invalid)r in file name at: '
                   '%(path)r' % locals())
            errors.append(Error(CRITICAL, msg))

        path = to_posix(orig_path)
        name = resource_name(path).lower()
        parent = posixpath.dirname(path)
        path = posixpath.join(parent, name)
        path = posixpath.normpath(path)
        path = posixpath.abspath(path)
        existing = seen.get(path)
        if existing:
            msg = ('Duplicate files: %(orig_path)r and %(existing)r '
                   'have the same case-insensitive file name' % locals())
            errors.append(Error(CRITICAL, msg))
        else:
            seen[path] = orig_path
    return errors


# TODO: rename to normalize_path
def get_absolute(location):
    """
    Return an absolute normalized location.
    """
    location = os.path.expanduser(location)
    location = os.path.expandvars(location)
    location = os.path.normpath(location)
    location = os.path.abspath(location)
    return location


def get_relative_path(base_loc, full_loc):
    """
    Return a posix path for a given full location relative to a base location.
    The first segment of the different between full_loc and base_loc will become
    the first segment of the returned path.
    """
    def norm(p):
        if p.startswith(UNC_PREFIX) or p.startswith(to_posix(UNC_PREFIX)):
            p = p.strip(UNC_PREFIX).strip(to_posix(UNC_PREFIX))
        p = to_posix(p)
        p = p.strip(posixpath.sep)
        p = posixpath.normpath(p)
        return p

    base = norm(base_loc)
    path = norm(full_loc)

    assert path.startswith(base), ('Cannot compute relative path: '
                                   '%(path)r does not start with %(base)r'
                                   % locals())
    base_name = resource_name(base)
    no_dir = base == base_name
    same_loc = base == path
    if same_loc:
        # this is the case of a single file or single dir
        if no_dir:
            # we have no dir: the full path is the same as the resource name
            relative = base_name
        else:
            # we have at least one dir
            parent_dir = posixpath.dirname(base)
            parent_dir = resource_name(parent_dir)
            relative = posixpath.join(parent_dir, base_name)
    else:
        relative = path[len(base) + 1:]
        # We don't want to keep the first segment of the root of the returned path.
        # See https://github.com/nexB/attributecode/issues/276
        # relative = posixpath.join(base_name, relative)
    return relative


def to_native(path):
    """
    Return a path using the current OS path separator given a path that may
    contain posix or windows separators, converting "/" to "\\" on windows
    and "\\" to "/" on posix OSes.
    """
    path = path.replace(ntpath.sep, os.path.sep)
    path = path.replace(posixpath.sep, os.path.sep)
    return path


def resource_name(path):
    """
    Return the file or directory name from a path.
    """
    path = path.strip()
    path = to_posix(path)
    path = path.rstrip(posixpath.sep)
    _left, right = posixpath.split(path)
    return right.strip()


def extract_zip(location):
    """
    Extract a zip file at location in a temp directory and return the temporary
    directory where the archive was extracted.
    """
    import zipfile
    import tempfile

    if not zipfile.is_zipfile(location):
        raise Exception('Incorrect zip file %(location)r' % locals())

    archive_base_name = os.path.basename(location).replace('.zip', '')
    base_dir = tempfile.mkdtemp(prefix='aboutcode-toolkit-extract-')
    target_dir = os.path.join(base_dir, archive_base_name)
    target_dir = add_unc(target_dir)

    os.makedirs(target_dir)

    if target_dir.endswith((ntpath.sep, posixpath.sep)):
        target_dir = target_dir[:-1]

    with zipfile.ZipFile(location) as zipf:
        for info in zipf.infolist():
            name = info.filename
            content = zipf.read(name)
            target = os.path.join(target_dir, name)
            is_dir = target.endswith((ntpath.sep, posixpath.sep))
            if is_dir:
                target = target[:-1]
            parent = os.path.dirname(target)
            if on_windows:
                target = target.replace(posixpath.sep, ntpath.sep)
                parent = parent.replace(posixpath.sep, ntpath.sep)
            if not os.path.exists(parent):
                os.makedirs(add_unc(parent))
            if not content and is_dir:
                if not os.path.exists(target):
                    os.makedirs(add_unc(target))
            if not os.path.exists(target):
                with open(target, 'wb') as f:
                    f.write(content)
    return target_dir


def add_unc(location):
    """
    Convert a `location` to an absolute Window UNC path to support long paths on
    Windows. Return the location unchanged if not on Windows. See
    https://msdn.microsoft.com/en-us/library/aa365247.aspx
    """
    if on_windows and not location.startswith(UNC_PREFIX):
        if location.startswith(UNC_PREFIX_POSIX):
            return UNC_PREFIX + os.path.abspath(location.strip(UNC_PREFIX_POSIX))
        return UNC_PREFIX + os.path.abspath(location)
    return location


# FIXME: add docstring
def copy_license_notice_files(fields, base_dir, reference_dir, afp):
    """
    Given a list of (key, value) `fields` tuples and a `base_dir` where ABOUT
    files and their companion LICENSE are stored, and an extra `reference_dir`
    where reference license and notice files are stored and the `afp`
    about_file_path value, this function will copy to the base_dir the
    license_file or notice_file if found in the reference_dir

    """
    lic_name = ''
    for key, value in fields:
        if not key in ('license_file','notice_file'):
            continue
        lic_name = value

        from_lic_path = posixpath.join(to_posix(reference_dir), lic_name)
        about_file_dir = os.path.dirname(to_posix(afp)).lstrip('/')
        to_lic_path = posixpath.join(to_posix(base_dir), about_file_dir)

        if on_windows:
            from_lic_path = add_unc(from_lic_path)
            to_lic_path = add_unc(to_lic_path)

        # Strip the white spaces
        from_lic_path = from_lic_path.strip()
        to_lic_path = to_lic_path.strip()

        # Errors will be captured when doing the validation
        if not posixpath.exists(from_lic_path):
            continue

        if not posixpath.exists(to_lic_path):
            os.makedirs(to_lic_path)

        shutil.copy2(from_lic_path, to_lic_path)


def unique(sequence):
    """
    Return a list of unique items found in sequence. Preserve the original
    sequence order.
    For example:
    >>> unique([1, 5, 3, 5])
    [1, 5, 3]
    """
    deduped = []
    for item in sequence:
        if item not in deduped:
            deduped.append(item)
    return deduped


def filter_errors(errors, minimum_severity=WARNING):
    """
    Return a list of unique `errors` Error object filtering errors that have a
    severity below `minimum_severity`.
    """
    return unique([e for e in errors if e.severity >= minimum_severity])

