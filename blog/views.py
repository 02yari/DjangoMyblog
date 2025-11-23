from django.db.models import Avg, Q, Sum, Value as V, Count
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from .models import Post, Comment, Review, Reaction, CommentVote, Notification, Subscription, Profile
from .forms import CommentForm, SignUpForm, ProfileForm, PostForm, ReviewForm
from taggit.models import Tag
import re
from django.utils.feedgenerator import Rss201rev2Feed

User = get_user_model()

# Cooldown en segundos entre reacciones (por usuario+post)
REACTION_COOLDOWN = 2

# ==================== POSTS ====================
def post_list(request):
    """Lista de posts publicados"""
    posts = Post.objects.filter(published=True).order_by('-published_date')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/post_list.html', {'page_obj': page_obj})

def post_detail(request, slug):
    """Detalle de un post con comentarios, reviews y reacciones"""
    post = get_object_or_404(Post, slug=slug, published=True)
    new_comment = None

    average_rating = post.reviews.aggregate(Avg('rating'))['rating__avg']
    counts = {key: post.reactions.filter(type=key).count() for key, _ in Reaction.REACTION_CHOICES}

    user_has_reviewed = request.user.is_authenticated and post.reviews.filter(user=request.user).exists()

    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        review_form = ReviewForm()
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
            messages.success(request, '¡Tu comentario ha sido añadido exitosamente!')
            return redirect('blog:post_detail', slug=post.slug)
    else:
        comment_form = CommentForm()
        review_form = ReviewForm()

    comments = post.comments.filter(active=True, is_approved=True).annotate(
        up_votes=Coalesce(Count('votes', filter=Q(votes__vote=1)), V(0)),
        down_votes=Coalesce(Count('votes', filter=Q(votes__vote=-1)), V(0)),
        total_score=Coalesce(Sum('votes__vote'), V(0)),
    ).order_by('-pinned', '-total_score', 'created_date')

    is_subscribed = False
    if request.user.is_authenticated and request.user != post.author:
        is_subscribed = Subscription.objects.filter(user=request.user, author=post.author).exists()


    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'review_form': review_form,
        'average_rating': average_rating,
        'user_has_reviewed': user_has_reviewed,
        'counts': counts,
        'is_subscribed': is_subscribed,
    })

@login_required
def create_post(request):
    """Crear un post (solo usuarios logueados)"""
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

@login_required
def edit_post(request, slug):
    """Editar post propio"""
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

@login_required
def delete_post(request, slug):
    """Eliminar post propio"""
    post = get_object_or_404(Post, slug=slug)
    if request.user != post.author:
        messages.error(request, 'No tienes permiso para borrar este post.')
        return redirect('blog:post_detail', slug=slug)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post eliminado correctamente.')
        return redirect('blog:post_list')

    return render(request, 'blog/post_confirm_delete.html', {'post': post})

# ==================== COMENTARIOS ====================
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get("content")
        if content:
            comment = Comment.objects.create(
                post=post,
                user=request.user,
                content=content
            )

            # Notificación al autor
            if request.user != post.author:
                Notification.objects.create(
                    user=post.author,
                    origin_user=request.user,
                    post=post,
                    comment=comment,
                    message=f"{request.user.username} comentó en tu post: {post.title}",
                )

            # Menciones @username
            pattern = r"@(\w+)"
            for username in re.findall(pattern, comment.content):
                user = User.objects.filter(username=username).first()
                if user and user != post.author:
                    Notification.objects.create(
                        user=user,
                        origin_user=request.user,
                        post=post,
                        comment=comment,
                        message=f"@{request.user.username} te mencionó en un comentario.",
                    )

            messages.success(request, "Tu comentario ha sido enviado exitosamente.")
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
def toggle_vote(request, comment_id, vote_type):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user

    value = 1 if vote_type == "up" else -1 if vote_type == "down" else None
    if value is None:
        return JsonResponse({"error": "Invalid vote type"}, status=400)

    vote, created = CommentVote.objects.get_or_create(comment=comment, user=user, defaults={"vote": value})
    if not created:
        vote.vote = 0 if vote.vote == value else value
        vote.save()

    up_count = CommentVote.objects.filter(comment=comment, vote=1).count()
    down_count = CommentVote.objects.filter(comment=comment, vote=-1).count()

    return JsonResponse({"up": up_count, "down": down_count, "current": vote.vote})

@login_required
def toggle_pin_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.pinned = not comment.pinned
    comment.save()
    return redirect(comment.post.get_absolute_url())

# ==================== REACCIONES ====================
@login_required
def toggle_reaction(request, post_id, reaction_type):
    post = get_object_or_404(Post, id=post_id)
    allowed = dict(Reaction.REACTION_CHOICES)
    if reaction_type not in allowed:
        return JsonResponse({"error": "Tipo de reacción inválido"}, status=400)

    cache_key = f"reaction-cooldown:{request.user.id}:{post.id}"
    if cache.get(cache_key):
        return JsonResponse({"error": "Too Many Requests"}, status=429)
    cache.set(cache_key, True, timeout=REACTION_COOLDOWN)

    existing = Reaction.objects.filter(post=post, user=request.user).first()
    if existing:
        if existing.type == reaction_type:
            existing.delete()
            action = "removed"
        else:
            existing.type = reaction_type
            existing.save()
            action = "changed"
    else:
        Reaction.objects.create(post=post, user=request.user, type=reaction_type)
        action = "added"
        if request.user != post.author:
            Notification.objects.create(
                user=post.author,
                origin_user=request.user,
                post=post,
                message=f"{request.user.username} reaccionó a tu post: {post.title}",
            )

    counts = {key: post.reactions.filter(type=key).count() for key, _ in Reaction.REACTION_CHOICES}

    wants_html = request.headers.get("HX-Request") == "true" or request.GET.get("format") == "html"
    if wants_html:
        html = render_to_string("blog/_reactions_fragment.html", {"post": post, "counts": counts, "user": request.user})
        return HttpResponse(html)

    return JsonResponse({"status": "ok", "action": action, "counts": counts})

