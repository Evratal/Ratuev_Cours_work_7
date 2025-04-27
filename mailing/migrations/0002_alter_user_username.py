from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('mailing', '0001_initial'),  # Зависит от вашей первой миграции
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(
                max_length=150,
                blank=True,
                null=True,
                unique=True,
                verbose_name='username'
            ),
        ),
    ]