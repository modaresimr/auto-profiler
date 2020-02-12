#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='auto_profiler',
    version=1.3,
    description='A timer for profiling a Python function or snippet.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='modaresi mr',
    author_email='modaresimr+git@gmail.com',
    url="https://github.com/modaresimr/auto_profiler",
    keywords='Profiling, Timer, Python, Auto prfiling, line profiler',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'monotonic>=1.3',
        'six>=1.10.0',
        'tree-format==0.1.1',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
