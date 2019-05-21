from django.apps import AppConfig
from portable_jukebox_project import settings
import logging.config

logging.config.dictConfig(settings.LOGGER_CONFIG)
logger = logging.getLogger(__name__)


class JukeboxConfig(AppConfig):
    name = 'jukebox'

    def ready(self):
        import pyqrcode
        # Creates QR code png on startup,
        # based on address specified in settings.py
        url = 'http://' + settings.HOST_IP + ':8000'
        qr_object = pyqrcode.create(url)
        qr_object.png('jukebox/static/qr.png', scale=12)
        logger.info("Created QR Code image")

        # database reset (if not using in-memory db)
        from django.db import connection
        with connection.cursor() as c:
            # clear playlist table
            sql = "DELETE FROM jukebox_playlistitem"
            c.execute(sql)
            # clear music cache map table
            sql = "DELETE FROM jukebox_musiccacheitem"
            c.execute(sql)
            # resetting auto_increment
            sql = "DELETE FROM sqlite_sequence " \
                  "WHERE name = 'jukebox_playlistitem' " \
                  "OR name = 'jukebox_musiccacheitem';"
            c.execute(sql)
            logger.info("Playlist db reset finished")

        # Map files in music_cache to database
        import os
        import mutagen
        import stagger.id3
        from jukebox.models import MusicCacheItem
        # Get list of music files in cache
        try:
            filelist = os.listdir('music_cache')
        except FileNotFoundError:
            logger.error("Failed to find music_cache directory")
            os.mkdir('music_cache')
            logger.info("Created music_cache in project root")
            return
        # save title, artist, album, length, filename to db
        bulk_obj_list = []
        for file in filelist:
            # open music file
            music_fd = mutagen.File('music_cache/{}'.format(file))
            if music_fd is None:  # Invalid file type
                continue
            # length info is given in seconds
            len_div = divmod(music_fd.info.length, 60)
            length = '{}m {}s'.format(int(len_div[0]), int(len_div[1]))
            # Read tag information
            tag = stagger.read_tag('music_cache/{}'.format(file))
            title = tag.title
            if title == '':
                title = file
            if len(title) > 80:
                title = title[:77] + '...'
            artist = tag.artist
            album = tag.album
            item = MusicCacheItem(title=title, artist=artist, album=album,
                                  length=length, filename=file)
            bulk_obj_list.append(item)
        MusicCacheItem.objects.bulk_create(bulk_obj_list)
