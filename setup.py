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

import sys
from setuptools import setup, find_packages

# generic helpers primarily for the long_description
def generate(*docname_or_string):
    res = []
    for value in docname_or_string:
        if value.endswith('.txt'):
            f = open(value)
            value = f.read()
            f.close()
        res.append(value)
        if not value.endswith('\n'):
            res.append('')
    return '\n'.join(res)
# end generic helpers


sys.path.insert(0, 'src')
from lazr.yourpkg import __version__

setup(
    name='lazr.yourpkg',
    version=__version__,
    namespace_packages=['lazr'],
    packages=find_packages('src'),
    package_dir={'':'src'},
    include_package_data=True,
    zip_safe=False,
    maintainer='LAZR Developers',
    maintainer_email='lazr-developers@lists.launchpad.net',
    description=open('README.txt').readline().strip(),
    long_description=generate(
        'src/lazr/yourpkg/README.txt',
        'src/lazr/yourpkg/NEWS.txt'),
    license='LGPL v3',
    install_requires=[
        'setuptools',
        'zope.interface',
        ],
    url='https://launchpad.net/lazr.yourpkg',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python"],
    setup_requires=['eggtestinfo'],
    test_suite='lazr.yourpkg.tests.test_suite',
    )
