#admin
from django.contrib import admin
from .models import Client, Message, Mailing, MailingAttempt, User
from django.contrib.auth.admin import UserAdmin


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'comment_short')
    search_fields = ('email', 'full_name')
    list_filter = ('owner',)

    def comment_short(self, obj):
        return obj.comment[:50] + '...' if obj.comment else ''


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at')
    list_filter = ('created_at',)  # Убрали 'owner', фильтруем по дате
    search_fields = ('subject', 'body')

    def body_short(self, obj):
        return obj.body[:100] + '...' if len(obj.body) > 100 else obj.body


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'start_time', 'end_time', 'owner')
    list_filter = ('status', 'owner')
    filter_horizontal = ('clients',)
    readonly_fields = ('status',)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ('mailing', 'status', 'attempt_time')
    list_filter = ('status', 'mailing__status')
    readonly_fields = ('attempt_time', 'status', 'server_response')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'phone', 'country')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('phone', 'country', 'avatar')}),
    )

#apps
from django.apps import AppConfig


class MailingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mailing'


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

#forms
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    SetPasswordForm,
    PasswordResetForm,
    AuthenticationForm
)
from .models import Mailing, Client, Message
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class MailingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['message'].queryset = Message.objects.filter(owner=user)
            self.fields['clients'].queryset = Client.objects.filter(owner=user)

    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'clients']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'message': forms.Select(attrs={'class': 'form-select'}),
            'clients': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com',
            'autocomplete': 'email'
        }),
        help_text=_("Обязательное поле. Проверьте правильность email.")
    )

    password1 = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Не менее 8 символов'
        }),
        help_text=_("Минимум 8 символов, не только цифры.")
    )

    password2 = forms.CharField(
        label=_("Подтверждение пароля"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    )

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Этот email уже зарегистрирован."))

        return email


class ClientForm(forms.ModelForm):
    # Форма клиента
    class Meta:
        model = Client
        fields = ['email', 'full_name', 'comment']


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите тему письма'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Введите текст письма'
            }),
        }


class UserEditForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX',
            'data-mask': '+7 (000) 000-00-00'
        })
    )

    country = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Страна проживания'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar', 'country']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'readonly': True  # Email нельзя менять после регистрации
            }),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].disabled = True  # Альтернатива readonly


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ваш email',
            'autofocus': True
        })
    )

    password = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )

    error_messages = {
        'invalid_login': _(
            "Неверный email или пароль. Учтите регистр символов."
        ),
        'inactive': _("Аккаунт неактивен. Подтвердите email."),
    }


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com'

        }),
        help_text=_("На этот email придёт ссылка для сброса пароля.")

    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Новый пароль'
        }),
        help_text=_("Минимум 8 символов, не только цифры.")
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    )
#models

from django.contrib.auth.base_user import BaseUserManager
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Корректное объявление поля email (без дублирования verbose_name)
    email = models.EmailField(
        ('email address'),  # Здесь уже установлен verbose_name
        unique=True,
        help_text=('Required. Must be a valid email address.')
    )

    username = models.CharField(
        ('username'),
        max_length=150,
        blank=True,
        null=True,
        unique=True,
        help_text=('Optional. 150 characters or fewer.')
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name=('Avatar')
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name=('Phone number')
    )

    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=('Country')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = ('User')
        verbose_name_plural = ('Users')

    def __str__(self):
        return self.email

    def get_backend(self):
        return 'django.contrib.auth.backends.ModelBackend'


class Client(models.Model):
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        help_text='Укажите email клиента'
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name='Ф.И.О.',
        help_text='Полное имя клиента'
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Комментарий',
        help_text='Дополнительная информация о клиенте'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='clients',
        verbose_name='Владелец'
    )

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['full_name']


