from django import forms
from .models import Comment, Post, Profile, Review
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django_ckeditor_5.widgets import CKEditor5Widget

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('name', 'email', 'content')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu comentario...'
            }),
        }
        labels = {
            'name': 'Nombre',
            'email': 'Email',
            'content': 'Comentario',
        }


#Registro de usuario
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        
#Formulario para editar avatar y bio
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio')

#Formulario para crear/editar posts
class PostForm(forms.ModelForm):
    content = forms.CharField(
        widget=CKEditor5Widget(
            attrs={'class': 'django_ckeditor_5'},
            config_name='default',  # usa el config definido en settings.py
        )
    )
    class Meta:
        model = Post
        fields = ['title', 'content', 'excerpt', 'cover', 'published']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribe tu review...'}),
        }
