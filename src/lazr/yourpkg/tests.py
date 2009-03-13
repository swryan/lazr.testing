# Copyright 2009 Canonical Ltd.  All rights reserved.

"""Test harness."""

__metaclass__ = type
__all__ = [
    'test_suite',
    ]

import os
import doctest
import unittest

DOCTEST_FLAGS = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_NDIFF)


def test_suite():
    package_directory = os.path.dirname(__file__)
    docs_directory = os.path.normpath(os.path.join(package_directory, 'docs'))
    if os.path.exists(docs_directory):
        doctest_files = [os.path.join('docs', filename)
                         for filename in os.listdir(docs_directory)
                         if filename.endswith('.txt')]
    else:
        doctest_files = []
    doctest_files.append('README.txt')
    kwargs = dict(module_relative=True, optionflags=DOCTEST_FLAGS)
    return unittest.TestSuite((
        doctest.DocFileSuite(*doctest_files, **kwargs)))
