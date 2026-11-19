from django.contrib import admin
from django.urls import path, include
from APPserv.views import get_zms_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/zms-token/', get_zms_token),
    path('api/', include('APPserv.urls')),
]