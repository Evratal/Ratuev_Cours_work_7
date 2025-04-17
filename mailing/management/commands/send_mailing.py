from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing.models import Mailing
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Запуск рассылки по ID с логированием попыток'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки для отправки')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительный запуск вне запланированного времени',
            default=False
        )

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']
        force = options['force']
        now = timezone.now()

        try:
            mailing = Mailing.objects.get(id=mailing_id)
            self.stdout.write(f"Начинаем отправку рассылки #{mailing.id}...")

            # Проверка статуса
            if mailing.status == 'completed':
                self.stdout.write(self.style.WARNING("Рассылка уже завершена"))
                return

            # Проверка временного интервала (если не принудительный запуск)
            if not force:
                if now < mailing.start_time:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Рассылка запланирована на {mailing.start_time}. "
                            "Используйте --force для принудительного запуска."
                        )
                    )
                    return
                elif now > mailing.end_time:
                    mailing.status = 'completed'
                    mailing.save()
                    self.stdout.write(
                        self.style.WARNING(
                            "Время рассылки истекло. Статус изменен на 'завершена'"
                        )
                    )
                    return

            # Обновляем статус если это первая отправка
            if mailing.status == 'created':
                mailing.status = 'started'
                mailing.save()

            success_count = 0
            failed_count = 0

            for client in mailing.clients.all():
                try:
                    send_mail(
                        subject=mailing.message.subject,
                        message=mailing.message.body,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[client.email],
                        fail_silently=False
                    )
                    mailing.attempts.create(
                        status='success',
                        server_response='OK'
                    )
                    success_count += 1
                    self.stdout.write(f"✓ Отправлено {client.email}")
                except Exception as e:
                    mailing.attempts.create(
                        status='failed',
                        server_response=str(e)[:255]  # Ограничиваем длину ответа
                    )
                    failed_count += 1
                    self.stdout.write(f"✗ Ошибка для {client.email}: {str(e)}")

            # Проверяем завершение рассылки
            if mailing.end_time <= now:
                mailing.status = 'completed'
                mailing.save()
                self.stdout.write("Рассылка завершена (достигнуто время окончания)")

            self.stdout.write(
                self.style.SUCCESS(
                    f"Итог: Успешно {success_count}, Неудачно {failed_count}"
                )
            )

        except Mailing.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Рассылка с ID {mailing_id} не найдена"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Критическая ошибка: {str(e)}"))