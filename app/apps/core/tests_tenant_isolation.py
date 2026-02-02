"""
IAMKT - Testes de Tenant Isolation

Testes para garantir que o isolamento de tenants está funcionando corretamente.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.core.models import Organization, Area
from apps.content.models import Pauta, Asset
from apps.posts.models import Post
from apps.campaigns.models import Project
from apps.knowledge.models import KnowledgeBase

User = get_user_model()


class TenantIsolationTestCase(TestCase):
    """
    Testes de isolamento de tenant.
    Garante que usuários de uma organization não acessam dados de outra.
    """
    
    def setUp(self):
        """Configurar ambiente de teste com 2 organizations"""
        # Criar organizations
        self.org1 = Organization.objects.create(
            name='Empresa A',
            slug='empresa-a',
            plan_type='premium',
            quota_pautas_dia=10,
            quota_posts_dia=10,
            quota_posts_mes=100
        )
        
        self.org2 = Organization.objects.create(
            name='Empresa B',
            slug='empresa-b',
            plan_type='basic',
            quota_pautas_dia=5,
            quota_posts_dia=5,
            quota_posts_mes=50
        )
        
        # Criar areas
        self.area1 = Area.objects.create(
            name='Marketing',
            organization=self.org1
        )
        
        self.area2 = Area.objects.create(
            name='Vendas',
            organization=self.org2
        )
        
        # Criar usuários
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@empresaa.com',
            password='senha123',
            organization=self.org1
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@empresab.com',
            password='senha123',
            organization=self.org2
        )
        
        # Criar dados para org1
        self.pauta1 = Pauta.objects.create(
            organization=self.org1,
            user=self.user1,
            area=self.area1,
            theme='Tema da Empresa A',
            target_audience='Público A',
            objective='engajamento',
            title='Pauta A',
            description='Descrição A'
        )
        
        self.post1 = Post.objects.create(
            organization=self.org1,
            user=self.user1,
            area=self.area1,
            content_type='post',
            social_network='instagram',
            ia_provider='openai',
            ia_model_text='gpt-4',
            caption='Post da Empresa A',
            status='draft'
        )
        
        # Criar dados para org2
        self.pauta2 = Pauta.objects.create(
            organization=self.org2,
            user=self.user2,
            area=self.area2,
            theme='Tema da Empresa B',
            target_audience='Público B',
            objective='conversao',
            title='Pauta B',
            description='Descrição B'
        )
        
        self.post2 = Post.objects.create(
            organization=self.org2,
            user=self.user2,
            area=self.area2,
            content_type='post',
            social_network='facebook',
            ia_provider='gemini',
            ia_model_text='gemini-pro',
            caption='Post da Empresa B',
            status='draft'
        )
    
    def test_pauta_isolation(self):
        """Testar isolamento de Pautas"""
        # Org1 deve ver apenas suas pautas
        pautas_org1 = Pauta.objects.for_organization(self.org1)
        self.assertEqual(pautas_org1.count(), 1)
        self.assertEqual(pautas_org1.first().id, self.pauta1.id)
        
        # Org2 deve ver apenas suas pautas
        pautas_org2 = Pauta.objects.for_organization(self.org2)
        self.assertEqual(pautas_org2.count(), 1)
        self.assertEqual(pautas_org2.first().id, self.pauta2.id)
        
        # Verificar que não há vazamento
        self.assertNotIn(self.pauta2, pautas_org1)
        self.assertNotIn(self.pauta1, pautas_org2)
    
    def test_post_isolation(self):
        """Testar isolamento de Posts"""
        # Org1 deve ver apenas seus posts
        posts_org1 = Post.objects.for_organization(self.org1)
        self.assertEqual(posts_org1.count(), 1)
        self.assertEqual(posts_org1.first().id, self.post1.id)
        
        # Org2 deve ver apenas seus posts
        posts_org2 = Post.objects.for_organization(self.org2)
        self.assertEqual(posts_org2.count(), 1)
        self.assertEqual(posts_org2.first().id, self.post2.id)
        
        # Verificar que não há vazamento
        self.assertNotIn(self.post2, posts_org1)
        self.assertNotIn(self.post1, posts_org2)
    
    def test_cross_tenant_access_blocked(self):
        """Testar que acesso cross-tenant é bloqueado"""
        # Tentar buscar pauta de outra org por ID
        with self.assertRaises(Pauta.DoesNotExist):
            Pauta.objects.for_organization(self.org1).get(id=self.pauta2.id)
        
        # Tentar buscar post de outra org por ID
        with self.assertRaises(Post.DoesNotExist):
            Post.objects.for_organization(self.org1).get(id=self.post2.id)
    
    def test_all_tenants_returns_all(self):
        """Testar que all_tenants() retorna todos os registros"""
        # all_tenants deve retornar TODOS os registros
        all_pautas = Pauta.objects.all_tenants()
        self.assertEqual(all_pautas.count(), 2)
        
        all_posts = Post.objects.all_tenants()
        self.assertEqual(all_posts.count(), 2)
    
    def test_manager_filters_automatically(self):
        """Testar que manager filtra automaticamente (quando possível)"""
        # Nota: Este teste é limitado pois o manager precisa do request
        # Em produção, o middleware injeta a organization no request
        
        # Verificar que métodos for_organization funcionam
        pautas = Pauta.objects.for_organization(self.org1)
        self.assertTrue(all(p.organization_id == self.org1.id for p in pautas))
        
        posts = Post.objects.for_organization(self.org2)
        self.assertTrue(all(p.organization_id == self.org2.id for p in posts))


class ManagerMethodsTestCase(TestCase):
    """Testes dos métodos dos managers customizados"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.org = Organization.objects.create(
            name='Test Org',
            slug='test-org',
            plan_type='premium'
        )
        
        self.area = Area.objects.create(
            name='Test Area',
            organization=self.org
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='senha123',
            organization=self.org
        )
    
    def test_for_organization_method(self):
        """Testar método for_organization()"""
        # Criar pautas
        Pauta.objects.create(
            organization=self.org,
            user=self.user,
            area=self.area,
            theme='Tema 1',
            target_audience='Público',
            objective='engajamento',
            title='Pauta 1',
            description='Desc 1'
        )
        
        # Buscar com for_organization
        pautas = Pauta.objects.for_organization(self.org)
        self.assertEqual(pautas.count(), 1)
    
    def test_for_request_method(self):
        """Testar método for_request()"""
        from django.test import RequestFactory
        
        # Criar request mock
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.organization = self.org
        
        # Criar post
        Post.objects.create(
            organization=self.org,
            user=self.user,
            area=self.area,
            content_type='post',
            social_network='instagram',
            ia_provider='openai',
            ia_model_text='gpt-4',
            caption='Test',
            status='draft'
        )
        
        # Buscar com for_request
        posts = Post.objects.for_request(request)
        self.assertEqual(posts.count(), 1)
    
    def test_for_request_without_organization(self):
        """Testar for_request() sem organization retorna vazio"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.organization = None  # Sem organization
        
        # Deve retornar queryset vazio
        posts = Post.objects.for_request(request)
        self.assertEqual(posts.count(), 0)


class SecurityTestCase(TestCase):
    """Testes de segurança do tenant isolation"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.org1 = Organization.objects.create(
            name='Org 1',
            slug='org-1',
            plan_type='premium'
        )
        
        self.org2 = Organization.objects.create(
            name='Org 2',
            slug='org-2',
            plan_type='basic'
        )
        
        self.area1 = Area.objects.create(
            name='Area 1',
            organization=self.org1
        )
        
        self.area2 = Area.objects.create(
            name='Area 2',
            organization=self.org2
        )
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@org1.com',
            password='senha123',
            organization=self.org1
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@org2.com',
            password='senha123',
            organization=self.org2
        )
    
    def test_user_cannot_access_other_org_data(self):
        """Testar que usuário não acessa dados de outra org"""
        # Criar pauta na org1
        pauta = Pauta.objects.create(
            organization=self.org1,
            user=self.user1,
            area=self.area1,
            theme='Tema Secreto',
            target_audience='Público',
            objective='engajamento',
            title='Pauta Secreta',
            description='Descrição Secreta'
        )
        
        # User2 (org2) não deve conseguir acessar
        pautas_user2 = Pauta.objects.for_organization(self.org2)
        self.assertNotIn(pauta, pautas_user2)
        
        # Tentar buscar diretamente por ID deve falhar
        with self.assertRaises(Pauta.DoesNotExist):
            Pauta.objects.for_organization(self.org2).get(id=pauta.id)
    
    def test_filter_by_organization_is_enforced(self):
        """Testar que filtro por organization é obrigatório"""
        # Criar dados em ambas as orgs
        Pauta.objects.create(
            organization=self.org1,
            user=self.user1,
            area=self.area1,
            theme='Tema 1',
            target_audience='Público',
            objective='engajamento',
            title='Pauta 1',
            description='Desc 1'
        )
        
        Pauta.objects.create(
            organization=self.org2,
            user=self.user2,
            area=self.area2,
            theme='Tema 2',
            target_audience='Público',
            objective='conversao',
            title='Pauta 2',
            description='Desc 2'
        )
        
        # Filtrar por org1 deve retornar apenas 1
        pautas_org1 = Pauta.objects.for_organization(self.org1)
        self.assertEqual(pautas_org1.count(), 1)
        
        # Filtrar por org2 deve retornar apenas 1
        pautas_org2 = Pauta.objects.for_organization(self.org2)
        self.assertEqual(pautas_org2.count(), 1)
        
        # all_tenants deve retornar 2
        all_pautas = Pauta.objects.all_tenants()
        self.assertEqual(all_pautas.count(), 2)
