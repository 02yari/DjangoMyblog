from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .views import toggle_reaction


app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
   
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),          # nuestra vista login
    path('logout/', views.logout_view, name='logout'), 

    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/approve/', views.approve_comment, name='approve_comment'),
    path('comment/<int:comment_id>/reject/', views.reject_comment, name='reject_comment'),

    path('post/<slug:slug>/review/', views.add_review, name='add_review'),
    path('tag/<slug:slug>/', views.posts_by_tag, name='posts_by_tag'),
    path('search/', views.search_posts, name='search_posts'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path("post/<int:post_id>/react/", toggle_reaction, name="toggle_reaction"),
]