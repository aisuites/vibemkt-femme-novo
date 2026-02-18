# Generated manually on 2026-01-28 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0013_add_concorrentes_field'),
    ]

    operations = [
        # Análises N8N
        migrations.AddField(
            model_name='knowledgebase',
            name='n8n_analysis',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Payload completo retornado pelo N8N (primeira análise)',
                verbose_name='Análise N8N'
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='n8n_compilation',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Compilação final retornada pelo N8N (plano de marketing, avaliações)',
                verbose_name='Compilação N8N'
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='accepted_suggestions',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Campos onde usuário aceitou sugestão do agente',
                verbose_name='Sugestões Aceitas'
            ),
        ),
        
        # Status e metadados
        migrations.AddField(
            model_name='knowledgebase',
            name='analysis_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pendente'),
                    ('processing', 'Processando'),
                    ('completed', 'Análise Concluída'),
                    ('compiling', 'Compilando'),
                    ('compiled', 'Compilado'),
                    ('error', 'Erro')
                ],
                default='pending',
                max_length=20,
                verbose_name='Status da Análise'
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='analysis_revision_id',
            field=models.CharField(
                blank=True,
                help_text='revision_id retornado pelo N8N',
                max_length=100,
                verbose_name='ID da Revisão N8N'
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='analysis_requested_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Análise Solicitada em'
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='analysis_completed_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Análise Concluída em'
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='compilation_requested_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Compilação Solicitada em'
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='compilation_completed_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Compilação Concluída em'
            ),
        ),
    ]
