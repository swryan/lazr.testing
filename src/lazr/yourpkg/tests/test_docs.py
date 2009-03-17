# Copyright 2009 Canonical Ltd.  All rights reserved.

"""Test harness."""

__metaclass__ = type
__all__ = [
    'additional_tests',
    ]

import atexit
import doctest
import os
import pkg_resources
import unittest

DOCTEST_FLAGS = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_NDIFF)


def additional_tests():
    doctest_files = [
        os.path.abspath(
            pkg_resources.resource_filename('lazr.yourpkg', 'README.txt'))]
    if pkg_resources.resource_exists('lazr.yourpkg', 'docs'):
        for name in pkg_resources.resource_listdir('lazr.yourpkg', 'docs'):
            if name.endswith('.txt'):
                doctest_files.append(
                    os.path.abspath(
                        pkg_resources.resource_filename(
                            'lazr.yourpkg', 'docs/%s' % name)))
    kwargs = dict(module_relative=False, optionflags=DOCTEST_FLAGS)
    atexit.register(pkg_resources.cleanup_resources)
    return unittest.TestSuite((
        doctest.DocFileSuite(*doctest_files, **kwargs)))
