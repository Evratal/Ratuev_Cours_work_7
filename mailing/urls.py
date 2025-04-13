from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, MessageViewSet, MailingViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'mailings', MailingViewSet, basename='mailing')

urlpatterns = [
    path('', include(router.urls)),
]
