from django.apps import AppConfig
from portable_jukebox_project import settings
import logging.config

logging.config.dictConfig(settings.LOGGER_CONFIG)
logger = logging.getLogger(__name__)


class JukeboxConfig(AppConfig):
    name = 'jukebox'

    def ready(self):
        self.read_config()
        self.create_qrqode()
        if not settings.TESTING:
            self.reset_db()
            self.cache_init()

    @staticmethod
    def read_config():
        """
        Reads config file and sets variables in settings.py accordingly.
        Creates new config from template if .config doesn't exist.
        :return: None
        """
        from configparser import ConfigParser
        import os
        from shutil import copyfile
        if not os.path.isfile('.config'):
            copyfile('.config_default', '.config')
            logger.info('Created config file using defaults')
            return
        p = ConfigParser()
        p.read('.config')
        # if config has missing section/options, default will be used
        settings.HOST_IP = p.get('SERVER', 'HOST_IP',
                                 fallback=settings.HOST_IP)
        settings.HOST_PASSWORD = p.get('SERVER', 'HOST_PASSWORD',
                                       fallback=settings.HOST_PASSWORD)
        settings.USE_PASSWORD = p.get('SERVER', 'USE_PASSWORD',
                                      fallback=settings.USE_PASSWORD)
        settings.PASSWORD = p.get('SERVER', 'PASSWORD',
                                  fallback=settings.PASSWORD)
        settings.ONLY_LOCAL = p.get('SERVER', 'ONLY_LOCAL',
                                    fallback=settings.ONLY_LOCAL)
        settings.API_KEY = p.get('SERVER', 'API_KEY',
                                 fallback=settings.API_KEY)
        settings.MAX_LENGTH = p.getint('PLAYER', 'MAX_LENGTH',
                                       fallback=settings.MAX_LENGTH)
        settings.MAX_FILESIZE = p.getint('PLAYER', 'MAX_FILESIZE',
                                         fallback=settings.MAX_FILESIZE)
        settings.MIN_SKIP_VOTE = p.getint('PLAYER', 'MIN_SKIP_VOTE',
                                          fallback=settings.MIN_SKIP_VOTE)
        settings.MIN_READD_VOTE = p.getint('PLAYER', 'MIN_READD_VOTE',
                                           fallback=settings.MIN_READD_VOTE)

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
        import io
        import mutagen
        import stagger.id3
        from PIL import Image
        from jukebox.models import MusicCacheItem
        # Get list of music files in cache
        filelist, coverlist = [], []
        try:
            filelist = os.listdir('jukebox/static/music_cache')
        except FileNotFoundError:
            logger.error("Failed to find music_cache directory")
            os.mkdir('jukebox/static/music_cache')
            logger.info("Created music_cache in jukebox/static")
            return
        try:
            coverlist = os.listdir('jukebox/static/img/cover_cache')
        except FileNotFoundError:
            logger.error("Failed to find img/cover_cache directory")
            os.mkdir('jukebox/static/img/cover_cache')
            logger.info("Created img/cover_cache in jukebox/static")
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
                # extract album cover img
                if '{}.png'.format(title) not in coverlist:
                    cover_bytes = None
                    ptag = tag.get(stagger.id3.PIC)
                    if ptag:
                        cover_bytes = ptag[0].data
                    aptag = tag.get(stagger.id3.APIC)
                    if aptag:
                        cover_bytes = aptag[0].data
                    if cover_bytes:  # cover image exists in tag
                        img = Image.open(io.BytesIO(cover_bytes))
                        img.save('jukebox/static/img/cover_cache/{}.png'
                                 .format(title), 'PNG')
                        img.close()
            except stagger.NoTagError:
                title = file
                artist, album = '<>', '<>'
            item = MusicCacheItem(title=title, artist=artist, album=album,
                                  length=length, filename=file)
            bulk_obj_list.append(item)
        MusicCacheItem.objects.bulk_create(bulk_obj_list)
        logger.info('Cache initialization finished')
