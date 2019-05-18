from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from portable_jukebox_project import settings


def index(request):
    """
    Shows auth page. If USE_PASSWORD is set to False in settings.py, auth is
    skipped and client will see now playing page right away.
    :param request: request object from client
    :return: rendered html
    """
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
        return redirect('now_playing')

    password = request.POST['password']
    if password == settings.PASSWORD:
        request.session['validated'] = True
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
        request.session.flush()
        return redirect('index')
    return render(request, 'nowplaying.html')
