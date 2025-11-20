from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from blog.models import Post, Reaction
from django.core.cache import cache

class ReactionToggleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('u', 'u@x.com', 'pwd')
        self.post = Post.objects.create(
            title="t",
            slug="s",
            author=self.user,
            content="c",
            published=True
        )
        self.client.login(username='u', password='pwd')

    def test_add_and_remove_reaction(self):
        url = reverse('blog:toggle_reaction', args=[self.post.id, 'like'])

        # Agregar reacción
        r = self.client.post(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            Reaction.objects.filter(
                post=self.post, user=self.user, type='like'
            ).count(), 
            1
        )

        # Quitar la reacción
        r2 = self.client.post(url)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(
            Reaction.objects.filter(
                post=self.post, user=self.user, type='like'
            ).count(),
            0
        )

    def test_invalid_reaction_type(self):
        url = reverse('blog:toggle_reaction', args=[self.post.id, 'xxx'])
        r = self.client.post(url)
        self.assertEqual(r.status_code, 400)

    def test_rate_limit(self):
        url = reverse('blog:toggle_reaction', args=[self.post.id, 'like'])

        # Primer intento → OK
        r1 = self.client.post(url)
        self.assertEqual(r1.status_code, 200)

        # Segundo intento inmediato → bloqueado (429)
        r2 = self.client.post(url)
        self.assertEqual(r2.status_code, 429)

    def test_unique_constraint(self):
        url = reverse('blog:toggle_reaction', args=[self.post.id, 'like'])

        # Intentar crear dos veces
        self.client.post(url)
        self.client.post(url)  # este debe borrar, no duplicar

        self.assertEqual(
            Reaction.objects.filter(
                post=self.post, user=self.user, type='like'
            ).count(),
            0  # después del toggle debería quedar en 0
        )
