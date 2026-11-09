from django.contrib import admin
from django.urls import path, include
from APPserv.views import sandbox_page

urlpatterns = [
    path('', sandbox_page),
    path('admin/', admin.site.urls),
    path('api/', include('APPserv.urls')),
]