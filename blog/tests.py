from django.test import TestCase
from django.contrib.auth.models import User
from .models import Post, Comment, Review, Profile

class TestBlogBasicTests(TestCase):
    def setUp(self):
        # Crear un usuario de prueba
        self.user = User.objects.create_user(username='testuser', password='12345')
        
        # Crear un post de prueba
        self.post = Post.objects.create(
            title="Test Post",
            content="Contenido de prueba",
            author=self.user,
            published=True
        )

    def test_post_creation(self):
        """Verifica que el post se crea correctamente"""
        self.assertEqual(self.post.title, "Test Post")
        self.assertTrue(self.post.published)

    def test_comment_creation(self):
        """Verifica que se puede crear un comentario"""
        comment = Comment.objects.create(post=self.post, user=self.user, content="Mi comentario")
        self.assertEqual(comment.content, "Mi comentario")
        self.assertFalse(comment.is_approved)

    def test_review_creation(self):
        """Verifica que se puede crear un review"""
        review = Review.objects.create(post=self.post, user=self.user, rating=5, comment="Excelente")
        self.assertEqual(review.rating, 5)

    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(username='testuser', password='12345')
        # Obtener profile si es necesario
        self.profile, created = Profile.objects.get_or_create(user=self.user)
        # Crear post de prueba
        self.post = Post.objects.create(
        title="Test Post",
        content="Contenido de prueba",
        author=self.user,
        published=True
    )


class BlogBasicTests(TestCase):
    def setUp(self):
        User.objects.filter(username='testuser').delete()
        self.user = User.objects.create_user(username='testuser', password='12345')
