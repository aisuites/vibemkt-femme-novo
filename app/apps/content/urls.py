"""
URLs do app content
"""
from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('pautas/', views.pautas_list, name='pautas'),
    path('pautas/nova/', views.pauta_create, name='pauta_create'),
    # NOTA: Rotas de posts movidas para apps.posts.urls
    path('trends/', views.trends_list, name='trends'),
]
