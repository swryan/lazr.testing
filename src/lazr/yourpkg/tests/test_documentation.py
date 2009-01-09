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
    # This breaks the zip-safe flag.
    docs_directory = os.path.normpath(os.path.join(__file__, '../../docs'))
    doctest_files = ['../docs/%s' % filename
                     for filename in os.listdir(docs_directory)
                     if filename.endswith('.txt')]

    return unittest.TestSuite((
        doctest.DocFileSuite(
            *doctest_files,
            module_relative=True,
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))
