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
            # resetting auto_increment
            sql = "DELETE FROM sqlite_sequence " \
                  "WHERE name = 'jukebox_playlistitem';"
            c.execute(sql)
            logger.info("Playlist db reset finished")
