from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json


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
        # Pass message to handler
        async_to_sync(self.channel_layer.group_send)(
            'skipadd',
            {
                'type': 'skipadd.event',
                'text': text_data,
            },
        )

    def skipadd_event(self, event):
        # Send message to channels in group
        self.send(text_data=event['text'])
