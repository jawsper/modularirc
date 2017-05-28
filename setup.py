#!/usr/bin/env python3

from setuptools import setup, find_packages

import sys
sys.path.insert(0, 'src')
from modularirc import __version__

setup(
    name='modularirc',
    version=__version__,
    author='Jasper Seidel',
    author_email='code@jawsper.nl',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/jawsper/modularirc',
    license='LICENSE.txt',
    description='A modular, extensible IRC bot.',
    long_description=open('README.rst').read(),
    install_requires=[
        'irc',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],

    entry_points={
        'console_scripts': [
            'ircbot.py=modularirc.run:main'
        ]
    },
    test_suite='tests',
)