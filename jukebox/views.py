from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from portable_jukebox_project import settings
from jukebox.models import *
from jukebox.consumers import ConsumerUtil
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from PIL import Image
import io
import logging.config
import os
import mutagen
import stagger.id3
import requests
import json

logging.config.dictConfig(settings.LOGGER_CONFIG)
logger = logging.getLogger(__name__)


def index(request):
    """
    Shows auth page. If USE_PASSWORD is set to False in settings.py, auth is
    skipped and client will see now playing page right away.
    :param request: request object from client
    :return: rendered html
    """
    # Access from host machine
    if request.META.get('REMOTE_ADDR') == '127.0.0.1':  # is this safe?
        return render(request, 'host_player.html',
                      {'address': settings.HOST_IP,
                       'skip_threshold': settings.MIN_SKIP_VOTE,
                       'readd_threshold': settings.MIN_READD_VOTE})
    # Access from other machines
    valid_access = request.session.get('validated')
    if valid_access is not None:
        logger.info('Session login from {}'.
                    format(request.META.get('REMOTE_ADDR')))
        return redirect('now_playing')
    if not settings.USE_PASSWORD or settings.PASSWORD == '':
        request.session['validated'] = True
        logger.info('Session login from {}'.
                    format(request.META.get('REMOTE_ADDR')))
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
    if not check_validated_access(request, 'now_playing'):
        request.session.flush()
        return redirect('index')
    return render(request, 'nowplaying.html')


def qrcode(request):
    """
    Shows QR code to access jukebox easily.
    :param request: request object from client
    :return: rendered html
    """
    if not check_validated_access(request, 'qrcode'):
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
    if not check_validated_access(request, 'add'):
        request.session.flush()
        return redirect('index')
    return render(request, 'add.html')


def add_youtube(request):
    """
    Shows add from youtube page.
    :param request: request object from client
    :return: rendered html
    """
    if not check_validated_access(request, 'add_youtube'):
        request.session.flush()
        return redirect('index')
    if settings.API_KEY == '':
        logger.warning('YouTube API Key is not provided')
        message = 'API key is not provided.'
        return render(request, 'add_error.html', {'message': message})
    return render(request, 'add_youtube.html')


def search_youtube(request):
    """
    Searches keyword submitted by client using YouTube Data API and returns
    result list. Tuples of video title, video id and thumbnail url are packed
    into a list and passed to template.
    :param request: request object from client
    :return: redirect to add_youtube, with result list
    """
    if not check_validated_access(request, 'search_youtube'):
        request.session.flush()
        return redirect('index')

    # Calling YouTube Data API
    resultlist = []
    api_key = settings.API_KEY
    api_url = 'https://www.googleapis.com/youtube/v3/' \
              'search?part=snippet&type=video&videoEmbeddable=true&'
    max_results = 10
    keyword = request.POST['keyword']  # Never null; validated at form
    api_url += 'maxResults={}&q={}&key={}'.format(max_results, keyword, api_key)
    response = requests.get(api_url)  # API call
    if response.status_code == 400:
        logger.error('Failed to call YouTube API with provided API key')
        message = 'YouTube API call failed using provided key.'
        return render(request, 'add_error.html', {'message': message})
    logger.info('YouTube API Call (Status={})'.format(response.status_code))
    res_json = response.json()
    for item in res_json['items']:
        vname = item['snippet']['title']
        if len(vname) > 80:
            vname = vname[:77] + '...'
        vid = item['id']['videoId']
        thumb = item['snippet']['thumbnails']['default']['url']
        resultlist.append((vid, vname, thumb))
    # TODO: check length limit (chain vIDs in 1 call at search_youtube?)
    return render(request, 'add_youtube.html', {'resultlist': resultlist})


def add_youtube_item(request):
    """
    Adds video specified by client to server playlist.
    :param request: request object from client
    :return: add_error.html on error, add_success on success
    """
    if not check_validated_access(request, 'add_youtube_item'):
        request.session.flush()
        return redirect('index')

    vid = request.POST.get('id', None)
    title = request.POST.get('title', None)
    if not vid or not title:  # videoID is somehow missing
        logger.error('Missing videoID/title in request')
        return render(request, 'add_error.html')

    # add to playlist
    item = PlaylistItem(type='youtube', title=title, link=vid)
    if not PlaylistItem.objects.filter(playing=True).exists():
        item.playing = True
        item.save()
        # signal /nowplaying that playlist has been updated
        ConsumerUtil.set_np_idx(item.pk)
        channel = get_channel_layer()
        async_to_sync(channel.group_send)('music', {
                        'type': 'music.event',
                        'text': json.dumps({
                            'target': 'skip',  # will make client refresh
                        }),
                    })
    else:
        item.save()
    logger.info('Adding music from youtube(id={}) to playlist'.format(vid))
    return render(request, 'add_success.html')


def add_file(request):
    """
    Shows add from cache / upload page.
    Passes list of music files in music cache.
    :param request: request object from client
    :return: add_file.html, with list of files in music cache
    """
    if not check_validated_access(request, 'add_file'):
        request.session.flush()
        return redirect('index')

    resultlist = []
    # Get list of files in cache
    files_set = MusicCacheItem.objects.all()
    # pass list of (id, title, artist, length) to template
    for file in files_set:
        packed_tag = (file.id, file.title, file.artist, file.length)
        resultlist.append(packed_tag)
    return render(request, 'add_file.html', {'resultlist': resultlist})


