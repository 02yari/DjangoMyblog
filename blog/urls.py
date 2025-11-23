from django.urls import path, include
from . import views

app_name = 'blog'

urlpatterns = [
    # Página principal
    path('', views.post_list, name='post_list'),
    # Auth
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),          # nuestra vista login
    path('logout/', views.logout_view, name='logout'),
    
    # Perfil
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile, name='profile_user'),
    #Notifiaciones
    path("notifications/open/<int:notification_id>/", views.open_notification, name="open_notification"),
    # Comentarios
    path('comment/<int:comment_id>/approve/', views.approve_comment, name='approve_comment'),
    path('comment/<int:comment_id>/reject/', views.reject_comment, name='reject_comment'),
    path('comment/<int:comment_id>/vote/<str:vote_type>/', views.toggle_vote, name='vote_comment'),
    path("comment/<int:comment_id>/toggle-pin/", views.toggle_pin_comment, name="toggle_pin_comment"),
    # Posts  
    path('post/create/', views.create_post, name='post_create'),
    path('post/<slug:slug>/review/', views.add_review, name='add_review'),
    path('post/<int:post_id>/react/<str:reaction_type>/', views.toggle_reaction, name='toggle_reaction'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    
    # Tags y búsqueda
    path('tag/<slug:slug>/', views.posts_by_tag, name='posts_by_tag'),
    path('search/', views.search_posts, name='search_posts'),
    # CKEditor
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    # redirige a tu propio perfil
    path('subscribe/<str:username>/', views.subscribe, name='subscribe'),
    path('unsubscribe/<str:username>/', views.unsubscribe, name='unsubscribe'),

]