class Message(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Владелец'
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='Тема письма',
        help_text='Максимальная длина 255 символов'  # Добавлено
    )
    body = models.TextField(
        verbose_name='Текст письма',
        help_text='Введите содержание письма'  # Добавлено
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-created_at']


class Mailing(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создана'),
        ('started', 'Запущена'),
        ('completed', 'Завершена'),
    ]

    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        verbose_name='Статус'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='mailings',
        verbose_name='Сообщение'
    )
    clients = models.ManyToManyField(
        Client,
        related_name='mailings',
        verbose_name='Клиенты'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mailings',
        verbose_name='Владелец'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    def __str__(self):
        return f"Рассылка #{self.id} ({self.get_status_display()})"

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_mailings", "Может просматривать все рассылки"),
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Время окончания должно быть позже времени начала")

        if self.status == 'started' and self.start_time > timezone.now():
            raise ValidationError("Нельзя запустить рассылку с будущей датой начала")

    def save(self, *args, **kwargs):
        self.full_clean()  # Автоматическая валидация при сохранении
        super().save(*args, **kwargs)

    def send_mailing(self):
        """
        Отправляет рассылку и создает запись о попытке
        """
        if self.status == 'completed':
            return False

        try:
            # Получаем список email клиентов
            recipients = [client.email for client in self.clients.all()]

            # Отправляем email
            send_mail(
                subject=self.message.subject,
                message=self.message.body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=recipients,
                fail_silently=False,
            )

            # Создаем запись об успешной попытке
            MailingAttempt.objects.create(
                mailing=self,
                status='success',
                server_response='OK'
            )

            # Обновляем статус рассылки
            if self.status != 'started':
                self.status = 'started'
                self.save()
            return True

        except Exception as e:
            # Создаем запись о неудачной попытке
            MailingAttempt.objects.create(
                mailing=self,
                status='failed',
                server_response=str(e)
            )
            return False

    def check_completion(self):
        """
        Проверяет, завершилась ли рассылка
        """
        if self.end_time <= timezone.now() and self.status != 'completed':
            self.status = 'completed'
            self.save()
            return True
        return False


class MailingAttempt(models.Model):
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('failed', 'Не успешно'),
    ]

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Рассылка'
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время попытки'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='Статус'
    )
    server_response = models.TextField(
        blank=True,
        null=True,
        verbose_name='Ответ сервера'
    )

    def __str__(self):
        return f"Попытка рассылки #{self.id} ({self.get_status_display()})"

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылки'
        ordering = ['-attempt_time']


def send_to_all(self):
    """
    Отправляет рассылку всем клиентам
    Возвращает словарь с результатами
    """
    if self.status == 'completed':
        return {'success': 0, 'failed': 0}

    results = {'success': 0, 'failed': 0}

    for client in self.clients.all():
        try:
            send_mail(
                subject=self.message.subject,
                message=self.message.body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[client.email],
                fail_silently=False
            )
            self.attempts.create(status='success', server_response='OK')
            results['success'] += 1
        except Exception as e:
            self.attempts.create(status='failed', server_response=str(e)[:255])
            results['failed'] += 1

    if self.end_time <= timezone.now():
        self.status = 'completed'
        self.save()

    return results


def start_mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)

    # Проверяем права доступа
    if mailing.owner != request.user:
        messages.error(request, "У вас нет прав для запуска этой рассылки")
        return redirect('mailing_list')

    # Проверяем, можно ли запускать рассылку
    if mailing.status == 'completed':
        messages.error(request, "Эта рассылка уже завершена")
    elif mailing.start_time > timezone.now():
        messages.error(request, "Время начала рассылки еще не наступило")
    else:
        if mailing.send_mailing():
            messages.success(request, "Рассылка успешно запущена")
        else:
            messages.error(request, "Ошибка при отправке рассылки")

    return redirect('mailing_detail', pk=pk)
