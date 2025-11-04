from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
   
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),          # nuestra vista login
    path('logout/', views.logout_view, name='logout'), 

    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    
]