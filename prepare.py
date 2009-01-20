#! /usr/bin/env python

# Copyright 2009 Canonical Ltd.  All rights reserved.
#
# This file is part of lazr.yourpkg
#
# lazr.yourpkg is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# lazr.yourpkg is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lazr.yourpkg.  If not, see <http://www.gnu.org/licenses/>.

"""Prepare the lazr template for specialization."""

# This requires at least Python 2.5.
from __future__ import with_statement

import os
import re
import sys

from contextlib import nested
from optparse import OptionParser

sys.path.insert(0, 'src')
from lazr.yourpkg import __version__

cre = re.compile(re.escape('lazr.yourpkg'))


def parse_arguments():
    """Parse command line arguments.

    :return: The parser, the options, and the name of the package
    :rtype: 3-tuple of (parser instance, options instance, string)
    """
    parser = OptionParser(version=__version__,
                          usage="""\
%prog [options] name

Hack the files in the lazr project template to reflect the name of the project
you're creating.  This physically edits the files, dropping you into the
editor of your choice (via $EDITOR) for any changes this script can't
automate.  After running this script, you should verify all changes before
committing them.""")
    parser.add_option('-k', '--keep', action='store_true', default=False,
                      help='Keep this prepare.py script after completion.')
    # Parse the command line options.
    options, arguments = parser.parse_args()
    # There should be exactly one argument, which is the short name of the new
    # package.
    if len(arguments) < 1:
        parser.error('New package name is missing.')
        # No return.
    if len(arguments) > 1:
        parser.error('Unexpected arguments.')
        # No return.
    return parser, options, arguments[0]


def hack_file(src, new_name):
    """Hack the contents of the file, essentially s/yourpkg/new_name/.

    :param src: The full path name of the file to hack.
    :type src: string
    :param new_name: The new package's name.
    :type new_name: string
    """
    dest = src + '.tmp'
    replacement = 'lazr.' + new_name
    with nested(open(src), open(dest, 'w')) as (in_file, out_file):
        for line in in_file:
            substituted = cre.sub(replacement, line)
            out_file.write(substituted)
    # Move the temporary file into place.
    os.rename(dest, sr)


def walk_and_replace(directory):
    """Walk the directory, looking for patterns in files to replace.

    :param directory: The directory to begin walking.
    :type directory: string
    """
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            # We should do the substitution in every file.
            path = os.path.join(dirpath, filename)
            hack_file(path)


def main():
    parser, options, name = parse_arguments()
    walk_and_replace('.')
    if not options.keep:
        os.remove('prepare.py')


if __name__ == '__main__':
    main()