#permissions

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Пермишен для проверки, что пользователь является владельцем объекта
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
#urls
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
    path('registration/register/', RegisterView.as_view(), name='register'),
    path('registration/login/', auth_views.LoginView.as_view(template_name='mailing/registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

#views
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, ListView, TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import IntegrityError
from myproject.settings import CACHE_TTL
from .models import Mailing, Client, Message, User, MailingAttempt
from .forms import MailingForm, ClientForm, MessageForm, UserEditForm
from django.views.generic import UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.contrib.auth import login
from .forms import RegisterForm


@cache_page(CACHE_TTL)
@login_required
def home(request):
    """Главная страница с общей статистикой"""
    if request.user.groups.filter(name='Менеджеры').exists():
        mailings = Mailing.objects.all()
        clients = Client.objects.all()
    else:
        mailings = Mailing.objects.filter(owner=request.user)
        clients = Client.objects.filter(owner=request.user)

    context = {
        'total_mailings': mailings.count(),
        'active_mailings': mailings.filter(status='started').count(),
        'unique_clients': clients.distinct().count()
    }
    return render(request, 'mailing/home.html', context)


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Создание новой рассылки"""
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def form_valid(self, form):
        try:
            form.instance.owner = self.request.user
            if form.instance.start_time <= timezone.now():
                form.instance.status = 'started'
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(None, 'Ошибка при создании рассылки')
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing/mailing_confirm_delete.html'

    success_url = reverse_lazy('mailing:mailing_list')


@method_decorator(cache_page(CACHE_TTL), name='dispatch')
class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = 'mailing/mailing/mailing_detail.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.groups.filter(name='Менеджеры').exists():

            queryset = queryset.filter(owner=self.request.user)
        return queryset


@method_decorator(cache_page(CACHE_TTL), name='dispatch')
class MailingListView(LoginRequiredMixin, ListView):
    """Список рассылок"""
    model = Mailing
    template_name = 'mailing/mailing/mailing_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.groups.filter(name='Менеджеры').exists():
            queryset = queryset.filter(owner=self.request.user)

        # Автоматическое обновление статусов
        now = timezone.now()
        for mailing in queryset:
            if mailing.start_time <= now <= mailing.end_time and mailing.status != 'started':
                mailing.status = 'started'
                mailing.save()
            elif now > mailing.end_time and mailing.status != 'completed':
                mailing.status = 'completed'

                mailing.save()

        return queryset


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        return kwargs


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Добавление нового клиента"""
    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('mailing:client_list')

    def form_valid(self, form):
        try:
            form.instance.owner = self.request.user
            return super().form_valid(form)
        except IntegrityError:
            form.add_error('email', 'Клиент с таким email уже существует')
            return self.form_invalid(form)


class ClientListView(LoginRequiredMixin, ListView):
    """Список клиентов"""
    model = Client
    template_name = 'mailing/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        cache_key = f'clients_{self.request.user.id}'  # Уникальный ключ для пользователя
        clients = cache.get(cache_key)

        if not clients:
            queryset = super().get_queryset()
            if not self.request.user.groups.filter(name='Менеджеры').exists():
                queryset = queryset.filter(owner=self.request.user)
            clients = list(queryset)  # Приводим к списку для кэширования
            cache.set(cache_key, clients, CACHE_TTL)

        return clients


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Создание сообщения"""
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message/message_form.html'

    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):

    model = Client
    form_class = ClientForm
    template_name = 'mailing/client_form.html'

    success_url = reverse_lazy('mailing:client_list')

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.groups.filter(name='Менеджеры').exists():
            queryset = queryset.filter(owner=self.request.user)
        return queryset


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client

    template_name = 'mailing/client_confirm_delete.html'
    success_url = reverse_lazy('mailing:client_list')

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.groups.filter(name='Менеджеры').exists():
            queryset = queryset.filter(owner=self.request.user)
        return queryset


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailing/message/message_list.html'
    context_object_name = 'messages'
    paginate_by = 10  # Добавляем пагинацию

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.groups.filter(name='Менеджеры').exists():
            queryset = queryset.filter(owner=self.request.user)
        return queryset.order_by('-created_at')


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message/message_form.html'

    success_url = reverse_lazy('mailing:message_list')


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailing/message/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')


@login_required
def send_mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)

    # Проверка прав доступа
    if mailing.owner != request.user:
        messages.error(request, "У вас нет прав для запуска этой рассылки")
        return redirect('mailing/mailing:mailing_list')

    # Проверка временного интервала
    now = timezone.now()
    if mailing.status == 'completed':
        messages.error(request, "Эта рассылка уже завершена")
    elif now < mailing.start_time:
        messages.error(request, "Время начала рассылки еще не наступило")
    elif now > mailing.end_time:
        mailing.status = 'completed'
        mailing.save()
        messages.error(request, "Время рассылки истекло")
    else:
        try:
            result = mailing.send_mailing()
            messages.success(
                request,
                f"Рассылка успешно запущена! Успешно: {result['success']}, Неудачно: {result['failed']}"
            )
        except Exception as e:
            messages.error(request, f"Ошибка при отправке рассылки: {str(e)}")

    return redirect('mailing/mailing:mailing_detail', pk=pk)


class AttemptListView(LoginRequiredMixin, ListView):
    model = MailingAttempt
    template_name = 'mailing/attempt_list.html'
    context_object_name = 'attempts'
    paginate_by = 20

    def get_queryset(self):
        cache_key = f'attempts_{self.request.user.id}'
        attempts = cache.get(cache_key)

        if not attempts:
            queryset = super().get_queryset().select_related('mailing', 'mailing__message')
            if not self.request.user.groups.filter(name='Менеджеры').exists():
                queryset = queryset.filter(mailing__owner=self.request.user)
            attempts = list(queryset.order_by('-attempt_time'))
            cache.set(cache_key, attempts, CACHE_TTL)

        return attempts


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'mailing/registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        # Сохраняем пользователя
        user = form.save()

        # Явно указываем бэкенд для автовхода
        backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, user, backend=backend)

        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'mailing/auth/edit_profile.html'
    success_url = reverse_lazy('mailing:profile')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'mailing/auth/profile.html'


@login_required
def profile(request):
    """Просмотр профиля пользователя"""
    return render(request, 'mailing/auth/profile.html', {'user': request.user})


@login_required
def edit_profile(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('mailing:profile')
    else:
        form = UserEditForm(instance=request.user)

    return render(request, 'mailing/auth/edit_profile.html', {'form': form})

