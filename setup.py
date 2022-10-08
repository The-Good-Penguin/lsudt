#!/usr/bin/env python

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'lsudt',
    version = '0.2.1',
    author = 'Andrew Murray',
    author_email = 'amurray@thegoodpenguin.co.uk',
    description = 'Utility to list USB devices including associated Linux devices',
    license = 'GPLv2',
    keywords = 'usb list devices lsusb udev pyudev',
    url = 'https://github.com/The-Good-Penguin/lsudt',
    packages = ['lsudt'],
    install_requires = ['pyudev', 'pyyaml'],
    long_description_content_type='text/markdown',
    long_description = read('README.md'),
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'lsudt = lsudt.lsudt:main'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: System :: Hardware :: Universal Serial Bus (USB)',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
)
