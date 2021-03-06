# -*- coding: utf-8 -*-

# Django settings for sanguo project.
import os
import arrow
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TMP_PATH = os.path.normpath(os.path.join(BASE_DIR, '../tmp'))
LOG_PATH = os.path.normpath(os.path.join(BASE_DIR, 'logs'))
# BATTLE_RECORD_PATH = os.path.normpath(os.path.join(BASE_DIR, 'battle_record'))

DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = '*'


DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
    #     'NAME': 'sanguo', # Or path to database file if using sqlite3.
    #     # The following settings are not used with sqlite3:
    #     'USER': 'root',
    #     'PASSWORD': 'root',
    #     'HOST': '127.0.0.1', # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
    #     'PORT': '3306', # Set to empty string for default.
    #     'CONN_MAX_AGE': 120,
    # }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
# ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
# TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
# Put strings here, like "/home/html/static" or "C:/www/django/static".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n9&fzaggb0d+ff+7!f@h9jlu%!0ybkrou2ut=#w!22(z_y2tfc'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    # 'django.middleware.common.CommonMiddleware',
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'libs.middleware.ContentMD5',
    'sanguo.middleware.UnpackAndVerifyData',
    'sanguo.middleware.PackMessageData',
)

ROOT_URLCONF = 'sanguo.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'sanguo.wsgi.application'

TEMPLATE_DIRS = (
# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    # 'django.contrib.auth',
    # 'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django.contrib.sites',
    # 'django.contrib.messages',
    # 'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'helpers',
)


# TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
# NOSE_ARGS = ['--stop',]

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'simple': {
            'format': '%(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },

        'sanguo': {
            'handlers': ['console',],
            'level': 'DEBUG'
        }
    }
}

DATETIME_FORMAT = "Y-m-d H:i:s"


# project settings
import xml.etree.ElementTree as et
tree = et.ElementTree(file=os.path.join(BASE_DIR, "config.xml"))
doc = tree.getroot()

TIME_ZONE = doc.find('timezone').text

ENABLE_BATTLE_LOG = doc.find('battle/log').text == "true"
ENABLE_TEST_MODE = doc.find('testmode').text == "true"

EMAIL_NAME = doc.find('email/name').text

REDIS_HOST = doc.find('redis/host').text
REDIS_PORT = int( doc.find('redis/port').text )


MONGODB_HOST = doc.find('mongodb/host').text
MONGODB_PORT = int( doc.find('mongodb/port').text )
MONGODB_DB = doc.find('mongodb/db').text

CRYPTO_KEY = doc.find('crypto/key').text

HUB_HOST = doc.find('hub/host').text
HUB_HTTPS_PORT = int( doc.find('hub/port/https').text )


SERVER_ID = int( doc.find('server/id').text )
SERVER_NAME = doc.find('server/name').text
SERVER_IP = doc.find('server/ip').text
LISTEN_PORT_HTTP = int( doc.find('server/port/http').text )
LISTEN_PORT_HTTPS = int( doc.find('server/port/https').text )
SERVER_OPEN_DATE = arrow.get( doc.find('server/open').text ).replace(tzinfo=TIME_ZONE)
SERVER_TEST = doc.find('server/test').text == 'true'

MAILGUN_ACCESS_KEY = doc.find('mailgun/key').text
MAILGUN_SERVER_NAME = doc.find('mailgun/domain').text

_CONFIG_ADMINS = doc.find('admins')
ADMINS = ()
for _admin in _CONFIG_ADMINS.getchildren():
    attrib = _admin.attrib
    ADMINS += ((attrib['name'], attrib['email']),)

MANAGERS = ADMINS

del _CONFIG_ADMINS
del et
del doc
del tree

SERVER_EMAIL = '{0}.{1} <{0}.{1}@sanguo.com>'.format(EMAIL_NAME, SERVER_ID)
EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
