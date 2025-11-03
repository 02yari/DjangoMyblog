from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name='Título')
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')
    content = models.TextField(verbose_name='Contenido')
    created_date = models.DateTimeField(default=timezone.now, verbose_name='Fecha de creación')
    published_date = models.DateTimeField(blank=True, null=True, verbose_name='Fecha de publicación')
    published = models.BooleanField(default=False, verbose_name='Publicado')

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
    name = models.CharField(max_length=100, verbose_name='Nombre')
    email = models.EmailField(verbose_name='Email')
    content = models.TextField(verbose_name='Comentario')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        ordering = ['created_date']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'

    def __str__(self):
        return f'Comentario de {self.name} en {self.post.title}'