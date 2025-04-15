# myproject/urls.py (ПРАВИЛЬНО)
from django.contrib import admin
from django.urls import path, include
from mailing.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('mailing/', include('mailing.urls')),
    path('', home, name='home'),
]

