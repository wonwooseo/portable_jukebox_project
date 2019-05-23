from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json

skip_counter = 0  # is this safe?
readd_counter = 0


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
            data_json['skip'] = skip_counter
            data_json['readd'] = readd_counter
            async_to_sync(self.channel_layer.send)(
                self.channel_name,
                {
                    'type': 'skipadd.event',
                    'text': json.dumps({
                        'target': 'fetch',
                        'skip': skip_counter,
                        'readd': readd_counter
                    }),
                }
            )
        else:  # Pass message to handler
            if data_json['target'] == 'skip':
                skip_counter += 1
                counter = skip_counter
            elif data_json['target'] == 'readd':
                readd_counter += 1
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
