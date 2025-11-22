from django.db.models import Avg, Q
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import JsonResponse,  HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Post, Comment, Review, Reaction
from .forms import CommentForm, SignUpForm, ProfileForm, PostForm, ReviewForm
from taggit.models import Tag

# Cooldown en segundos entre reacciones (por usuario+post)
REACTION_COOLDOWN = 2

def post_list(request):
    """Vista para mostrar la lista de posts publicados"""
    posts = Post.objects.filter(published=True).order_by('-published_date')
    # Paginación
    paginator = Paginator(posts, 10)  # 10 posts por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/post_list.html', {'page_obj': page_obj})

def post_detail(request, slug):
    """Vista para mostrar un post específico con sus comentarios"""
    post = get_object_or_404(Post, slug=slug, published=True)
    comments = post.comments.filter(active=True)
    new_comment = None

     # Calcular promedio de reviews
    average_rating = post.reviews.aggregate(Avg('rating'))['rating__avg']

    # Calcular conteo de reacciones
    from .models import Reaction
    counts = { key: post.reactions.filter(type=key).count() for key,_ in Reaction.REACTION_CHOICES }


    # Verificar si el usuario ya hizo review
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = post.reviews.filter(user=request.user).exists()

    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        review_form = ReviewForm()
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
        review_form = ReviewForm() 

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'review_form': review_form, 
        'average_rating': average_rating,
        'user_has_reviewed': user_has_reviewed,
        'counts': counts,
    })

# Vista para el formulario de registro de usuario
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente. Por favor inicia sesión.')
            return redirect('blog:login')  # ruta de login
    else:
        form = SignUpForm()
    return render(request, 'blog/signup.html', {'form': form})

# Vista para el formulario de inicio de sesión

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # Inicia la sesión
            messages.success(request, f'¡Bienvenido, {user.username}!')
            return redirect('blog:post_list')  # Redirige al home/lista de posts
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'blog/login.html', {'form': form})

#Vistas de logout
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('blog:login')  # Redirige al login


#protege la vista para que solo usuarios logueados puedan acceder.
@login_required
def profile_view(request):
    return render(request, 'blog/profile.html', {'user': request.user})

@login_required
def profile_edit(request):
    profile = getattr(request.user, "profile", None)
    if profile is None:
        from .models import Profile
        profile = Profile.objects.create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('blog:profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'blog/profile_edit.html', {'form': form})

def profile(request):
    return render(request, 'blog/profile.html')

# vistar para crear posts
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post creado correctamente.')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm()
    return render(request, 'blog/post_form.html', {'form': form})

#vista para editar posts
@login_required
def edit_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user != post.author:
        messages.error(request, 'No tienes permiso para editar este post.')
        return redirect('blog:post_detail', slug=slug)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post actualizado correctamente.')
            return redirect('blog:post_detail', slug=slug)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'blog/post_form.html', {'form': form})

# vista para borrar posts
@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user != post.author:
        messages.error(request, 'No tienes permiso para borrar este post.')
        return redirect('blog:post_detail', slug=slug)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post eliminado correctamente.')
        return redirect('blog:post_list')

    return render(request, 'blog/post_confirm_delete.html', {'post': post})

# vista para agregar comentarios
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Comment.objects.create(post=post, user=request.user, content=content)
            messages.success(request, "Tu comentario ha sido enviado y está pendiente de aprobación.")
        else:
            messages.error(request, "No puedes enviar un comentario vacío.")
    return redirect('blog:post_detail', slug=post.slug)


@staff_member_required
def approve_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.is_approved = True
    comment.save()
    messages.success(request, "Comentario aprobado.")
    return redirect('blog:post_detail', pk=comment.post.id)

@staff_member_required
def reject_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    messages.warning(request, "Comentario eliminado.")
    return redirect('blog:post_detail', pk=comment.post.id)

@login_required
def add_review(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    # Evitar que el usuario haga más de un review por post
    if Review.objects.filter(post=post, user=request.user).exists():
        messages.warning(request, "Ya has hecho una review de este post.")
        return redirect('blog:post_detail', slug=post.slug)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.post = post
            review.save()
            messages.success(request, "Tu review ha sido enviada.")
            return redirect('blog:post_detail', slug=post.slug)
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = ReviewForm()

    return redirect('blog:post_detail', slug=post.slug)

def posts_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(published=True, tags__slug=slug)
    context = {
        'tag': tag,
        'posts': posts,
    }
    return render(request, 'blog/posts_by_tag.html', context)

def search_posts(request):
    query = request.GET.get('q')
    posts = Post.objects.filter(published=True)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    
    paginator = Paginator(posts, 10)  # 10 posts por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'posts': posts,
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'blog/search_results.html', context)

def toggle_reaction(request, post_id, reaction_type):
    post = get_object_or_404(Post, id=post_id)

    # Validar tipo
    allowed = dict(Reaction.REACTION_CHOICES)
    if reaction_type not in allowed:
        return JsonResponse({"error": "Tipo de reacción inválido"}, status=400)

    # Rate-limit simple: una acción por REACTION_COOLDOWN por user+post
    cache_key = f"reaction-cooldown:{request.user.id}:{post.id}"
    #evita spameo extremo y operaciones repetidas.
    if cache.get(cache_key):
        return JsonResponse({"error": "Too Many Requests"}, status=429)
    cache.set(cache_key, True, timeout=REACTION_COOLDOWN)
    existing = Reaction.objects.filter(post=post, user=request.user).first()
    if existing:
        if existing.type == reaction_type:
            # mismo emoji → quitar
            existing.delete()
            action = "removed"
        else:
            # cambiar el emoji
            existing.type = reaction_type
            existing.save()
            action = "changed"
    else:
        # crear nueva
        Reaction.objects.create(
            post=post,
            user=request.user,
            type=reaction_type
        )
        action = "added"
    
   # === RECALCULAR CONTEOS ===
    counts = {
        key: post.reactions.filter(type=key).count()
        for key, _ in Reaction.REACTION_CHOICES
    }

    # === SI ES HTMX → DEVOLVER HTML ===
    wants_html = (
        request.headers.get("HX-Request") == "true"
        or request.GET.get("format") == "html"
    )

    if wants_html:
        html = render_to_string(
            "blog/_reactions_fragment.html",
            {"post": post, "counts": counts, "user": request.user}
        )
        return HttpResponse(html)

    # === RESPUESTA JSON POR DEFECTO ===
    return JsonResponse({"status": "ok", "action": action, "counts": counts})
