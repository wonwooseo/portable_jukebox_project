from django.apps import AppConfig
from portable_jukebox_project import settings
import pyqrcode


class JukeboxConfig(AppConfig):
    name = 'jukebox'

    def ready(self):
        # Creates QR code png on startup,
        # based on address specified in settings.py
        url = 'http://' + settings.HOST_IP + ':8000'
        qr_object = pyqrcode.create(url)
        qr_object.png('jukebox/static/qr.png', scale=12)

        # TODO: database reset (if not using in-memory db)
