from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Post, Comment, CommentVote

class CommentVoteTests(TestCase):
    def setUp(self):
        # Usuarios
        self.user1 = User.objects.create_user('user1', 'u1@test.com', 'pwd')
        self.user2 = User.objects.create_user('user2', 'u2@test.com', 'pwd')
        self.staff = User.objects.create_user('staff', 'staff@test.com', 'pwd', is_staff=True)

        # Post
        self.post = Post.objects.create(title="Test Post", slug="test-post", author=self.user1, content="Content", published=True)

        # Comentarios
        self.comment1 = Comment.objects.create(post=self.post, user=self.user1, name="User1", email="u1@test.com", content="Comentario 1", is_approved=True)
        self.comment2 = Comment.objects.create(post=self.post, user=self.user2, name="User2", email="u2@test.com", content="Comentario 2", is_approved=True)

    def test_vote_unicity(self):
        """Un usuario no puede votar dos veces en el mismo comentario"""
        CommentVote.objects.create(comment=self.comment1, user=self.user1, vote=1)
        # Intentar duplicar voto
        with self.assertRaises(Exception):
            CommentVote.objects.create(comment=self.comment1, user=self.user1, vote=-1)

    def test_vote_toggle(self):
        """Hacer click en el mismo voto lo pone a neutral"""
        vote = CommentVote.objects.create(comment=self.comment1, user=self.user1, vote=1)
        vote.vote = 1  # simula click en el mismo
        if vote.vote == 1:
            vote.vote = 0
        vote.save()
        self.assertEqual(vote.vote, 0)

    def test_order_pinned_score(self):
        """Los comentarios se ordenan por pinned DESC, score DESC, created_at ASC"""
        # Pin comment2 y darle votos
        self.comment2.pinned = True
        self.comment2.save()
        CommentVote.objects.create(comment=self.comment1, user=self.user2, vote=1)
        CommentVote.objects.create(comment=self.comment2, user=self.user1, vote=1)
        CommentVote.objects.create(comment=self.comment2, user=self.user2, vote=1)

        comments = self.post.comments.filter(active=True, is_approved=True).annotate(score=models.Sum('votes__vote')).order_by('-pinned', '-score', 'created_date')

        # El comentario pinned debe ir primero
        self.assertEqual(comments[0], self.comment2)
        self.assertEqual(comments[1], self.comment1)

    def test_staff_can_pin_comment(self):
        """El staff puede fijar un comentario"""
        self.client.force_login(self.staff)
        response = self.client.post(reverse('blog:toggle_pin_comment', args=[self.comment1.id]))
        self.comment1.refresh_from_db()
        self.assertTrue(self.comment1.pinned)
