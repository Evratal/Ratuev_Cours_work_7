from django.urls import path
from . import views
from mailing.views import RegisterView
from django.contrib.auth import views as auth_views


app_name = 'mailing'

urlpatterns = [
    path('', views.home, name='home'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(
        template_name='mailing/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Профиль
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Рассылки
    path('mailings/', views.MailingListView.as_view(), name='mailing_list'),
    path('mailings/create/', views.MailingCreateView.as_view(), name='mailing_create'),
    path('mailings/<int:pk>/edit/', views.MailingUpdateView.as_view(), name='mailing_edit'),
    path('mailings/<int:pk>/delete/', views.MailingDeleteView.as_view(), name='mailing_delete'),
    path('mailings/<int:pk>/send/', views.send_mailing, name='mailing_send'),
    path('mailings/<int:pk>/', views.MailingDetailView.as_view(), name='mailing_detail'),

    # Клиенты
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),

    # Сообщения
    path('messages/', views.MessageListView.as_view(), name='message_list'),
    path('messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('messages/<int:pk>/edit/', views.MessageUpdateView.as_view(), name='message_edit'),
    path('messages/<int:pk>/delete/', views.MessageDeleteView.as_view(), name='message_delete'),

    # Попытки рассылок
    path('attempts/', views.AttemptListView.as_view(), name='attempt_list'),

    # Регистрация
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='mailing/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
