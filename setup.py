#!/usr/bin/env python
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


pkgs = find_packages()

setup(
    name='strictdict3',
    version='0.4.5',
    description='Strict Dict',
    author='Dmitry Zhiltsov',
    author_email='dzhiltsov@me.com',
    ext_modules=[],
    packages=pkgs,
    tests_require=['py==1.4.31', 'pytest==3.0.0'],
    cmdclass={'test': PyTest},
    scripts=[],
    data_files=[],
    install_requires=[
        'msgpack-python==0.4.8',
    ],
    test_suite="strictdict.tests",
    platforms='any',
    license='MIT',
    url='https://github.com/PushAMP/strictdict3',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
