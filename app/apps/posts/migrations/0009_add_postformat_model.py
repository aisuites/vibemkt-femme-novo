from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_alter_post_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostFormat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('social_network', models.CharField(
                    choices=[
                        ('instagram', 'Instagram'),
                        ('facebook', 'Facebook'),
                        ('linkedin', 'LinkedIn'),
                        ('twitter', 'Twitter/X'),
                        ('tiktok', 'TikTok'),
                        ('whatsapp', 'WhatsApp'),
                    ],
                    max_length=20,
                    verbose_name='Rede Social'
                )),
                ('name', models.CharField(
                    help_text='Ex: Feed Quadrado, Stories, Reels',
                    max_length=100,
                    verbose_name='Nome do Formato'
                )),
                ('width', models.IntegerField(verbose_name='Largura (px)')),
                ('height', models.IntegerField(verbose_name='Altura (px)')),
                ('aspect_ratio', models.CharField(
                    help_text='Ex: 1:1, 4:5, 9:16, 16:9',
                    max_length=10,
                    verbose_name='Aspect Ratio'
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('order', models.IntegerField(default=0, verbose_name='Ordem')),
            ],
            options={
                'verbose_name': 'Formato de Post',
                'verbose_name_plural': 'Formatos de Post',
                'ordering': ['social_network', 'order', 'name'],
                'unique_together': {('social_network', 'name')},
            },
        ),
        migrations.AddField(
            model_name='post',
            name='post_format',
            field=models.ForeignKey(
                blank=True,
                help_text='Formato de imagem selecionado (dimensões e aspect ratio)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='posts',
                to='posts.postformat',
                verbose_name='Formato',
            ),
        ),
    ]
