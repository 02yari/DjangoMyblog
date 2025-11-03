from django.contrib import admin
from .models import Post, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'author', 'created_date', 'published')
    list_filter = ('created_date', 'published_date', 'author', 'published')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_date'
    ordering = ('created_date',)
    list_editable = ('published',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'content')
        }),
        ('Opciones de publicación', {
            'fields': ('published', 'published_date'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'post', 'created_date', 'active')
    list_filter = ('active', 'created_date')
    search_fields = ('name', 'email', 'content')
    actions = ['approve_comments']
    list_editable = ('active',)

    def approve_comments(self, request, queryset):
        queryset.update(active=True)
        self.message_user(request, f'{queryset.count()} comentarios aprobados.')
    approve_comments.short_description = 'Aprobar comentarios seleccionados'