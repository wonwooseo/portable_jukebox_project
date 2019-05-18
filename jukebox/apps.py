from django.apps import AppConfig


class JukeboxConfig(AppConfig):
    name = 'jukebox'

    def ready(self):
        import pyqrcode

        
        pass
