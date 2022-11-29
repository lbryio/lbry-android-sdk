#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
On device unit test app
=======================

This is a dynamic test app, which means that depending on the requirements
supplied at build time, will perform some tests or others. Also, this app will
have an ui, or not, depending on requirements as well.

For now, we contemplate three possibilities:
  -  A kivy unittest app (sdl2 bootstrap)
  -  A unittest app (webview bootstrap)
  -  A non-gui unittests app

If you install/build this app via the `setup.py` file, a file named
`app_requirements.txt` will be generated which will contain the requirements
that we passed to the `setup.py` via arguments, which will determine
the unittests that this app will run.

.. note:: This app is made to be working on desktop and on an android device.
          Be aware that some of the functionality of this app will only work on
          an android device.

.. tip:: you can write more unit tests at `tests/test_requirements.py` and test
         these on desktop just by editing the file `app_requirements.txt`,
         which should be located at the same location than this file. This
         `app_requirements.txt` file, it's autogenerated when the
         `setup.py` is ran, so in certain circumstances, you may need
         to create it. Also be aware that each `python-for-android` recipe
         that you want to test should be in a new line, taking into account the
         case of the recipe.

.. warning:: If you use buildozer you only will get the basic `kivy unittest
             app`, with a basic set of tests: sqlite3, libffi, openssl and
             pyjnius.
"""

import sys
import unittest

from os import curdir
from os.path import isfile, realpath

print('Imported unittest')

sys.path.append('./')

# read `app_requirements.txt` and find out which tests to perform
tests_to_perform = {}
requirements = None
if isfile('app_requirements.txt'):
    with open('app_requirements.txt', 'r') as requirements_file:
        requirements = set(requirements_file.read().splitlines())
if not requirements:
    # we will test a basic set of recipes
    requirements = {'sqlite3', 'libffi', 'openssl', 'pyjnius'}
print('App requirements are: ', requirements)

for recipe in requirements:
    test_name = 'tests.test_requirements.{recipe}TestCase'.format(
        recipe=recipe.capitalize()
    )
    try:
        exist_test = unittest.TestLoader().loadTestsFromName(test_name)
    except AttributeError:
        # python2 case
        pass
    else:
        if '_exception' not in exist_test._tests[0].__dict__:
            print('Adding Testcase: ', test_name)
            tests_to_perform[recipe] = test_name
print('Tests to perform are: ', tests_to_perform)

# Find out which app we want to run
if 'kivy' in requirements:
    from app_kivy import TestKivyApp

    test_app = TestKivyApp()
    test_app.tests_to_perform = tests_to_perform
    test_app.run()
elif 'flask' in requirements:
    import app_flask
    app_flask.TESTS_TO_PERFORM = tests_to_perform

    print('Current directory is ', realpath(curdir))
    flask_debug = not realpath(curdir).startswith('/data')

    # Flask is run non-threaded since it tries to resolve app classes
    # through pyjnius from request handlers. That doesn't work since the
    # JNI ends up using the Java system class loader in new native
    # threads.
    #
    # https://github.com/kivy/python-for-android/issues/2533
    app_flask.app.run(threaded=False, debug=flask_debug)
else:
    # we don't have kivy or flask in our
    # requirements, so we run unittests in terminal
    suite = unittest.TestLoader().loadTestsFromNames(list(tests_to_perform.values()))
    unittest.TextTestRunner().run(suite)
