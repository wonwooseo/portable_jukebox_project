from django.apps import AppConfig
from portable_jukebox_project import settings
import logging.config

logging.config.dictConfig(settings.LOGGER_CONFIG)
logger = logging.getLogger(__name__)


class JukeboxConfig(AppConfig):
    name = 'jukebox'

    def ready(self):
        self.create_qrqode()
        self.reset_db()
        self.cache_init()

    @staticmethod
    def create_qrqode():
        """
        Creates QR code png on startup based on address specified in settings.py
        :return: None
        """
        import pyqrcode
        url = 'http://' + settings.HOST_IP + ':8000'
        qr_object = pyqrcode.create(url)
        qr_object.png('jukebox/static/img/qr.png', scale=12)
        logger.info("Created QR Code image")

    @staticmethod
    def reset_db():
        """
        Resets database tables with raw queries
        :return: None
        """
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

    @staticmethod
    def cache_init():
        """
        Map files in music_cache to database
        :return: None
        """
        import os
        import mutagen
        import stagger.id3
        from jukebox.models import MusicCacheItem
        # Get list of music files in cache
        try:
            filelist = os.listdir('jukebox/static/music_cache')
        except FileNotFoundError:
            logger.error("Failed to find music_cache directory")
            os.mkdir('jukebox/static/music_cache')
            logger.info("Created music_cache in jukebox/static")
            return
        # save title, artist, album, length, filename to db
        bulk_obj_list = []
        for file in filelist:
            # open music file
            try:
                music_fd = mutagen.File('jukebox/static/music_cache/{}'
                                        .format(file))
            except mutagen.MutagenError:
                logger.error('Corrupted file in cache({})'.format(file))
                os.remove('jukebox/static/music_cache/{}'.format(file))
                continue
            if music_fd is None:  # Invalid file type
                # TODO: remove gitignore check on production!
                if file == '.gitignore':
                    continue
                logger.error('Unsupported file in cache({})'.format(file))
                os.remove('jukebox/static/music_cache/{}'.format(file))
                continue
            if 'mp3' not in music_fd.mime[0]:  # not mp3 file
                logger.error('Unsupported file in cache({})'.format(file))
                os.remove('jukebox/static/music_cache/{}'.format(file))
                continue
            if music_fd.info.sketchy:  # file might not be valid mpeg audio
                logger.error('Corrupted file in cache({})'.format(file))
                os.remove('jukebox/static/music_cache/{}'.format(file))
                continue
            # length info is given in seconds
            len_div = divmod(music_fd.info.length, 60)
            length = '{}m {}s'.format(int(len_div[0]), int(len_div[1]))
            # Read tag information
            try:
                tag = stagger.read_tag('jukebox/static/music_cache/{}'
                                       .format(file))
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
            except stagger.NoTagError:
                title = file
                artist, album = '<>', '<>'
            item = MusicCacheItem(title=title, artist=artist, album=album,
                                  length=length, filename=file)
            bulk_obj_list.append(item)
        MusicCacheItem.objects.bulk_create(bulk_obj_list)
        logger.info('Cache initialization finished')
