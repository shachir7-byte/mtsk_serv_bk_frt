import os
from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from APPserv.websocket_routing import router

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROJserv.settings')
django_app = ASGIStaticFilesHandler(get_asgi_application())

application = ProtocolTypeRouter({
    'http': django_app,
    'websocket': router,
})