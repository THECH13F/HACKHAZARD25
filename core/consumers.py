import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

logger = logging.getLogger('rt_cta')

class ThreatNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        # Anonymous users cannot connect
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Each user gets their own group
        self.group_name = f"user_{self.user.id}_notifications"
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket connected for user {self.user.id}")
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for user {self.user.id}")

    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        Currently only used for ping/pong to keep the connection alive.
        """
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', '')
        
        if message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': text_data_json.get('timestamp', '')
            }))

    async def threat_notification(self, event):
        """
        Receive threat notification from group and send to WebSocket.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'threat_notification',
            'data': event['data']
        }))

    async def analysis_update(self, event):
        """
        Receive analysis status update from group and send to WebSocket.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'analysis_update',
            'data': event['data']
        }))

    @classmethod
    async def notify_user(cls, user_id, notification_type, data):
        """
        Utility method to send a notification to a specific user.
        
        Args:
            user_id (int): The ID of the user to notify
            notification_type (str): The type of notification (threat_notification or analysis_update)
            data (dict): The data to send
        """
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        
        await channel_layer.group_send(
            f"user_{user_id}_notifications",
            {
                'type': notification_type,
                'data': data
            }
        ) 