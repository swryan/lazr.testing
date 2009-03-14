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

regexp = re.compile(re.escape('yourpkg'))


def parse_arguments():
    """Parse command line arguments.

    :return: The parser, the options, and the name of the package
    :rtype: 3-tuple of (parser instance, options instance, string)
    """
    parser = OptionParser(version=__version__,
                          usage="""\
%prog [options] name

Hack the files in the lazr project template to reflect the name of the project
you're creating.  After running this script, you should verify all changes
before committing them.""")
    parser.add_option('-k', '--keep', action='store_true', default=False,
                      help='Keep this prepare.py script after completion.')
    parser.add_option('-v', '--verbose',
                      dest='verbosity', action='count', default=0,
                      help='Increase verbosity.')
    parser.add_option('-n', '--dry-run', action='store_true', default=False,
                      help='Make no changes, just show what would be done.')
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


def hack_file(src, name, options):
    """Hack the contents of the file, essentially s/yourpkg/name/.

    :param src: The full path name of the file to hack.
    :type src: string
    :param name: The new package's name.
    :type name: string
    :param options: The options instance.
    :type options: Options
    """
    dest = src + '.tmp'
    total_substitution_count = 0
    with nested(open(src), open(dest, 'w')) as (in_file, out_file):
        for line in in_file:
            substituted, substitution_count = regexp.subn(name, line)
            out_file.write(substituted)
            total_substitution_count += substitution_count
    # Move the temporary file into place, unless dry-running.
    if options.dry_run or total_substitution_count == 0:
        os.remove(dest)
    else:
        os.rename(dest, src)
    if options.verbosity > 0:
        if options.verbosity > 1 or total_substitution_count > 0:
            print 'File:', src, 'changes:', total_substitution_count


def walk_and_replace(directory, name, options):
    """Walk the directory, looking for patterns in files to replace.

    :param directory: The directory to begin walking.
    :type directory: string
    :param name: The new package's name.
    :type name: string
    :param options: The options instance.
    :type options: Options
    """
    # Start by moving src/lazr/yourpkg to src/lazr/name.
    if options.verbosity > 0:
        print 'Moving src/lazr/yourpkg -> src/lazr/%s' % name
    if not options.dry_run:
        os.system('bzr mv src/lazr/yourpkg src/lazr/%s' % name)
    for dirpath, dirnames, filenames in os.walk(directory):
        # Skip the .bzr directory!
        if '.bzr' in dirnames:
            dirnames.remove('.bzr')
        for filename in filenames:
            # Skip the prepare.py file if we're not keeping it, otherwise bzr
            # rm will complain.
            if (not options.keep and
                os.path.join(dirpath, filename) == __file__):
                continue
            if filename.endswith('.pyc'):
                continue
            # We should do the substitution in every file.
            path = os.path.join(dirpath, filename)
            hack_file(path, name, options)


def main():
    parser, options, name = parse_arguments()
    # Do some basic sanity checking on the name.
    if name.startswith('lazr.'):
        name = name[5:]
    if name.count('.') > 0:
        parser.error('Name may not have dots in it')
    if options.dry_run:
        # --dry-run implies at least one level of verbosity.
        options.verbosity = max(options.verbosity, 1)
    walk_and_replace('.', name, options)
    if not options.keep:
        if options.verbosity > 0:
            print 'Removing prepare.py'
        if not options.dry_run:
            os.system('bzr rm prepare.py')


if __name__ == '__main__':
    main()
