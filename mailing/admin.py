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
    list_display = ('subject', 'body_short')
    search_fields = ('subject', 'body')
    list_filter = ('owner',)

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
