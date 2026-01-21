"""
IAMKT - Context Processors

Adiciona variáveis globais aos templates.
"""


def tenant_context(request):
    """
    Adiciona organization atual ao contexto de todos os templates.
    
    Uso nos templates:
        {{ organization.name }}
        {{ organization.slug }}
        {% if organization %}
            ...
        {% endif %}
    """
    context = {
        'organization': None,
        'tenant': None,  # Alias
    }
    
    if hasattr(request, 'organization') and request.organization:
        context['organization'] = request.organization
        context['tenant'] = request.organization
    
    return context
