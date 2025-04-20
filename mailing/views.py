from django.core.mail import send_mail
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
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache

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
    form_class = UserCreationForm
    template_name = 'mailing/registration/register.html'
    success_url = reverse_lazy('mailing:home')

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
