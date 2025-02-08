from channels.generic.websocket import AsyncWebsocketConsumer
from tethys_sdk.routing import consumer
import json


@consumer(name='dam_notification', url='dams/notifications/')
class NotificationsConsumer(AsyncWebsocketConsumer):

    async def authorized_connect(self):
        await self.channel_layer.group_add("notifications", self.channel_name)
        print(f"Added {self.channel_name} channel to notifications")

    async def authorized_disconnect(self, close_code):
        await self.channel_layer.group_discard("notifications", self.channel_name)
        print(f"Removed {self.channel_name} channel from notifications")

    async def dam_notifications(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))
        print(f"Got message {event} at {self.channel_name}")