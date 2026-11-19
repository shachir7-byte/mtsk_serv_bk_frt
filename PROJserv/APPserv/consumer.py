import json
from channels.generic.websocket import AsyncWebsocketConsumer


class OrderStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        payload = json.loads(text_data) if text_data else {}
        order_id = payload.get('order_id')
        status = payload.get('status')
        await self.send(text_data=json.dumps({
            'event': 'order_updated',
            'order_id': order_id,
            'status': status
        }))

    async def disconnect(self, close_code):
        pass