from .models import PlaylistItem
from portable_jukebox_project import settings
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

skip_counter = 0  # is this safe?
readd_counter = 0
np_idx = 0
playing = False


class SkipAddConsumer(WebsocketConsumer):
    def connect(self):
        # Add created channel to group
        async_to_sync(self.channel_layer.group_add)('skipadd',
                                                    self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        # Remove channel from group
        async_to_sync(self.channel_layer.group_discard)('skipadd',
                                                        self.channel_name)

    def receive(self, text_data):
        global skip_counter
        global readd_counter

        data_json = json.loads(text_data)
        if data_json.get('fetch'):  # new connection; send current counters
            if not playing:  # music not playing now
                async_to_sync(self.channel_layer.send)(
                    self.channel_name,
                    {
                        'type': 'skipadd.event',
                        'text': json.dumps({
                            'target': 'notplaying',
                        }),
                    }
                )
                return
            data_json['skip'] = skip_counter
            data_json['readd'] = readd_counter
            async_to_sync(self.channel_layer.send)(
                self.channel_name,
                {
                    'type': 'skipadd.event',
                    'text': json.dumps({
                        'target': 'fetch',
                        'skip': skip_counter,
                        'readd': readd_counter,
                        'idx': np_idx,  # for sync between consumer and client
                    }),
                }
            )
        else:
            if data_json.get('target') == 'skip' and \
                    data_json.get('idx') == np_idx:
                skip_counter += 1
                if skip_counter == settings.MIN_SKIP_VOTE:
                    ConsumerUtil.skip_handler()
                    return
                counter = skip_counter
            elif data_json.get('target') == 'readd' and \
                    data_json.get('idx') == np_idx:
                readd_counter += 1
                if readd_counter == settings.MIN_SKIP_VOTE:
                    # Copy and insert current item to playlist
                    np_item = PlaylistItem.objects.get(pk=np_idx)
                    np_item.pk = None  # will newly set id
                    np_item.save()
                    readd_counter = '✔'
                counter = readd_counter
            else:
                # Something wrong happened
                return
            async_to_sync(self.channel_layer.group_send)(
                'skipadd',
                {
                    'type': 'skipadd.event',
                    'text': json.dumps({
                        'target': data_json['target'],
                        'count': counter
                    }),
                },
            )

    def skipadd_event(self, event):
        # Send message to channels in group
        self.send(text_data=event['text'])


class MusicConsumer(WebsocketConsumer):
    def connect(self):
        # Add created channel to group
        async_to_sync(self.channel_layer.group_add)('music',
                                                    self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        # Remove channel from group
        async_to_sync(self.channel_layer.group_discard)('music',
                                                        self.channel_name)

    def receive(self, text_data):
        data_json = json.loads(text_data)
        if data_json.get('fetch'):  # new connection; send current music info
            if not playing:
                async_to_sync(self.channel_layer.send)(
                    self.channel_name,
                    {
                        'type': 'music.event',
                        'text': json.dumps({
                            'target': 'notplaying',
                        }),
                    }
                )
                return
            np_item = PlaylistItem.objects.get(pk=np_idx)
            if np_item.type == 'file':
                path = '/static/music_cache/{}'.format(np_item.link)
            else:
                path = np_item.link
            async_to_sync(self.channel_layer.send)(
                self.channel_name,
                {
                    'type': 'music.event',
                    'text': json.dumps({
                        'target': 'fetch',
                        'title': np_item.title,
                        'artist': np_item.artist,
                        'album': np_item.album,
                        'type': np_item.type,
                        'link': path,
                    }),
                }
            )
        else:
            if data_json.get('target') == 'skip':
                ConsumerUtil.skip_handler()
            else:
                # Something bad happened
                return

    def music_event(self, event):
        # Send message to channels in group
        self.send(text_data=event['text'])


class ConsumerUtil:
    @staticmethod
    def skip_handler():
        """
        Function to handle skip event. Marks current playlist item as not
        playing, next item as playing, then updates np_idx.
        :return: None
        """
        global skip_counter, readd_counter, playing
        skip_counter, readd_counter = 0, 0
        channel_layer = get_channel_layer()
        try:
            next_item = PlaylistItem.objects.get(pk=np_idx + 1)
            next_item.save()
        except PlaylistItem.DoesNotExist:  # playlist depleted
            playing = False
            async_to_sync(channel_layer.group_send)(
                'music',
                {
                    'type': 'music.event',
                    'text': json.dumps({
                        'target': 'skip',  # make client refresh
                    }),
                }
            )
            return
        ConsumerUtil.set_np_idx(np_idx + 1)
        async_to_sync(channel_layer.group_send)(
            'music',
            {
                'type': 'music.event',
                'text': json.dumps({
                    'target': 'skip',  # will make client refresh
                }),
            }
        )

    @staticmethod
    def get_np_idx():
        """
        Returns current value of np_idx.
        :return: np_idx: int
        """
        return np_idx

    @staticmethod
    def set_np_idx(new_idx):
        """
        Sets np_idx to given value.
        :param new_idx: new index
        :return: None
        """
        global np_idx
        global playing
        np_idx = new_idx
        playing = True

    @staticmethod
    def get_playing():
        """
        Returns current value of playing.
        :return: playing: boolean
        """
        return playing
