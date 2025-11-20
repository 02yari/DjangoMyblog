from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from taggit.managers import TaggableManager
from django_ckeditor_5.fields import CKEditor5Field
from django.conf import settings

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name='Título')
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')

    #content = models.TextField(verbose_name='Contenido')
    content = CKEditor5Field('Contenido') # <-- reemplaza TextField por RichTextField
    #"Se agrega cover para subir imagen de portada."
    cover = models.ImageField(upload_to='covers/', null=True, blank=True, verbose_name='Imagen de portada') 
    excerpt = models.TextField(max_length=300, blank=True, verbose_name='Resumen')
    created_date = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    published_date = models.DateTimeField(blank=True, null=True, verbose_name='Fecha de publicación')
    published = models.BooleanField(default=False, verbose_name='Publicado')
    tags = TaggableManager(blank=True, verbose_name='Etiquetas')
    class Meta:
        ordering = ['-created_date']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def publish(self):
        self.published_date = timezone.now()
        self.published = True
        self.save()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='Nombre')
    email = models.EmailField(verbose_name='Email')
    content =CKEditor5Field('Comentario')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    active = models.BooleanField(default=True, verbose_name='Activo')
    is_approved = models.BooleanField(default=False, verbose_name='Aprobado')

    class Meta:
        ordering = ['created_date']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
    
    @property
    def score(self):
        return self.votes.aggregate(total=models.Sum('vote'))['total'] or 0

    def __str__(self):
        if self.user:
            return f'Comentario de {self.user.username} en {self.post.title}'
        return f'Comentario de {self.name} en {self.post.title}'

# Clase profile

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

#post_save para crear o actualizar el perfil del usuario automáticamente
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_staff and not instance.is_superuser:
        Profile.objects.create(user=instance)


class Review(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'

    def __str__(self):
        return f'Review de {self.user.username} en {self.post.title} ({self.rating})'



class Reaction(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    REACTION_CHOICES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('haha', '😂'),
        ('wow', '😮'),
    ]
    type = models.CharField(max_length=10, choices=REACTION_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user', 'type')

    def __str__(self):
        return f"{self.user} reacted {self.type} on {self.post}"
    
class CommentVote(models.Model):
    UP = 1
    DOWN = -1
    NEUTRAL = 0

    VOTE_CHOICES = [
        (UP, "Upvote"),
        (DOWN, "Downvote"),
        (NEUTRAL, "Neutral"),
    ]
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.IntegerField(choices=VOTE_CHOICES, default=NEUTRAL)
    class Meta:
        unique_together = ("user", "comment")

    def __str__(self):
        return f"{self.user} → {self.comment} ({self.vote})"



