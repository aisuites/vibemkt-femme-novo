# Generated manually on 2026-01-28 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0012_rename_historia_to_descricao_produto'),
    ]

    operations = [
        migrations.AddField(
            model_name='knowledgebase',
            name='concorrentes',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Lista de concorrentes: [{"nome": "Empresa X", "url": "https://..."}, ...]',
                verbose_name='Concorrentes'
            ),
        ),
    ]
