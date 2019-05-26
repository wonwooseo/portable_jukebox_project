"""
Django settings for portable_jukebox_project project.

Generated by 'django-admin startproject' using Django 2.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'g0(z*3k#vhv!js)#f!_*obxn3z0gx#r(=yhbr6kh^^u2$5j#9%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

ALLOWED_CIDR_NETS = ['192.168.0.1/8']


# Application definition

INSTALLED_APPS = [
    'channels',
    'jukebox.apps.JukeboxConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allow_cidr.middleware.AllowCIDRMiddleware'
]

ROOT_URLCONF = 'portable_jukebox_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'portable_jukebox_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

# Session related settings
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Channels settings
ASGI_APPLICATION = 'portable_jukebox_project.routing.application'

# For channel layers
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        }
    }
}

# Config for logger
LOGGER_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '[%(asctime)s][%(levelname)s] %(funcName)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        }
    },
    'loggers': {
        '': {
            'level': 'INFO',
            'handlers': ['console']
        }
    }
}

# Jukebox Settings
# Enter host machine's IP address here.
HOST_IP = '192.168.0.103'

# Key that host(admin) will use to access host-specific features.
HOST_PASSWORD = 'admin'

# Determines whether clients need password to access jukebox.
USE_PASSWORD = True

# Key that clients will use to access jukebox.
# If USE_PASSWORD is set to False, this is ignored.
# If PASSWORD is left empty, jukebox will not ask for passwords.
PASSWORD = '1234'

# Limit access to jukebox only to clients on same network.
# If set to False, jukebox will accept any clients.
ONLY_LOCAL = True

# Maximum length of music to be added from YouTube, in minutes.
# Jukebox will assume invalid value as 60(Default).
MAX_LENGTH = 60

# Maximum size of music file to be uploaded from client, in MB.
# Jukebox will assume invalid value as 20(Default).
MAX_FILESIZE = 20

# Minimum votes required to skip current music.
# Jukebox will assume invalid value as 1(Default).
MIN_SKIP_VOTE = 3

# Minimum votes required to re-add current music to playlist.
# Jukebox will assume invalid value as 1(Default).
MIN_READD_VOTE = 3
