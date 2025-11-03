from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Post, Comment
from .forms import CommentForm

def post_list(request):
    """Vista para mostrar la lista de posts publicados"""
    posts = Post.objects.filter(published=True).order_by('-published_date')
    
    # Paginación
    paginator = Paginator(posts, 5)  # 5 posts por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'blog/post_list.html', {'page_obj': page_obj})

def post_detail(request, slug):
    """Vista para mostrar un post específico con sus comentarios"""
    post = get_object_or_404(Post, slug=slug, published=True)
    comments = post.comments.filter(active=True)
    new_comment = None

    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Crear comentario pero no guardarlo aún
            new_comment = comment_form.save(commit=False)
            # Asignar el post actual al comentario
            new_comment.post = post
            # Guardar el comentario
            new_comment.save()
            messages.success(request, '¡Tu comentario ha sido añadido exitosamente!')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        comment_form = CommentForm()

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form
    })