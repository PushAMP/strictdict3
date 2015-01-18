#!/usr/bin/env python

from setuptools import setup, find_packages

pkgs = find_packages()

setup(
    name='strictdict3',
    version='0.4.1',
    description='Strict Dict',
    author='Dmitry Zhiltsov',
    author_email='dzhiltsov@me.com',
    ext_modules=[],
    packages=pkgs,
    scripts=[],
    data_files=[],
    install_requires=[
        'msgpack-python',
    ],
    platforms='any',
    license='MIT',
    url='https://bitbucket.org/3f17/strictdict3',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
