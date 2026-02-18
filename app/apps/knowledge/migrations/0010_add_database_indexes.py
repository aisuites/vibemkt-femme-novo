"""
Migration para adicionar índices de performance
Melhora queries frequentes em Logo, ReferenceImage, CustomFont, ColorPalette, Typography
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0009_remove_legacy_json_fields'),
    ]

    operations = [
        # Índices para Logo
        migrations.AddIndex(
            model_name='logo',
            index=models.Index(fields=['knowledge_base'], name='logo_kb_idx'),
        ),
        migrations.AddIndex(
            model_name='logo',
            index=models.Index(fields=['knowledge_base', 'is_primary'], name='logo_kb_primary_idx'),
        ),
        migrations.AddIndex(
            model_name='logo',
            index=models.Index(fields=['knowledge_base', 'logo_type'], name='logo_kb_type_idx'),
        ),
        
        # Índices para ReferenceImage
        migrations.AddIndex(
            model_name='referenceimage',
            index=models.Index(fields=['knowledge_base'], name='refimg_kb_idx'),
        ),
        migrations.AddIndex(
            model_name='referenceimage',
            index=models.Index(fields=['knowledge_base', '-created_at'], name='refimg_kb_created_idx'),
        ),
        
        # Índices para CustomFont
        migrations.AddIndex(
            model_name='customfont',
            index=models.Index(fields=['knowledge_base'], name='font_kb_idx'),
        ),
        migrations.AddIndex(
            model_name='customfont',
            index=models.Index(fields=['knowledge_base', 'font_type'], name='font_kb_type_idx'),
        ),
        
        # Índices para ColorPalette
        migrations.AddIndex(
            model_name='colorpalette',
            index=models.Index(fields=['knowledge_base'], name='color_kb_idx'),
        ),
        migrations.AddIndex(
            model_name='colorpalette',
            index=models.Index(fields=['knowledge_base', 'order'], name='color_kb_order_idx'),
        ),
        
        # Índices para Typography
        migrations.AddIndex(
            model_name='typography',
            index=models.Index(fields=['knowledge_base'], name='typo_kb_idx'),
        ),
        migrations.AddIndex(
            model_name='typography',
            index=models.Index(fields=['knowledge_base', 'usage'], name='typo_kb_usage_idx'),
        ),
        
        # Índices para InternalSegment
        migrations.AddIndex(
            model_name='internalsegment',
            index=models.Index(fields=['knowledge_base'], name='segment_kb_idx'),
        ),
        migrations.AddIndex(
            model_name='internalsegment',
            index=models.Index(fields=['knowledge_base', 'is_active'], name='segment_kb_active_idx'),
        ),
        
        # Índices para SocialNetwork
        migrations.AddIndex(
            model_name='socialnetwork',
            index=models.Index(fields=['knowledge_base'], name='social_kb_idx'),
        ),
    ]