# ==================== REVIEWS ====================
@login_required
def add_review(request, slug):
    post = get_object_or_404(Post, slug=slug)
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
    return redirect('blog:post_detail', slug=post.slug)

# ==================== BÚSQUEDAS / TAGS ====================
def posts_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(published=True, tags__slug=slug)
    return render(request, 'blog/posts_by_tag.html', {'tag': tag, 'posts': posts})

def search_posts(request):
    query = request.GET.get('q')
    posts = Post.objects.filter(published=True)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/search_results.html', {'posts': posts, 'query': query, 'page_obj': page_obj})

# ==================== PERFIL / USUARIO ====================
@login_required
def profile_edit(request):
    profile = getattr(request.user, "profile", None)
    if profile is None:
        profile = Profile.objects.create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('blog:profile', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'blog/profile_edit.html', {'form': form})

@login_required
def profile(request, username=None):
    profile_user = get_object_or_404(User, username=username) if username else request.user
    profile_obj = getattr(profile_user, "profile", None)
    
    subscriber_count = profile_user.subscribers.count()
    is_subscribed = False
    if request.user != profile_user:
        is_subscribed = Subscription.objects.filter(user=request.user, author=profile_user).exists()

    notifications = request.user.notifications.order_by('-created_at') if request.user == profile_user else []

    return render(request, "blog/profile.html", {
        "profile_user": profile_user,
        "profile": profile_obj,
        "notifications": notifications,
        "is_subscribed": is_subscribed,
        "subscriber_count": subscriber_count,
    })

# ==================== SUSCRIPCIONES ====================
@login_required
def subscribe(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Subscription.objects.get_or_create(user=request.user, author=author)
        messages.success(request, f"Te has suscrito a {author.username}")
    return redirect('blog:profile_user', username=username)

@login_required
def unsubscribe(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Subscription.objects.filter(user=request.user, author=author).delete()
        messages.success(request, f"Te has dejado de suscribir de {author.username}")
    return redirect('blog:profile_user', username=username)

# ==================== NOTIFICACIONES ====================
@login_required
def open_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()

    if notification.comment:
        comment = notification.comment
        return redirect(f"{comment.post.get_absolute_url()}#comment-{comment.id}")
    return redirect(notification.post.get_absolute_url())

# ==================== LOGIN / LOGOUT / SIGNUP ====================
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente. Por favor inicia sesión.')
            return redirect('blog:login')
    else:
        form = SignUpForm()
    return render(request, 'blog/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}!')
            return redirect('blog:post_list')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'blog/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('blog:login')

@login_required
def subscribe_author(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Subscription.objects.get_or_create(user=request.user, author=author)
        messages.success(request, f"Te has suscrito a {author.username}")
    return redirect('blog:profile_user', username=username)

@login_required
def unsubscribe_author(request, username):
    author = get_object_or_404(User, username=username)
    Subscription.objects.filter(user=request.user, author=author).delete()
    messages.success(request, f"Te has dejado de suscribir de {author.username}")
    return redirect('blog:profile_user', username=username)


@login_required
def subscribe_tag(request, tag_name):
    Subscription.objects.get_or_create(user=request.user, tag=tag_name)
    messages.success(request, f"Te has suscrito al tema: {tag_name}")
    return redirect('blog:post_list')  # o la página donde estés mostrando posts

@login_required
def unsubscribe_tag(request, tag_name):
    Subscription.objects.filter(user=request.user, tag=tag_name).delete()
    messages.success(request, f"Te has dejado de suscribir al tema: {tag_name}")
    return redirect('blog:post_list')

def feed_author(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author, published=True).order_by('-published_date')

    feed = Rss201rev2Feed(
        title=f"Posts de {author.username}",
        link=f"/feed/author/{author.username}/",
        description=f"Últimos posts publicados por {author.username}"
    )

    for post in posts:
        feed.add_item(
            title=post.title,
            link=post.get_absolute_url(),
            description=post.excerpt or post.content,
            pubdate=post.published_date
        )

    return HttpResponse(feed.writeString('utf-8'), content_type='application/rss+xml')


def feed_tag(request, tag):
    posts = Post.objects.filter(tags__name__iexact=tag, published=True).order_by('-published_date')

    feed = Rss201rev2Feed(
        title=f"Posts con etiqueta #{tag}",
        link=f"/feed/tag/{tag}/",
        description=f"Últimos posts publicados con la etiqueta #{tag}"
    )

    for post in posts:
        feed.add_item(
            title=post.title,
            link=post.get_absolute_url(),
            description=post.excerpt or post.content,
            pubdate=post.published_date
        )

    return HttpResponse(feed.writeString('utf-8'), content_type='application/rss+xml')