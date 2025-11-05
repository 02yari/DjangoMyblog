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
    # columnas que verás en la lista
    list_display = ('post', 'user', 'name', 'email', 'short_content', 'created_date', 'is_approved', 'active')
    list_filter = ('is_approved', 'active', 'created_date')
    search_fields = ('user__username', 'name', 'email', 'content')
    actions = ['approve_comments', 'reject_comments']
    list_editable = ('is_approved', 'active')

    # acción para aprobar
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True, active=True)
        self.message_user(request, f"{updated} comentario(s) aprobados correctamente.")
    approve_comments.short_description = 'Aprobar comentarios seleccionados'

    # acción para rechazar
    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False, active=False)
        self.message_user(request, f"{updated} comentario(s) rechazados.")
    reject_comments.short_description = 'Rechazar comentarios seleccionados'

    # para no mostrar el comentario entero en la tabla (demasiado largo),
    # definimos un método que recorta el content a p.ej. 50 caracteres
    def short_content(self, obj):
        return (obj.content[:47] + '...') if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Comentario'