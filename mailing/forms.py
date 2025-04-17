from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm, PasswordResetForm
from .models import Mailing, Client, Message, User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm

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