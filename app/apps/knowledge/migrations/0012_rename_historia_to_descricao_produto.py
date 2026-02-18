# Generated manually on 2026-01-28 10:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0011_add_onboarding_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='knowledgebase',
            old_name='historia',
            new_name='descricao_produto',
        ),
    ]
