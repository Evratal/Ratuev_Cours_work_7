import os
import sys
import django
from django.core.management import call_command

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

try:
    with open('backup.json', 'w', encoding='utf-8') as f:
        # Перенаправляем stdout в файл
        original_stdout = sys.stdout
        sys.stdout = f

        try:
            call_command(
                'dumpdata',
                exclude=['contenttypes', 'auth.Permission'],
                natural_foreign=True,
                natural_primary=True
            )
        finally:
            # Восстанавливаем stdout
            sys.stdout = original_stdout
except Exception as e:
    print(f"Ошибка при создании резервной копии: {str(e)}", file=sys.stderr)
    sys.exit(1)