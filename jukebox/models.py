from django.db import models


class PlaylistItem(models.Model):
    """
    Model class to represent playlist and its entries.
    """
    title = models.CharField(max_length=80)
    album = models.CharField(max_length=80)  # for file only
    artist = models.CharField(max_length=80)  # for file only
    type = models.CharField(max_length=10)  # youtube or file
    link = models.TextField()  # videoID or filename
