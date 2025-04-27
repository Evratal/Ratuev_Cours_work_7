from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Создает группу менеджеров и назначает права'

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name='Менеджеры')

        # Добавляем разрешение на просмотр всех рассылок
        permission = Permission.objects.get(
            codename='can_view_all_mailings',
            content_type__model='mailing'
        )
        group.permissions.add(permission)

        self.stdout.write(self.style.SUCCESS('Группа менеджеров создана'))
