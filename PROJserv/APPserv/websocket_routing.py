from channels.routing import URLRouter
from django.urls import path
from .consumer import OrderStatusConsumer

router = URLRouter([
    path('ws/orders/', OrderStatusConsumer.as_asgi()),
])