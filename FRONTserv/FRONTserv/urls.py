from django.urls import path, re_path
from APPfront.views import index_view, api_gateway_proxy

urlpatterns = [
    path('', index_view),
    re_path(r'^api/(?P<subpath>.*)$', api_gateway_proxy),
]