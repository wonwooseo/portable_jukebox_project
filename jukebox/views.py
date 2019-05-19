from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from portable_jukebox_project import settings
import requests
import logging.config

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '[%(asctime)s][%(levelname)s] %(funcName)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console']
        }
    }
})
logger = logging.getLogger(__name__)


def index(request):
    """
    Shows auth page. If USE_PASSWORD is set to False in settings.py, auth is
    skipped and client will see now playing page right away.
    :param request: request object from client
    :return: rendered html
    """
    valid_access = request.session.get('validated')
    if valid_access is not None:
        return redirect('now_playing')
    if not settings.USE_PASSWORD:
        return render(request, 'nowplaying.html')
    return render(request, 'index.html')


def check_password(request):
    """
    Checks if session key entered by client is right.
    Key is temporary and only used for access control, so no need for hashing,
    at least for now.
    :param request: request object from client
    :return: calls now_playing if match, index if mismatch
    """
    if settings.PASSWORD == '':
        request.session['validated'] = True
        logger.info('Session login from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        return redirect('now_playing')

    password = request.POST['password']
    if password == settings.PASSWORD:
        request.session['validated'] = True
        logger.info('Session login from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        return redirect('now_playing')
    else:
        messages.add_message(request, messages.INFO, 'Wrong Key!')
        return redirect('index')


def now_playing(request):
    """
    Shows now playing page to validated users.
    If client made illegal access to this page, redirect to index.
    :param request: request object from client
    :return: rendered html
    """
    valid_access = request.session.get('validated')
    if valid_access is None:
        logger.info('Unvalidated access from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        request.session.flush()
        return redirect('index')
    return render(request, 'nowplaying.html')


def qrcode(request):
    """
    Shows QR code to access jukebox easily.
    :param request: request object from client
    :return: rendered html
    """
    valid_access = request.session.get('validated')
    if valid_access is None:
        logger.info('Unvalidated access from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        request.session.flush()
        return redirect('index')
    context = {'address': settings.HOST_IP}  # add port in future?
    return render(request, 'qrcode.html', context)


def add(request):
    """
    Shows add music page. Client will choose to search YouTube or use local
    cache / upload file.
    :param request: request object from client
    :return: rendered html
    """
    valid_access = request.session.get('validated')
    if valid_access is None:
        logger.info('Unvalidated access from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        request.session.flush()
        return redirect('index')
    return render(request, 'add.html')


def add_youtube(request):
    """
    Shows add from youtube page.
    :param request: request object from client
    :return: rendered html
    """
    valid_access = request.session.get('validated')
    if valid_access is None:
        logger.info('Unvalidated access from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        request.session.flush()
        return redirect('index')
    return render(request, 'add_youtube.html')


def search_youtube(request):
    """
    Searches keyword submitted by client using YouTube Data API and returns
    result list. Tuples of video title, video id and thumbnail url are packed
    into a list and passed to template.
    :param request: request object from client
    :return: redirect to add_youtube, with result list
    """
    valid_access = request.session.get('validated')
    if valid_access is None:
        logger.info('Unvalidated access from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        request.session.flush()
        return redirect('index')

    # Calling YouTube Data API
    resultlist = []
    # TODO: Should read api key from untracked file when repo goes public
    api_key = 'AIzaSyB6J3gOdKJ4ZUefoABbHitfzWFzvcLUm3s'
    api_url = 'https://www.googleapis.com/youtube/v3/' \
              'search?part=snippet&type=video&videoEmbeddable=true&'
    max_results = 10
    keyword = request.POST['keyword']  # Never null; validated at form
    api_url += 'maxResults={}&q={}&key={}'.format(max_results, keyword, api_key)
    response = requests.get(api_url)  # API call
    logger.info('YouTube API Call (Status={})'.format(response.status_code))
    res_json = response.json()
    for item in res_json['items']:
        vname = item['snippet']['title'][:80] + '...'
        vid = item['id']['videoId']
        thumb = item['snippet']['thumbnails']['default']['url']
        resultlist.append((vid, vname, thumb))
    return render(request, 'add_youtube.html', {'resultlist': resultlist})


def add_youtube_item(request):
    """
    Adds video specified by client to server playlist.
    :param request: request object from client
    :return: add_error.html on error, add_success on success
    """
    valid_access = request.session.get('validated')
    if valid_access is None:
        logger.info('Unvalidated access from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        request.session.flush()
        return redirect('index')

    vid = request.POST.get('id', None)
    if not vid:  # videoID is somehow missing
        logger.error('Missing videoID in request')
        return render(request, 'add_error.html')

    # TODO: add to playlist
    # TODO: check length limit (chain vIDs in 1 call at search_youtube?)
    logger.info('Adding music from youtube(id={}) to playlist'.format(vid))
    return render(request, 'add_success.html')
