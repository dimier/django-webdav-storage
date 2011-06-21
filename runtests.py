#!/usr/bin/env python
import sys
from os.path import dirname, abspath
from optparse import OptionParser
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test.db',
            },
        },
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'tests',
        ],
        ROOT_URLCONF='tests.urls',
        MEDIA_URL="/m/",
        DEBUG=False,
        SITE_ID=1,
    )

from django.test.simple import run_tests

def runtests(*test_args, **kwargs):
    if not test_args:
        test_args = ['tests']
    failures = run_tests(test_args, verbosity=kwargs.get('verbosity', 1), interactive=kwargs.get('interactive', False), failfast=kwargs.get('failfast'))
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--failfast', action='store_true', default=False, dest='failfast')

    (options, args) = parser.parse_args()

    runtests(failfast=options.failfast, *args)
