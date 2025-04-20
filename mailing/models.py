from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Email')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Телефон'
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Страна'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


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
