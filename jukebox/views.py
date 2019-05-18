from django.shortcuts import render
from django.http import HttpResponse
import configparser

config_dict = {}  # config options are constant, keep them on global dict


def read_config():
    parser = configparser.ConfigParser()
    parser.read('config.ini')
    # Set options from security section
    try:
        use_pw = parser.getboolean('SECURITY', 'USE_PASSWORD', fallback=True)
        config_dict['use_password'] = use_pw
    except ValueError:
        config_dict['use_password'] = True

    config_dict['password'] = parser.get('SECURITY', 'PASSWORD', fallback='')

    try:
        only_local = parser.getboolean('SECURITY', 'ONLY_LOCAL', fallback=True)
        config_dict['local'] = only_local
    except ValueError:
        config_dict['local'] = True
    # Set options from player section
    try:
        length = parser.getint('PLAYER', 'MAX_LENGTH', fallback=60)
        config_dict['max_length'] = length
    except ValueError:
        config_dict['max_length'] = 60

    try:
        size = parser.getint('PLAYER', 'MAX_FILESIZE', fallback=20)
        config_dict['max_size'] = size
    except ValueError:
        config_dict['max_size'] = 20

    try:
        skip = parser.getint('PLAYER', 'MIN_SKIP_VOTES', fallback=1)
        config_dict['min_skip'] = skip
    except ValueError:
        config_dict['max_length'] = 1

    try:
        readd = parser.getint('PLAYER', 'MIN_READD_VOTES', fallback=1)
        config_dict['min_readd'] = readd
    except ValueError:
        config_dict['min_readd'] = 1


def index(request):
    read_config()
    if not config_dict['use_password']:
        return render(request, 'nowplaying.html')
    return render(request, 'index.html')