def add_file_item(request):
    """
    Adds chosen / uploaded file to playlist.
    :param request: request from client
    :return: add_success: added successfully
             upload_error: error while handling uploaded file
             add_error: Missing parts in request
    """
    if not check_validated_access(request, 'add_file_item'):
        request.session.flush()
        return redirect('index')

    request_type = request.POST.get('reqtype')
    if request_type == 'add':  # adding from cache
        fid = request.POST.get('fileid')
        # Find file with given id in DB
        music = MusicCacheItem.objects.get(id=fid)
        # Add to playlist
        item = PlaylistItem(type='file', title=music.title, artist=music.artist,
                            album=music.album, link=music.filename)
        if not PlaylistItem.objects.filter(playing=True).exists():
            item.playing = True
            item.save()
            # Signal /nowplaying playlist has been updated
            ConsumerUtil.set_np_idx(item.pk)
            channel = get_channel_layer()
            async_to_sync(channel.group_send)('music', {
                'type': 'music.event',
                'text': json.dumps({
                    'target': 'skip',  # will make client refresh
                }),
            })
        else:
            item.save()
        logger.info('Adding music from cache(file={}) '
                    'to playlist'.format(music.filename))

    elif request_type == 'upload':  # uploading to cache
        # Get file POSTed from request object
        file = request.FILES.get('musicfile')
        # Check duplicate filename
        if MusicCacheItem.objects.filter(filename=file.name).exists():
            logger.error('UPLOAD: Duplicate file (file={})'.format(file.name))
            message = 'File with same name already exists in the cache :('
            return render(request, 'upload_error.html', {'message': message})
        # Write to music_cache first
        with open('jukebox/static/music_cache/{}'.format(file.name),
                  'wb') as fd:
            if file.multiple_chunks():  # big files
                for chunk in file.chunks():
                    fd.write(chunk)
            else:  # smaller files
                fd.write(file.read())
        # Check if file is valid
        try:
            music_fd = mutagen.File('jukebox/static/music_cache/{}'
                                    .format(file.name))
        except mutagen.MutagenError:  # Corrupted file
            logger.error('UPLOAD: Corrupted file (file={})'.format(file.name))
            os.remove('jukebox/static/music_cache/{}'.format(file.name))
            message = 'Looks like your file is corrupted :('
            return render(request, 'upload_error.html', {'message': message})
        # Invalid file type
        if music_fd is None or 'mp3' not in music_fd.mime[0]:
            logger.error('UPLOAD: Unsupported file (file={})'.format(file.name))
            os.remove('jukebox/static/music_cache/{}'.format(file.name))
            message = 'Looks like jukebox does not support this file :('
            return render(request, 'upload_error.html', {'message': message})
        # file might not be valid mpeg audio
        if music_fd.info.sketchy:
            logger.error('UPLOAD: Corrupted file (file={})'.format(file.name))
            os.remove('jukebox/static/music_cache/{}'.format(file.name))
            message = 'Looks like your file is corrupted :('
            return render(request, 'upload_error.html', {'message': message})
        # Get tag info and update cache map database
        len_div = divmod(music_fd.info.length, 60)  # length given in seconds
        length = '{}m {}s'.format(int(len_div[0]), int(len_div[1]))
        try:
            tag = stagger.read_tag('jukebox/static/music_cache/{}'
                                   .format(file.name))
            title = tag.title
            if title == '':
                title = file
            if len(title) > 80:
                title = title[:77] + '...'
            artist = tag.artist
            if artist == '':
                artist = '<>'
            album = tag.album
            if album == '':
                album = '<>'
            # extract album cover img
            cover_bytes = None
            ptag = tag.get(stagger.id3.PIC)
            if ptag:
                cover_bytes = ptag[0].data
            aptag = tag.get(stagger.id3.APIC)
            if aptag:
                cover_bytes = aptag[0].data
            if cover_bytes:
                img = Image.open(io.BytesIO(cover_bytes))
                img.save('jukebox/static/img/cover_cache/{}.png'
                         .format(title), 'PNG')
                img.close()
        except stagger.NoTagError:
            title = file.name
            artist, album = '<>', '<>'
        cache_item = MusicCacheItem(title=title, artist=artist, album=album,
                                    length=length, filename=file.name)
        cache_item.save()
        logger.info('Uploaded file added to cache (file={})'.format(file.name))
        # Add file to playlist
        plist_item = PlaylistItem(type='file', title=title, artist=artist,
                                  album=album, link=file.name)
        if not PlaylistItem.objects.filter(playing=True).exists():
            plist_item.playing = True
            plist_item.save()
            # Signal /nowplaying
            ConsumerUtil.set_np_idx(plist_item.pk)
            channel = get_channel_layer()
            async_to_sync(channel.group_send)('music', {
                'type': 'music.event',
                'text': json.dumps({
                    'target': 'skip',  # will make client refresh
                }),
            })
        else:
            plist_item.save()
        logger.info('Adding music from upload(file={}) '
                    'to playlist'.format(file.name))

    else:
        logger.error('Missing request type in request')
        return render(request, 'add_error.html')

    return render(request, 'add_success.html')


def check_validated_access(request, caller):
    """
    Extracted function to check if access is valid.
    :param request: request object from client, passed by caller
    :param caller: name of caller, in string
    :return: True if valid access, False if not
    """
    valid_access = request.session.get('validated')
    if valid_access is None:
        logger.info('Unvalidated access to {} from {}'.
                    format(caller, request.META.get('REMOTE_ADDR')))
        return False
    return True
