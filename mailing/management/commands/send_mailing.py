from django.core.management.base import BaseCommand
from mailing.models import Mailing

class Command(BaseCommand):
    help = 'Запуск рассылки по ID'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int)

    def handle(self, *args, **options):
        try:
            mailing = Mailing.objects.get(id=options['mailing_id'])
            mailing.send_to_all()
            self.stdout.write(f"Рассылка {mailing.id} отправлена!")
        except Mailing.DoesNotExist:
            self.stderr.write("Рассылка не найдена")