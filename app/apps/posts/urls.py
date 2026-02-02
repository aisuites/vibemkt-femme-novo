from django.urls import path
from . import views, views_upload, views_gerar

app_name = 'posts'

urlpatterns = [
    path('', views.posts_list, name='list'),
    
    # Gerar Post
    path('gerar/', views_gerar.gerar_post, name='gerar'),
    
    # Upload S3 - Imagens de Referência
    path('reference/upload-url/', views_upload.generate_reference_upload_url, name='reference_upload_url'),
    path('reference/create/', views_upload.create_reference_image, name='reference_create'),
    
    # TODO: Adicionar demais rotas conforme necessário
    # path('<int:pk>/editar/', views.editar_post, name='editar'),
    # path('<int:pk>/excluir/', views.excluir_post, name='excluir'),
]
