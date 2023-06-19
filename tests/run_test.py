#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import importlib
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))


def show_executable_test_files():
    print 'List of Test Case'
    print '================='
    files = [f for f in os.listdir('tests') if f.endswith('.py') and f != '__init__.py']
    for f in files:
        print f.replace('.py', '')


def check_execute_dir():
    current_path = os.getcwd()
    current_dir = current_path.split('/')[-1]
    if current_dir == 'tests':
        print 'please run `python tests/run_test.py` at root directory...'
        sys.exit(1)


if __name__ == '__main__':
    # confirm the directory to execute this file.
    check_execute_dir()

    parser = argparse.ArgumentParser(description="The script to run all or the specific test cases.")
    parser.add_argument('--list',  '-l', action='store_true', default=False, help='show the list of test file.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--all', action='store_true', help='All the test cases will be run if this flag is used.')
    group.add_argument('--case', '-c', nargs='+',
                       help='Please provide the test case file name (without `.py`) you want to run.')
    args = parser.parse_args()

    if args.list:
        show_executable_test_files()
        sys.exit(0)

    if args.all or (not args.all and not args.case):
        print 'run all test cases.'
        suite = unittest.TestLoader().discover(os.path.abspath(os.path.dirname(__file__)), '*_test.py')
        result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite).wasSuccessful()
    else:
        print 'run cases: {}'.format(', '.join(args.case))
        loader = unittest.TestLoader()
        loaded_suites = []
        for c in args.case:
            suite = loader.loadTestsFromModule(importlib.import_module(c))
            loaded_suites.append(suite)
        suites = unittest.TestSuite(loaded_suites)
        result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suites).wasSuccessful()

    if result:
        sys.exit(0)
    else:
        sys.exit(1)

