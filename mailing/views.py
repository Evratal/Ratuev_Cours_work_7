from rest_framework import viewsets, permissions
from .models import Client, Message, Mailing
from .serializers import ClientSerializer, MessageSerializer, MailingSerializer
from .permissions import IsOwnerOrReadOnly
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from .models import User

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MailingViewSet(viewsets.ModelViewSet):
    serializer_class = MailingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


def home(request):
    context = {
        'total_mailings': Mailing.objects.count(),
        'active_mailings': Mailing.objects.filter(status='started').count(),  # или 'Запущена' в зависимости от выбора
        'unique_clients': Client.objects.distinct().count()
    }
    return render(request, 'mailing/home.html', context)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'mailing/register.html', {'form': form})

def profile(request):
    return render(request, 'mailing/profile.html', {'user': request.user})

def edit_profile(request):
    if request.method == 'POST':
        # Логика обновления профиля
        pass
    return render(request, 'mailing/edit_profile.html')