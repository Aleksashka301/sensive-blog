from django.contrib import admin
from blog.models import Post, Tag, Comment


class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'post')
    raw_id_fields = ('author',)


class PostAdmin(admin.ModelAdmin):
    raw_id_fields = ('likes',)


admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(Comment, CommentAdmin)
