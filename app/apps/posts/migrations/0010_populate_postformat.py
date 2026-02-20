from django.db import migrations


FORMATS = [
    # Instagram
    ('instagram', 'Feed Quadrado',   1080, 1080, '1:1',  0),
    ('instagram', 'Feed Retrato',    1080, 1350, '4:5',  1),
    ('instagram', 'Feed Paisagem',   1080,  566, '1.91:1', 2),
    ('instagram', 'Stories',         1080, 1920, '9:16', 3),
    ('instagram', 'Reels',           1080, 1920, '9:16', 4),
    # Facebook
    ('facebook',  'Feed',            1200,  630, '16:9', 0),
    ('facebook',  'Feed Quadrado',   1080, 1080, '1:1',  1),
    ('facebook',  'Stories',         1080, 1920, '9:16', 2),
    # LinkedIn
    ('linkedin',  'Feed',            1200,  627, '16:9', 0),
    ('linkedin',  'Feed Quadrado',   1080, 1080, '1:1',  1),
    ('linkedin',  'Stories',         1080, 1920, '9:16', 2),
    # TikTok
    ('tiktok',    'Vídeo/Reels',     1080, 1920, '9:16', 0),
    # WhatsApp
    ('whatsapp',  'Status',          1080, 1920, '9:16', 0),
    ('whatsapp',  'Imagem',          1080, 1080, '1:1',  1),
]


def populate_formats(apps, schema_editor):
    PostFormat = apps.get_model('posts', 'PostFormat')
    for network, name, width, height, ratio, order in FORMATS:
        PostFormat.objects.get_or_create(
            social_network=network,
            name=name,
            defaults={
                'width': width,
                'height': height,
                'aspect_ratio': ratio,
                'order': order,
                'is_active': True,
            }
        )


def remove_formats(apps, schema_editor):
    PostFormat = apps.get_model('posts', 'PostFormat')
    PostFormat.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_add_postformat_model'),
    ]

    operations = [
        migrations.RunPython(populate_formats, remove_formats),
    ]
